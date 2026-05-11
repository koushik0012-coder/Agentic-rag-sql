import os
import pandas as pd
from sqlalchemy import create_engine, inspect, text


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), "data")
DB_PATH = os.path.join(BASE_DIR, "sqlite.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"


engine = create_engine(DATABASE_URL)

def get_engine():
    return engine

def ingest_csv_data():
    """
    Scans the 'data' directory for CSV files and loads them into SQLite.
    Returns a list of table names created.
    """
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        return []

    tables_created = []
    
    for filename in os.listdir(DATA_DIR):
        if filename.endswith(".csv"):
            file_path = os.path.join(DATA_DIR, filename)
            table_name = os.path.splitext(filename)[0].lower().replace(" ", "_").replace("-", "_")
            
            try:
                chunk_iterator = pd.read_csv(file_path, chunksize=100000)
                
                first_chunk = True
                for chunk in chunk_iterator:
                    if first_chunk:
                        chunk.to_sql(table_name, engine, if_exists="replace", index=False)
                        first_chunk = False
                    else:
                        chunk.to_sql(table_name, engine, if_exists="append", index=False)
                
                tables_created.append(table_name)
                print(f"Successfully ingested {filename} into table '{table_name}'")
            except Exception as e:
                print(f"Error ingesting {filename}: {e}")

    return tables_created

def get_schema_info():
    """
    Returns a string dict describing the schema of all tables, including Foreign Keys.
    Since SQLite from CSVs often lacks physical FKs, we INFER provided semantic relationships.
    """
    inspector = inspect(engine)
    schema_info = {}
    
    all_table_columns = {}
    for table_name in inspector.get_table_names():
        columns = inspector.get_columns(table_name)
        fks = inspector.get_foreign_keys(table_name)
        
        all_table_columns[table_name] = {
            "columns": [{"name": col["name"], "type": str(col["type"])} for col in columns],
            "foreign_keys": [
                f"FOREIGN KEY ({fk['constrained_columns'][0]}) REFERENCES {fk['referred_table']}({fk['referred_columns'][0]})"
                for fk in fks
            ]
        }
    
    known_entities = {
        "movieId": "movies",
        "userId": "users", 
        "tagId": "tags",
        "imdbId": "links",
        "tmdbId": "links"
    }

    for table, info in all_table_columns.items():
        existing_fks_str = "".join(info["foreign_keys"])
        
        for col in info["columns"]:
            col_name = col["name"]
            
            if col_name in known_entities:
                target_table = known_entities[col_name]
                
                if table != target_table and target_table in all_table_columns:

                    if col_name not in existing_fks_str:
                         info["foreign_keys"].append(f"FOREIGN KEY ({col_name}) REFERENCES {target_table}({col_name})")

    return all_table_columns

def execute_sql_query(query: str):
    """
    Executes a raw SQL query and returns the results.
    """
    try:
        with engine.connect() as connection:
            result = connection.execute(text(query))
            return [dict(row) for row in result.mappings()]
    except Exception as e:
        return {"error": str(e)}
