import logging
import time
import random
from whatsapp_api import WhatsAppAPI
from gemini_api import GeminiAPI
from database_service import DatabaseService

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class ChatBot:
    def __init__(self):
        """Initialize the chatbot with database and AI components"""
        self.db = DatabaseService()
        self.gemini = GeminiAPI()

    def respond(self, sender, message):
        """Processes user messages, fetches responses, and saves interactions."""
        logging.info(f"Received message from {sender}: {message}")

        # Fetch or create user
        user_id, user_name = self.db.get_or_create_user(sender)
        logging.info(f"User ID: {user_id}, Name: {user_name}")

        # Handle user registration session
        user = self.db.get_user(sender)
        if user.session:
            self.db.update_user_name(user.id, message)  # Save name
            return f"Thanks {message}, your details have been saved!"

        # Handle escalation requests
        if 'help' in message.lower() or 'support' in message.lower():
            assistants = self.db.get_support_assistants()
            
            # Debug log to check what is being returned
            logging.info(f"Support assistants found: {assistants}")
            
            if assistants:
                assistant_list = "\n".join([f"{a.name} - {a.phone_number}" for a in assistants])
                return f"Here are the available support assistants:\n{assistant_list}"
            else:
                return "No support assistants are currently available."

        # Check FAQ before querying Gemini AI
        faq_entry = self.db.find_faq_match(message)
        if faq_entry:
            faq_answer = faq_entry.answer  # Extract answer
            logging.info(f"FAQ response found: {faq_answer}")
            self.db.save_chat_message(user_id, faq_answer, is_response=True)
            return faq_answer

        # Generate AI response
        try:
            response = self.gemini.fetch_response(message)
            if not response:
                raise ValueError("GeminiAPI returned an empty response.")
        except Exception as e:
            logging.error(f"Error fetching AI response: {e}")
            response = "I'm having trouble understanding. Let me escalate this for you."
            self.db.create_escalation(user_id, message)

        # Save messages to database
        self.db.save_chat_message(user_id, message, is_response=False)
        self.db.save_chat_message(user_id, response, is_response=True)

        return response


class ChatBotService:
    def __init__(self):
        """Initialize the chatbot service to process WhatsApp messages"""
        self.chatbot = ChatBot()
        self.whatsapp_api = WhatsAppAPI()  # Ensure WhatsAppAPI instance is used

    def process_messages(self):
        """Checks unread messages and sends responses."""
        while True:
            unread_messages = self.whatsapp_api.get_unread_messages()
            logging.info("Checking for unread messages...")

            if isinstance(unread_messages, dict) and unread_messages.get("status") == "success":
                messages = unread_messages.get("response", [])
                logging.info(f"Total unread messages: {len(messages)}")

                for message_data in messages:
                    sender_id = message_data.get("from", "").strip()
                    message_content = message_data.get("body", "").strip()
                    message_id = message_data.get("messageId", "")

                    if sender_id and message_content:
                        logging.info(f"Processing message from {sender_id}: {message_content} (Message ID: {message_id})")
                        try:
                            response = self.chatbot.respond(sender_id, message_content)
                            logging.info(f"Replying to {sender_id}: {response}")

                            # Send response using WhatsAppAPI instance
                            self.whatsapp_api.send_message(sender_id, is_group=False, message=response, message_id=message_id)
                            logging.info(f"Message sent to {sender_id}")
                        except Exception as e:
                            logging.error(f"Error processing message from {sender_id}: {e}")
                    else:
                        logging.warning(f"Incomplete message data, skipping. Data: {message_data}")
            else:
                logging.warning("No new messages or API error")

            time.sleep(2)  # Wait before checking again
