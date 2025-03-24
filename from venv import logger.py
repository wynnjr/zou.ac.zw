from venv import logger
from sqlalchemy import text

from database_service import SessionLocal

def test_db_connection():
    session = SessionLocal()
    try:
        result = session.execute(text("SELECT 1")).fetchall()
        logger.info(f"Database connection test result: {result}")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
    finally:
        session.close()

test_db_connection()