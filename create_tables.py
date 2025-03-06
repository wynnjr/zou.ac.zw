from models import Base, engine

# Create all tables
Base.metadata.create_all(engine)

print("Database tables created successfully!")