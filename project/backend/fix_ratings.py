import pandas as pd
from sqlalchemy import create_engine, event
import os
import time

# Define paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), "data")
DB_PATH = os.path.join(BASE_DIR, "sqlite.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Create engine with longer timeout
engine = create_engine(DATABASE_URL, connect_args={'timeout': 60})

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL") # Better concurrency
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()

def ingest_table(filename, table_name):
    file_path = os.path.join(DATA_DIR, filename)
    print(f"Starting ingestion for {table_name}...")
    
    try:
        # Read CSV in smaller chunks
        chunk_iterator = pd.read_csv(file_path, chunksize=50000)
        
        first_chunk = True
        count = 0
        for chunk in chunk_iterator:
            for attempt in range(5):
                try:
                    if first_chunk:
                        chunk.to_sql(table_name, engine, if_exists="replace", index=False)
                        first_chunk = False
                    else:
                        chunk.to_sql(table_name, engine, if_exists="append", index=False)
                    break
                except Exception as e:
                    if "locked" in str(e):
                        print(f"Database locked, retrying chunk {count}... ({attempt+1}/5)")
                        time.sleep(2)
                    else:
                        raise e
            
            count += 1
            if count % 10 == 0:
                print(f"Processed {count} chunks for {table_name}...")
                
        print(f"Successfully ingested {table_name}")
        return True
    except Exception as e:
        print(f"Error ingesting {table_name}: {e}")
        return False

if __name__ == "__main__":
    ingest_table("ratings.csv", "ratings")
    ingest_table("tags.csv", "tags")
