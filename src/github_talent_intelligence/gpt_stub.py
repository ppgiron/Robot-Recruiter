import os
from .db import ChatGPTInteraction, get_session
from .token_manager import get_openai_api_key

try:
    import openai
except ImportError:
    openai = None

def get_chatgpt_suggestion(prompt, feedback_id=None, model="gpt-3.5-turbo", temperature=0.2):
    """
    Calls OpenAI's ChatGPT API to get a classification suggestion.
    Saves prompt and response to DB.
    """
    try:
        api_key = get_openai_api_key()
    except ValueError:
        api_key = None
    
    if not openai or not api_key:
        canned_response = "[STUB] This is a placeholder ChatGPT suggestion. (No OpenAI API key or openai package)"
        db = get_session()
        interaction = ChatGPTInteraction(
            prompt=prompt, response=canned_response, feedback_id=feedback_id
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
        prompt=prompt, response=chatgpt_response, feedback_id=feedback_id
    )
    db.add(interaction)
    db.commit()
    db.close()
    return chatgpt_response
