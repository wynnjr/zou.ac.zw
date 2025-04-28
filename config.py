# config.py
# WhatsApp API Configuration
BASE_URL = "http://localhost:21465/api/wtc"
UNREAD_MESSAGES_ENDPOINT = f"{BASE_URL}/all-unread-messages"
SEND_MESSAGE_ENDPOINT = "http://localhost:21465/api/wtc/send-message"  # Updated endpoint
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
MAX_HISTORY_MESSAGES = 10  # Maximum number of historical messages to include in context
DATA_RETENTION_DAYS = 7  # Number of days to keep chat messages before auto-cleanup
CLEANUP_INTERVAL_HOURS = 24  # Run cleanup process every 24 hours