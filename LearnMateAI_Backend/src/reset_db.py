from .database import models
from .database.database import engine

# Drop all tables
models.Base.metadata.drop_all(bind=engine)

# Recreate tables
models.Base.metadata.create_all(bind=engine)

print("Database tables have been reset.")
