import requests
import logging
from config import UNREAD_MESSAGES_ENDPOINT, SEND_MESSAGE_ENDPOINT, HEADERS, MAX_MESSAGE_LENGTH

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class WhatsAppAPI:
    """Handles WhatsApp API interactions"""

    @staticmethod
    def get_unread_messages():
        try:
            response = requests.get(UNREAD_MESSAGES_ENDPOINT, headers=HEADERS)
            response.raise_for_status()
            logging.info("Fetched unread messages successfully.")
            return response.json()
        except requests.RequestException as e:
            logging.error(f"Error fetching unread messages: {e}")
            return {}

    @staticmethod
    def send_message(phone, is_group, message, message_id=None):
        try:
            payload = {"phone": phone, "isGroup": is_group, "message": message}
            if message_id:
                payload["messageId"] = message_id

            response = requests.post(SEND_MESSAGE_ENDPOINT, headers=HEADERS, json=payload)
            response.raise_for_status()
            logging.info(f"Message sent to {phone} (Group: {is_group}): {message}")
        except requests.RequestException as e:
            logging.error(f"Error sending message: {e}")