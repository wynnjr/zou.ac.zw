# WhatsApp API Configuration
BASE_URL = "http://localhost:21465/api/wtc"
UNREAD_MESSAGES_ENDPOINT = f"{BASE_URL}/all-unread-messages"
SEND_MESSAGE_ENDPOINT = "http://localhost:21465/api/wtc/send-message"
AUTHORIZATION_KEY = "Bearer $2b$10$1La1M.FeV0UEkNGi.tkKsuj1GV7XbxUPoS_8j5Nj0QGyU0I5LqyeK"

HEADERS = {
    "Authorization": AUTHORIZATION_KEY,
    "Content-Type": "application/json",
}

# Gemini AI API Configuration
GEMINI_API_KEY = "AIzaSyAzTxF_M30GVq9kUXdWcBk6sLVy45gAaB0"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

# Database settings
DATABASE_URL = "postgresql://postgres:wynn@localhost/chatbot?options=-c search_path=public"

# Chatbot settings
MAX_HISTORY_MESSAGES = 10
DATA_RETENTION_DAYS = 7
CLEANUP_INTERVAL_HOURS = 24
MAX_CONSECUTIVE_FAILURES = 3

# Email Configuration for Chatbot
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True

# Sender Configuration (Chatbot's email account)
EMAIL_USER = "wchimpaka@gmail.com"  # Your Gmail account
EMAIL_PASSWORD = "kmex dccx wlcj crlc"   # Use App Password, not regular password!

# Recipients Configuration
IT_SUPPORT_EMAIL = "chimpakaw@zou.ac.zw"  # Primary IT support

# Email Settings
EMAIL_FROM_NAME = "ZOU IT Support Chatbot"
EMAIL_TIMEOUT = 30  # seconds

# Message Chunking
MAX_MESSAGE_LENGTH = 500