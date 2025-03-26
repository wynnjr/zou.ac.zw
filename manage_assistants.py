from database_service import DatabaseService

db = DatabaseService()

def list_assistants():
    """List all support assistants"""
    assistants = db.get_support_assistants()
    print("\nCurrent Support Assistants:")
    for a in assistants:
        print(f"ID: {a['id']}, Name: {a['name']}, Phone: {a['phone_number']}")

def add_assistant(phone, name):
    """Add a new support assistant"""
    # First check if user exists
    user = db.get_user(phone)
    if user:
        # Mark existing user as assistant
        db.mark_user_as_assistant(phone)
        db.update_user_name(user.id, name)
    else:
        # Create new assistant user
        db.create_assistant_user(phone, name)
    print(f"Assistant {name} added successfully")

def remove_assistant(phone):
    """Remove assistant status from user"""
    user = db.get_user(phone)
    if user:
        db.mark_user_as_assistant(phone, False)
        print(f"User {phone} is no longer an assistant")
    else:
        print("User not found")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "list":
            list_assistants()
        elif sys.argv[1] == "add" and len(sys.argv) == 4:
            add_assistant(sys.argv[2], sys.argv[3])
        elif sys.argv[1] == "remove" and len(sys.argv) == 3:
            remove_assistant(sys.argv[2])
        else:
            print("Usage:")
            print("  python manage_assistants.py list")
            print("  python manage_assistants.py add <phone> <name>")
            print("  python manage_assistants.py remove <phone>")
    else:
        list_assistants()