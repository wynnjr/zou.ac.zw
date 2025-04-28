# main.py
import logging
import time
import threading
from whatsapp_api import WhatsAppAPI
from gemini_api import GeminiAPI
from database_service import DatabaseService
from config import DATA_RETENTION_DAYS, CLEANUP_INTERVAL_HOURS

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class ChatBot:
    def __init__(self):
        """Initialize the chatbot with database and AI components."""
        self.db = DatabaseService()
        self.gemini = GeminiAPI()
        self.conversation_end_phrases = ['goodbye', 'bye', 'exit', 'end', 'quit', 'thank you', 'thanks']

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
            
            # Check for conversation end phrases to clean up
            if message.lower() in self.conversation_end_phrases:
                # Clean up the user's conversation data
                self.db.cleanup_completed_conversation(user.id)
                return f"Thank you for chatting with us, Your conversation has been completed and data cleared for privacy. Have a great day!"
            
            # If user exists with name, proceed with normal conversation
            logging.info(f"User ID: {user.id}, Name: {user.name}")

            # Get conversation history (last 10 messages)
            recent_messages = self.db.get_last_messages(user.id, limit=10)
            conversation_history = ""
            if recent_messages:
                conversation_history = "Previous conversation:\n"
                for msg in recent_messages:
                    prefix = "User: " if not msg.is_response else "Bot: "
                    conversation_history += f"{prefix}{msg.message}\n"
            
            logging.info(f"Retrieved conversation history with {len(recent_messages) if recent_messages else 0} messages")

            # Handle escalation requests
            if 'help' in message.lower() or 'support' in message.lower():
                assistants = self.db.get_support_assistants()
                
                # Log the assistants data for debugging
                logging.info(f"Support assistants data: {assistants}")
                
                if assistants:
                    # Format the list of assistants
                    assistant_list = "\n".join([f"{a['name']} - {a['phone_number']}" for a in assistants])
                    
                    # Clean up the chat history when escalating to human support
                    self.db.clear_user_chat_history(user.id)
                    
                    return f"Here are the available support assistants:\n{assistant_list}\n\nYour chat history has been cleared for privacy."
                else:
                    return "No support assistants are currently available."

            # Check FAQ before querying Gemini AI
            faq_entry = self.db.find_faq_match(message)
            if faq_entry:
                faq_answer = faq_entry.answer  # Extract answer
                logging.info(f"FAQ response found: {faq_answer}")
                self.db.save_chat_message(user.id, faq_answer, is_response=True)
                return faq_answer

            # Generate AI response with conversation context
            try:
                # Combine conversation history with current message for context
                context_prompt = f"{conversation_history}\nUser's current message: {message}\nPlease respond to the user's current message:"
                response = self.gemini.fetch_response(context_prompt)
                if not response:
                    raise ValueError("GeminiAPI returned an empty response.")
            except Exception as e:
                logging.error(f"Error fetching AI response: {e}")
                response = "I'm having trouble understanding. Let me escalate this for you."
                escalation_id = self.db.create_escalation(user.id, message)
                
                # Clean up chat history after escalation
                self.db.clear_user_chat_history(user.id)
                
                return f"{response}\n\nYour conversation history has been cleared for privacy."

            # Save messages to database
            self.db.save_chat_message(user.id, message, is_response=False)
            self.db.save_chat_message(user.id, response, is_response=True)

            # Personalize response if we have the user's name
            if user.name:
                response = f"{response}"

            return response

        except Exception as e:
            logging.error(f"Error processing message: {e}")
            return "An error occurred while processing your request. Please try again later."


class ChatBotService:
    def __init__(self):
        """Initialize the chatbot service to process WhatsApp messages."""
        self.chatbot = ChatBot()
        self.whatsapp_api = WhatsAppAPI()

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

                                # Send response using WhatsAppAPI
                                self.whatsapp_api.send_message(sender_id, False, response, message_id)
                                logging.info(f"Message sent to {sender_id}")
                            except Exception as e:
                                logging.error(f"Error processing message from {sender_id}: {e}")
                else:
                    logging.warning("No new messages or API error")

                time.sleep(2)  # Wait before checking again

        except KeyboardInterrupt:
            logging.info("ChatBot service stopped gracefully.")
        except Exception as e:
            logging.error(f"Unexpected error in process_messages: {e}")

def scheduled_cleanup(database_service, interval_hours=CLEANUP_INTERVAL_HOURS, days_retention=DATA_RETENTION_DAYS):
    """Run a scheduled cleanup task every interval_hours."""
    while True:
        # Sleep for the specified interval
        time.sleep(interval_hours * 3600)  # Convert hours to seconds
        
        logging.info(f"Starting scheduled database cleanup (retention: {days_retention} days)")
        
        # Run the cleanup
        try:
            # Clean up old conversations
            msg_count, esc_count = database_service.cleanup_old_conversations(days_old=days_retention)
            logging.info(f"Scheduled cleanup completed: removed {msg_count} messages and {esc_count} escalations")
            
            # Clean up resolved escalations
            resolved_count = database_service.cleanup_resolved_escalations()
            logging.info(f"Cleaned up {resolved_count} resolved escalations")
            
        except Exception as e:
            logging.error(f"Error in scheduled cleanup: {e}")

# Main entry point
# main.py (continued)
# Main entry point
if __name__ == "__main__":
    try:
        chatbot_service = ChatBotService()
        
        # Start the cleanup thread
        cleanup_thread = threading.Thread(
            target=scheduled_cleanup, 
            args=(chatbot_service.chatbot.db, CLEANUP_INTERVAL_HOURS, DATA_RETENTION_DAYS),
            daemon=True
        )
        cleanup_thread.start()
        logging.info(f"Scheduled cleanup thread started (interval: {CLEANUP_INTERVAL_HOURS} hours, retention: {DATA_RETENTION_DAYS} days)")
        
        # Start the main service
        logging.info("Starting WhatsApp ChatBot service")
        chatbot_service.process_messages()
    except Exception as e:
        logging.error(f"Error starting ChatBot service: {e}")