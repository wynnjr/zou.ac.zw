import logging
from sqlalchemy import create_engine, inspect

# Database connection
DATABASE_URL = "postgresql://postgres:wynn@localhost/chatbot"
engine = create_engine(DATABASE_URL)
inspector = inspect(engine)

# Inspect columns in the 'users' table
columns = inspector.get_columns('users')

for column in columns:
    print(f"Column: {column['name']}, Type: {column['type']}")