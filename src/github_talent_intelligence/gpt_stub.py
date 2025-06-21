from .db import ChatGPTInteraction, get_session


def get_chatgpt_suggestion(prompt, feedback_id=None):
    """
    Stub for ChatGPT integration. Saves prompt and canned response to DB.
    """
    db = get_session()
    canned_response = "[STUB] This is a placeholder ChatGPT suggestion."
    interaction = ChatGPTInteraction(
        prompt=prompt, response=canned_response, feedback_id=feedback_id
    )
    db.add(interaction)
    db.commit()
    db.close()
    return canned_response
