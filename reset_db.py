from src.database import Base, engine, SessionLocal
from src import models # Import models to ensure they are registered with Base

print("Dropping all tables...")
Base.metadata.drop_all(engine)
print("Creating all tables...")
Base.metadata.create_all(engine)
print("Database reset complete.")
