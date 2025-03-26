from database_service import DatabaseService
db = DatabaseService()

# Get raw database records
print("RAW USERS TABLE:")
for user in db.get_all_users():
    print(f"ID: {user.id}, Phone: {user.phone_number}, Name: {user.name or 'NULL'}, Session: {user.session}")

print("\nRAW ESCALATIONS TABLE:")
for esc in db.get_pending_escalations():
    print(f"EscID: {esc.id}, UserID: {esc.user_id}, MsgID: {esc.message_id}")