from sqlalchemy import create_engine

DATABASE_URL = "postgresql://postgres:wynn@localhost/chatbot"

try:
    engine = create_engine(DATABASE_URL)
    connection = engine.connect()
    print("✅ Connection successful!")
    connection.close()
except Exception as e:
    print("❌ Connection failed:", e)
