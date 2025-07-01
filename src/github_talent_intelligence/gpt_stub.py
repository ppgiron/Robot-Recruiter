import os
from .db import ChatGPTInteraction, get_session
from .token_manager import get_openai_api_key

try:
    import openai
except ImportError:
    openai = None

def get_chatgpt_suggestion(prompt, feedback_id=None, model="gpt-3.5-turbo", temperature=0.2, version=1):
    """
    Calls OpenAI's ChatGPT API to get a classification suggestion.
    Saves prompt and response to DB with model, temperature, and version.
    Temperature controls randomness (default 0.2, configurable).
    """
    try:
        api_key = get_openai_api_key()
    except ValueError:
        api_key = None
    temp_int = int(temperature * 10)
    if not openai or not api_key:
        canned_response = "[STUB] This is a placeholder ChatGPT suggestion. (No OpenAI API key or openai package)"
        db = get_session()
        interaction = ChatGPTInteraction(
            prompt=prompt, response=canned_response, feedback_id=feedback_id,
            model=model, temperature=temp_int, version=version
        )
        db.add(interaction)
        db.commit()
        db.close()
        return canned_response

    openai.api_key = api_key
    try:
        response = openai.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=32,
        )
        chatgpt_response = response.choices[0].message.content.strip()
    except Exception as e:
        chatgpt_response = f"[ERROR] ChatGPT API call failed: {e}"

    db = get_session()
    interaction = ChatGPTInteraction(
        prompt=prompt, response=chatgpt_response, feedback_id=feedback_id,
        model=model, temperature=temp_int, version=version
    )
    db.add(interaction)
    db.commit()
    db.close()
    return chatgpt_response


def get_suggestions_for_feedback(feedback_id):
    """Retrieve all ChatGPT suggestions for a given feedback item."""
    db = get_session()
    suggestions = db.query(ChatGPTInteraction).filter_by(feedback_id=feedback_id).order_by(ChatGPTInteraction.created_at).all()
    db.close()
    return suggestions


def update_suggestion_review(suggestion_id, review_status, reviewer_id=None, review_comment=None):
    """Update the review status and comment for a ChatGPT suggestion."""
    db = get_session()
    suggestion = db.query(ChatGPTInteraction).get(suggestion_id)
    if suggestion:
        suggestion.review_status = review_status
        if reviewer_id:
            suggestion.reviewed_by = reviewer_id
        if review_comment:
            suggestion.review_comment = review_comment
        db.commit()
    db.close()
