import unittest
from whatsapp_api import WhatsAppAPI

class TestWhatsAppAPI(unittest.TestCase):
    def test_get_unread_messages(self):
        response = WhatsAppAPI.get_unread_messages()
        self.assertIsInstance(response, dict)

    def test_send_message(self):
        test_response = WhatsAppAPI.send_message(phone="123456789", is_group=False, message="Test Message")
        self.assertIsNone(test_response)

if __name__ == '__main__':
    unittest.main()
