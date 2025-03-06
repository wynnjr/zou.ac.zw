from database_service import DatabaseService
from gemini_api import GeminiAPI

def process_user_message(phone_number, message):
    """Process user messages and respond accordingly"""
    db_service = DatabaseService()
    user_id, user_name = db_service.get_or_create_user(phone_number)

    if not user_name:
        return "I don't know your name yet. What should I call you?"

    return GeminiAPI.fetch_response(phone_number, message)

def store_user_name(phone_number, name):
    """Store user-provided name in the database"""
    db_service = DatabaseService()
    if db_service.update_user_name(phone_number, name):
        return f"Got it, {name}! I'll remember your name from now on. How can I assist you?"
    return "I couldn't save your name. Please try again."
