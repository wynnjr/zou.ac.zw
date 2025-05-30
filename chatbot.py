import logging
import time
import threading
import re
from whatsapp_api import WhatsAppAPI
from gemini_api import GeminiAPI
from database_service import DatabaseService
from config import (DATA_RETENTION_DAYS, CLEANUP_INTERVAL_HOURS, MAX_CONSECUTIVE_FAILURES, IT_SUPPORT_EMAIL)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class ChatBot:
    def __init__(self):
        """Initialize the chatbot with database and AI components."""
        self.db = DatabaseService()
        self.gemini = GeminiAPI()
        self.conversation_end_phrases = ['goodbye', 'bye', 'exit', 'end', 'quit', 'thank you', 'thanks']
        self.confusion_phrases = ["I don't understand", "I'm not sure", "I can't help with that", 
                                 "I don't know how to", "I don't have enough information"]
        
        # Escalation trigger phrases
        self.escalation_phrases = ['human', 'agent', 'escalate', 'speak to someone', 'talk to person', 
                                  'customer service', 'supervisor', 'manager', 'help me', 'not working',
                                  'still not working', 'this is not helping', 'this isn\'t working',
                                  'need help', 'talk to a person', 'real person', 'live chat',
                                  'transfer me', 'connect me', 'operator']
        
        self.low_quality_threshold = 0.4
        self.max_consecutive_failures = MAX_CONSECUTIVE_FAILURES

    def _is_low_quality_response(self, response):
        """Check if a response appears to be low quality or indicates confusion."""
        if not response or not response.strip():
            return True
            
        for phrase in self.confusion_phrases:
            if phrase.lower() in response.lower():
                return True
                
        if len(response) < 20 and not any(greeting in response.lower() for greeting in ["hello", "hi", "welcome", "thanks", "thank you"]):
            return True
            
        if re.search(r"(cannot|can't|couldn't|unable to|fail(ed)? to|having trouble|difficulty) (process|understand|respond|help|assist)", 
                    response.lower()):
            return True
            
        return False

    def _should_escalate(self, user, message, ai_response=None):
        """Determine if the conversation should be escalated to human support."""
        try:
            # Check for explicit escalation requests
            message_lower = message.lower()
            for phrase in self.escalation_phrases:
                if phrase.lower() in message_lower:
                    return True, f"User requested escalation with phrase: '{phrase}'"
            
            # Check if AI response is low quality
            if ai_response and self._is_low_quality_response(ai_response):
                # Get current failure count
                failure_count = self._get_user_failure_count_safe(user.id)
                failure_count += 1
                self._set_user_failure_count_safe(user.id, failure_count)
                
                if failure_count >= self.max_consecutive_failures:
                    return True, f"Consecutive low-quality responses: {failure_count}"
            
            # Check for repeated similar messages (user frustration)
            try:
                recent_user_messages = self._get_last_user_messages_safe(user.id, limit=3)
                if len(recent_user_messages) >= 3:
                    if self._messages_similar([msg.message for msg in recent_user_messages]):
                        return True, "User appears to be stuck in a loop"
            except Exception as e:
                logging.warning(f"Could not check message similarity: {e}")
            
            # Check conversation length without resolution
            try:
                total_messages = self.db.get_user_message_count(user.id)
                if total_messages > 20:  # After 20+ messages, offer escalation
                    return True, "Long conversation without resolution"
            except Exception as e:
                logging.warning(f"Could not get message count: {e}")
            
            # Check for frustration indicators
            frustration_indicators = ['frustrated', 'angry', 'upset', 'annoyed', 'terrible', 'awful', 
                                    'useless', 'waste of time', 'not helpful', 'doesn\'t work']
            for indicator in frustration_indicators:
                if indicator in message_lower:
                    return True, f"User showing frustration: '{indicator}'"
            
            return False, None
        except Exception as e:
            logging.error(f"Error in _should_escalate: {e}")
            return False, None

    def _get_user_failure_count_safe(self, user_id):
        """Safely get user failure count with fallback."""
        try:
            if hasattr(self.db, 'get_user_failure_count'):
                return self.db.get_user_failure_count(user_id)
        except Exception as e:
            logging.warning(f"Could not get failure count for user {user_id}: {e}")
        return 0

    def _set_user_failure_count_safe(self, user_id, count):
        """Safely set user failure count with fallback."""
        try:
            if hasattr(self.db, 'set_user_failure_count'):
                self.db.set_user_failure_count(user_id, count)
        except Exception as e:
            logging.warning(f"Could not set failure count for user {user_id}: {e}")

    def _get_last_user_messages_safe(self, user_id, limit=3):
        """Safely get last user messages with fallback."""
        try:
            # Try the expected method first
            if hasattr(self.db, 'get_last_user_messages'):
                return self.db.get_last_user_messages(user_id, limit)
            
            # Fallback: try to get all messages and filter user messages
            if hasattr(self.db, 'get_last_messages'):
                all_messages = self.db.get_last_messages(user_id, limit * 2)  # Get more to filter
                user_messages = [msg for msg in all_messages if not msg.is_response]
                return user_messages[:limit]
            
        except Exception as e:
            logging.warning(f"Could not get last user messages for user {user_id}: {e}")
        
        return []

    def _messages_similar(self, messages):
        """Simple check to see if recent messages are similar (indicating user frustration)."""
        if len(messages) < 2:
            return False
        
        # Check if messages contain similar keywords or are very short repeated messages
        for i in range(len(messages) - 1):
            msg1 = messages[i].lower().strip()
            msg2 = messages[i + 1].lower().strip()
            
            # If messages are identical or very similar short messages
            if msg1 == msg2 or (len(msg1) < 15 and len(msg2) < 15 and 
                               len(set(msg1.split()) & set(msg2.split())) > max(1, len(msg1.split()) * 0.7)):
                return True
        
        return False

    def respond(self, sender, message):
        """Processes user messages, fetches responses, and saves interactions."""
        logging.info(f"Received message from {sender}: {message}")

        try:
            user = self.db.get_user(sender)
            
            if not user:
                user_id = self.db.create_user(sender)
                user = self.db.get_user(sender)
                return "Welcome To The ZOU IT Support Team! Please tell me your name to get started."
            
            if user.session and not user.name:
                self.db.update_user_name(user.id, message)
                return f"Thank you, {message}! How can I assist you today?"
            
            if message.lower() in self.conversation_end_phrases:
                self.db.cleanup_completed_conversation(user.id)
                # Reset failure count on conversation end
                self._set_user_failure_count_safe(user.id, 0)
                return f"Thank you for chatting with us, {user.name}. Your conversation has been completed and data cleared for privacy. Have a great day!"
            
            logging.info(f"User ID: {user.id}, Name: {user.name}")

            # Handle waiting for email state
            user_state = self.db.get_user_state(user.id)
            if user_state and user_state.state == "waiting_for_email":
                if re.match(r"[^@]+@[^@]+\.[^@]+", message):
                    self.db.update_user_email(user.id, message)
                    escalation_id = user_state.data
                    
                    from email_service import send_support_ticket, send_confirmation_email
                    
                    original_message = self.db.get_escalation_message(escalation_id)
                    
                    ticket_subject = f"Support Request from {user.name} (ID: {user.id})"
                    ticket_body = f"""
Support request from WhatsApp Chatbot user:

User: {user.name}
User ID: {user.id}
Phone: {user.phone_number}
Email: {message}
Escalation ID: {escalation_id}

Original Message:
{original_message}

Please review the conversation history and contact the user.
"""
                    send_support_ticket(
                        to_email=IT_SUPPORT_EMAIL,
                        from_email=message,
                        subject=ticket_subject,
                        body=ticket_body
                    )
                    
                    confirmation_subject = "Your Support Request Has Been Received"
                    confirmation_body = f"""
Hello {user.name},

We have received your support request.

Our team has been notified and will review your conversation history.
Someone will contact you shortly to provide assistance.

Reference ID: {escalation_id}

Thank you for your patience.
"""
                    send_confirmation_email(
                        to_email=message,
                        subject=confirmation_subject,
                        body=confirmation_body
                    )
                    
                    self.db.update_escalation_status(escalation_id, "email_provided")
                    self.db.update_user_state(user.id, None)
                    self.db.save_chat_message(user.id, message, is_response=False)
                    
                    response = "Thank you for providing your email address. I've created a ticket and sent it to our IT support team.\n\n"
                    response += f"A confirmation email has been sent to {message}.\n\n"
                    response += "Our IT team will contact you shortly."
                    
                    self.db.save_chat_message(user.id, response, is_response=True)
                    # Reset failure count after successful escalation
                    self._set_user_failure_count_safe(user.id, 0)
                    return response
                else:
                    self.db.save_chat_message(user.id, message, is_response=False)
                    response = "The email address you provided doesn't appear to be valid. Please provide a valid email address in the format user@example.com."
                    self.db.save_chat_message(user.id, response, is_response=True)
                    return response

            # Check for immediate escalation triggers (before AI response)
            should_escalate, escalation_reason = self._should_escalate(user, message)
            if should_escalate and "User requested escalation" in escalation_reason:
                return self._handle_escalation(user, message, escalation_reason)

            # Get conversation history
            recent_messages = self.db.get_last_messages(user.id, limit=10)
            conversation_history = ""
            if recent_messages:
                conversation_history = "Previous conversation:\n"
                for msg in recent_messages:
                    prefix = "User: " if not msg.is_response else "Bot: "
                    conversation_history += f"{prefix}{msg.message}\n"
            
            logging.info(f"Retrieved conversation history with {len(recent_messages) if recent_messages else 0} messages")

            # Save user message
            self.db.save_chat_message(user.id, message, is_response=False)
            
            # Generate AI response
            prompt = f"{conversation_history}\nUser: {message}\n\nPlease provide a helpful response:"
            ai_response = self.gemini.fetch_response(prompt)
            
            if not ai_response or ai_response.strip() == "":
                ai_response = "I'm sorry, I'm having trouble processing your request. Could you please rephrase your question?"
            
            # Check for escalation after AI response
            should_escalate, escalation_reason = self._should_escalate(user, message, ai_response)
            if should_escalate:
                # Don't save the AI response if we're escalating
                return self._handle_escalation(user, message, escalation_reason)
            
            # Reset failure count on successful response
            if not self._is_low_quality_response(ai_response):
                self._set_user_failure_count_safe(user.id, 0)
            
            self.db.save_chat_message(user.id, ai_response, is_response=True)
            return ai_response

        except Exception as e:
            logging.error(f"Error in respond method: {e}")
            # On system errors, escalate if user has been active
            if 'user' in locals() and user and hasattr(user, 'id'):
                return self._handle_escalation(user, message, f"System error: {str(e)}")
            return "Sorry, something went wrong while processing your request. Please try again later."

    def _handle_escalation(self, user, message, reason):
        """Central method to handle all escalations with consistent behavior"""
        logging.info(f"Escalating for user {user.id} ({user.name}). Reason: {reason}")
        
        try:
            # Save the user message if not already saved
            self.db.save_chat_message(user.id, message, is_response=False)
            escalation_id = self._create_escalation_safe(user.id, message)
            
            # Log the escalation
            try:
                self.db.log_event("escalation", f"User: {user.id} | Reason: {reason}")
            except Exception as e:
                logging.warning(f"Could not log escalation event: {e}")
            
            # Reset failure count since we're escalating
            self._set_user_failure_count_safe(user.id, 0)
            
            if user.email:
                try:
                    from email_service import send_support_ticket, send_confirmation_email
                    
                    ticket_subject = f"Support Request from {user.name} (ID: {user.id})"
                    ticket_body = f"""
Support request from WhatsApp Chatbot user:

User: {user.name}
User ID: {user.id}
Phone: {user.phone_number}
Escalation ID: {escalation_id}

Original Message:
{message}

Reason for Escalation:
{reason}

Please review the conversation history and contact the user.
"""
                    send_support_ticket(
                        to_email=IT_SUPPORT_EMAIL,
                        from_email=user.email,
                        subject=ticket_subject,
                        body=ticket_body
                    )
                    
                    confirmation_subject = "Your Support Request Has Been Received"
                    confirmation_body = f"""
Hello {user.name},

We have received your support request.

Our team has been notified and will review your conversation history. 
Someone will contact you shortly to provide assistance.

Reference ID: {escalation_id}

Thank you for your patience.
"""
                    send_confirmation_email(
                        to_email=user.email,
                        subject=confirmation_subject,
                        body=confirmation_body
                    )
                    
                    response = "I understand you need additional assistance. I've created a support ticket and sent it to our IT team.\n\n"
                    response += f"A confirmation email has been sent to {user.email}.\n\n"
                    response += "Our support team will contact you shortly to help resolve your issue."
                except Exception as e:
                    logging.error(f"Error sending escalation emails: {e}")
                    response = "I understand you need additional assistance. I've created a support ticket for our IT team.\n\n"
                    response += "Our support team will contact you shortly to help resolve your issue."
            else:
                response = "I understand you need additional assistance. Let me connect you with our support team.\n\n"
                
                try:
                    assistants = self.db.get_support_assistants()
                    
                    if assistants:
                        assistant_list = "\n".join([f"{a['name']} - {a['phone_number']}" for a in assistants])
                        response += f"Here are the available support assistants:\n{assistant_list}\n\n"
                    else:
                        response += "Our support team will contact you shortly.\n\n"
                except Exception as e:
                    logging.warning(f"Could not get support assistants: {e}")
                    response += "Our support team will contact you shortly.\n\n"
                
                try:
                    self.db.update_user_state(
                        user.id,
                        "waiting_for_email", 
                        str(escalation_id)
                    )
                except Exception as e:
                    logging.warning(f"Could not update user state: {e}")
                
                response += "To help us resolve your issue faster, please provide your email address."
            
            # Save the escalation response
            self.db.save_chat_message(user.id, response, is_response=True)
            return response
            
        except Exception as e:
            logging.error(f"Error in escalation handling: {e}")
            # Fallback response
            response = "I understand you need additional assistance. Our support team has been notified and will contact you shortly."
            try:
                self.db.save_chat_message(user.id, response, is_response=True)
            except Exception as save_error:
                logging.error(f"Could not save fallback escalation response: {save_error}")
            return response

    def _create_escalation_safe(self, user_id, message):
        """Safely create escalation with fallback for missing columns."""
        try:
            # Try the original method first
            return self.db.create_escalation(user_id, message)
        except Exception as e:
            if "resolved_at" in str(e):
                # Try to create escalation without resolved_at column
                logging.warning("Escalations table missing resolved_at column, using fallback method")
                return self._create_escalation_fallback(user_id, message)
            else:
                raise e

    def _create_escalation_fallback(self, user_id, message):
        """Fallback method to create escalation without resolved_at column."""
        try:
            # Get the message ID
            message_id = self.db.save_chat_message(user_id, message, is_response=False)
            
            # Insert escalation without resolved_at
            import datetime
            escalation_data = {
                'user_id': user_id,
                'message_id': message_id,
                'status': 'pending',
                'created_at': datetime.datetime.now()
            }
            
            # Try to insert manually
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO escalations (user_id, message_id, status, created_at) 
                    VALUES (%(user_id)s, %(message_id)s, %(status)s, %(created_at)s) 
                    RETURNING id
                """, escalation_data)
                escalation_id = cursor.fetchone()[0]
                conn.commit()
                return escalation_id
                
        except Exception as e:
            logging.error(f"Fallback escalation creation failed: {e}")
            return None


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

                                self.whatsapp_api.send_message(sender_id, False, response, message_id)
                                logging.info(f"Message sent to {sender_id}")
                            except Exception as e:
                                logging.error(f"Error processing message from {sender_id}: {e}")
                                # Send error escalation if possible
                                try:
                                    user = self.chatbot.db.get_user(sender_id)
                                    if user:
                                        error_response = self.chatbot._handle_escalation(
                                            user, message_content, f"Message processing error: {str(e)}"
                                        )
                                        self.whatsapp_api.send_message(sender_id, False, error_response, message_id)
                                except Exception as escalation_error:
                                    logging.error(f"Failed to escalate error for {sender_id}: {escalation_error}")
                                    # Send a basic error message as last resort
                                    try:
                                        basic_error = "I'm experiencing technical difficulties. Our support team has been notified."
                                        self.whatsapp_api.send_message(sender_id, False, basic_error, message_id)
                                    except Exception as final_error:
                                        logging.error(f"Could not send any response to {sender_id}: {final_error}")
                else:
                    logging.warning("No new messages or API error")

                time.sleep(1)

        except KeyboardInterrupt:
            logging.info("ChatBot service stopped.")
        except Exception as e:
            logging.error(f"Unexpected error in process_messages: {e}")

def scheduled_cleanup(database_service, interval_hours=CLEANUP_INTERVAL_HOURS, days_retention=DATA_RETENTION_DAYS):
    """Run a scheduled cleanup task every interval_hours."""
    while True:
        time.sleep(interval_hours * 3600)
        
        logging.info(f"Starting scheduled database cleanup (retention: {days_retention} days)")
        
        try:
            msg_count, esc_count = database_service.cleanup_old_conversations(days_old=days_retention)
            logging.info(f"Scheduled cleanup completed: removed {msg_count} messages and {esc_count} escalations")
            
            try:
                resolved_count = database_service.cleanup_resolved_escalations()
                logging.info(f"Cleaned up {resolved_count} resolved escalations")
            except Exception as e:
                logging.warning(f"Could not cleanup resolved escalations: {e}")
            
            # Also cleanup failure counts for inactive users
            try:
                database_service.cleanup_inactive_user_states()
                logging.info("Cleaned up inactive user states and failure counts")
            except Exception as e:
                logging.warning(f"Could not cleanup inactive user states: {e}")
            
        except Exception as e:
            logging.error(f"Error in scheduled cleanup: {e}")

# Main entry point
if __name__ == "__main__":
    try:
        chatbot_service = ChatBotService()
        
        cleanup_thread = threading.Thread(
            target=scheduled_cleanup, 
            args=(chatbot_service.chatbot.db, CLEANUP_INTERVAL_HOURS, DATA_RETENTION_DAYS),
            daemon=True
        )
        cleanup_thread.start()
        logging.info(f"Scheduled cleanup thread started (interval: {CLEANUP_INTERVAL_HOURS} hours, retention: {DATA_RETENTION_DAYS} days)")
        
        logging.info("Starting WhatsApp ChatBot service")
        chatbot_service.process_messages()
    except Exception as e:
        logging.error(f"Error starting ChatBot service: {e}")