from database_service import DatabaseService
from tabulate import tabulate  
from models import User, SessionLocal

db = DatabaseService()

def display_users():
    """Display all users in a formatted table"""
    try:
        users = db.get_all_users()
        if not users:
            print("No users found in the database")
            return
            
        print("\nCurrent Users:")
        print(tabulate(
            [(u.id, u.name or "None", u.phone_number, "Yes" if u.is_assistant else "No") for u in users],
            headers=["ID", "Name", "Phone", "Is Assistant"],
            tablefmt="grid"
        ))
    except Exception as e:
        print(f"Error displaying users: {e}")

def set_assistant(user_id, is_assistant):
    """Set assistant status for a user"""
    session = SessionLocal()
    try:
        user = session.query(User).get(user_id)
        if user:
            user.is_assistant = is_assistant
            session.commit()
            print(f"Updated user {user_id} (Name: {user.name or 'None'}) - Assistant: {'Yes' if is_assistant else 'No'}")
        else:
            print(f"User ID {user_id} not found")
    except Exception as e:
        session.rollback()
        print(f"Error updating user: {e}")
    finally:
        session.close()

def update_name(user_id, new_name):
    """Update a user's name"""
    session = SessionLocal()
    try:
        user = session.query(User).get(user_id)
        if user:
            old_name = user.name
            user.name = new_name
            session.commit()
            print(f"Changed user {user_id} name: '{old_name or 'None'}' → '{new_name}'")
        else:
            print(f"User ID {user_id} not found")
    except Exception as e:
        session.rollback()
        print(f"Error updating name: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    import sys
    
    # Display users by default
    if len(sys.argv) == 1:
        display_users()
    
    # Handle commands
    elif len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "set" and len(sys.argv) >= 4:
            # Set assistant status: python user_management.py set <id> <true/false>
            user_id = int(sys.argv[2])
            status = sys.argv[3].lower() in ("true", "yes", "1", "on")
            set_assistant(user_id, status)
            
        elif command == "name" and len(sys.argv) >= 4:
            # Change name: python user_management.py name <id> "New Name"
            user_id = int(sys.argv[2])
            new_name = ' '.join(sys.argv[3:])
            update_name(user_id, new_name)
            
        else:
            print("Available commands:")
            print("  set <user_id> <true/false> - Set assistant status")
            print("  name <user_id> \"New Name\" - Change user's name")
            print("  (no command) - Show all users")