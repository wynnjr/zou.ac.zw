#(Run this first to create tables)
from sqlalchemy import create_engine
from models import Base
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = "postgresql://postgres:wynn@localhost/chatbot?options=-c search_path=public"

def setup_database():
    """Create all database tables"""
    try:
        engine = create_engine(DATABASE_URL)
        Base.metadata.create_all(bind=engine)
        logger.info("All database tables created successfully!")
        
        # Test connection
        with engine.connect() as conn:
            logger.info("Database connection successful!")
            
    except Exception as e:
        logger.error(f"Error setting up database: {e}")
        raise

if __name__ == "__main__":
    setup_database()