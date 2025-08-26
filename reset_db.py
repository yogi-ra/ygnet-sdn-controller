from src.database import Base, engine

print("Dropping all tables...")
Base.metadata.drop_all(engine)
print("Creating all tables...")
Base.metadata.create_all(engine)
print("Database reset complete.")
