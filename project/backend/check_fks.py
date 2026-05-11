from sqlalchemy import create_engine, inspect
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "sqlite.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL)
inspector = inspect(engine)

print("--- Checking Foreign Keys ---")
for table_name in inspector.get_table_names():
    fks = inspector.get_foreign_keys(table_name)
    print(f"Table: {table_name}, FKs: {fks}")
