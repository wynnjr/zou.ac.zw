# delete_users_script.py
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import User

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection - must match your main application
DATABASE_URL = "postgresql://postgres:wynn@localhost/chatbot"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def display_all_users():
    """Display all users in the database"""
    session = SessionLocal()
    try:
        # Get all users
        users = session.query(User).order_by(User.id).all()
        
        # Display support assistants first
        print("\nHere are the available support assistants:")
        assistants = [u for u in users if u.is_assistant]
        if assistants:
            for user in assistants:
                print(f"ID: {user.id}, Name: {user.name or 'Unnamed Assistant'}, Phone: {user.phone_number}")
        else:
            print("No support assistants found.")
        
        # Display all users
        print("\nHere are all users:")
        if users:
            for user in users:
                print(f"ID: {user.id}, Name: {user.name or 'Unnamed User'}, Phone: {user.phone_number}")
        else:
            print("No users found in database.")
            
        return users
    except Exception as e:
        logger.error(f"Error displaying users: {e}")
        return []
    finally:
        session.close()

def delete_all_users():
    """Delete all users from the database"""
    session = SessionLocal()
    try:
        # Get count before deletion for logging
        user_count = session.query(User).count()
        
        if user_count == 0:
            print("No users to delete.")
            return True
            
        # Delete all users (cascading deletes will handle related messages/escalations)
        session.query(User).delete()
        session.commit()
        
        logger.info(f"Successfully deleted {user_count} users and their related data")
        return True
    except Exception as e:
        session.rollback()
        logger.error(f"Error deleting users: {e}")
        return False
    finally:
        session.close()

if __name__ == "__main__":
    print("User Management Console")
    print("======================\n")
    
    # First display all users
    users = display_all_users()
    
    if users:
        print("\nWARNING: This will delete ALL users and their related data!")
        confirmation = input("Are you sure you want to delete ALL users? (yes/no): ").strip().lower()
        
        if confirmation == 'yes':
            print("\nStarting deletion...")
            if delete_all_users():
                print("\nOperation completed successfully. All users deleted.")
                
                # Verify deletion
                print("\nVerifying database state...")
                display_all_users()
            else:
                print("\nFailed to delete users. Check logs for details.")
        else:
            print("\nOperation cancelled. No users were deleted.")
    else:
        print("\nNo users found in database. Nothing to delete.")