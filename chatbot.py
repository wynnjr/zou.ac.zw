import logging
import time
from whatsapp_api import WhatsAppAPI
from gemini_api import GeminiAPI
from database_service import DatabaseService

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class ChatBot:
    def __init__(self):
        """Initialize the chatbot with database and AI components."""
        self.db = DatabaseService()
        self.gemini = GeminiAPI()

    def respond(self, sender, message):
        """Processes user messages, fetches responses, and saves interactions."""
        logging.info(f"Received message from {sender}: {message}")

        try:
            # Fetch user from database
            user = self.db.get_user(sender)
            
            # If user doesn't exist, create new user with session=True
            if not user:
                user_id = self.db.create_user(sender)
                user = self.db.get_user(sender)
                return "Welcome! Please tell me your name to get started."
            
            # If user exists but has no name (session=True), save the name
            if user.session and not user.name:
                # Assume the first message from a new user is their name
                self.db.update_user_name(user.id, message)
                return f"Thank you, {message}! How can I assist you today?"
            
            # If user exists with name, proceed with normal conversation
            logging.info(f"User ID: {user.id}, Name: {user.name}")

            # Handle escalation requests
            if 'help' in message.lower() or 'support' in message.lower():
                assistants = self.db.get_support_assistants()
                
                # Log the assistants data for debugging
                logging.info(f"Support assistants data: {assistants}")
                
                if assistants:
                    # Format the list of assistants
                    assistant_list = "\n".join([f"{a['name']} - {a['phone_number']}" for a in assistants])
                    return f"Here are the available support assistants:\n{assistant_list}"
                else:
                    return "No support assistants are currently available."

            # Check FAQ before querying Gemini AI
            faq_entry = self.db.find_faq_match(message)
            if faq_entry:
                faq_answer = faq_entry.answer  # Extract answer
                logging.info(f"FAQ response found: {faq_answer}")
                self.db.save_chat_message(user.id, faq_answer, is_response=True)
                return faq_answer

            # Generate AI response
            try:
                response = self.gemini.fetch_response(message)
                if not response:
                    raise ValueError("GeminiAPI returned an empty response.")
            except Exception as e:
                logging.error(f"Error fetching AI response: {e}")
                response = "I'm having trouble understanding. Let me escalate this for you."
                self.db.create_escalation(user.id, message)

            # Save messages to database
            self.db.save_chat_message(user.id, message, is_response=False)
            self.db.save_chat_message(user.id, response, is_response=True)

            # Personalize response if we have the user's name
            if user.name:
                response = f"{user.name}, {response}"

            return response

        except Exception as e:
            logging.error(f"Error processing message: {e}")
            return "An error occurred while processing your request. Please try again later."


class ChatBotService:
    def __init__(self):
        """Initialize the chatbot service to process WhatsApp messages."""
        self.chatbot = ChatBot()
        self.whatsapp_api = WhatsAppAPI()  # Ensure WhatsAppAPI instance is used

    def process_messages(self):
        """Checks unread messages and sends responses."""
        try:
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

                time.sleep(1)  # Wait before checking again

        except KeyboardInterrupt:
            logging.info("ChatBot service stopped gracefully.")
        except Exception as e:
            logging.error(f"Unexpected error in process_messages: {e}")


# Main entry point
if __name__ == "__main__":
    chatbot_service = ChatBotService()
    chatbot_service.process_messages()