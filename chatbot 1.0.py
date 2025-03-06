# WhatsApp API Configuration
BASE_URL = "http://localhost:21465/api/wtc"
UNREAD_MESSAGES_ENDPOINT = f"{BASE_URL}/all-unread-messages"
SEND_MESSAGE_ENDPOINT = f"{BASE_URL}/send-message"
AUTHORIZATION_KEY = "Bearer $2b$10$nizKsRPrsNg7KCbdeombnuVAlxdeIRk2PMtIVDZjL9iAV3ilkzesu"

HEADERS = {
    "Authorization": AUTHORIZATION_KEY,
    "Content-Type": "application/json",
}

# Gemini AI API Configuration
GEMINI_API_KEY = "AIzaSyAzTxF_M30GVq9kUXdWcBk6sLVy45gAaB0"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
