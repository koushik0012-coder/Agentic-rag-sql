import database
import rag
import json

print("--- Data Directory Check ---")
import os
print(os.listdir(database.DATA_DIR))

print("\n--- Database Tables ---")
print(database.get_engine().table_names())

print("\n--- Schema Info ---")
schema = database.get_schema_info()
print(json.dumps(schema, indent=2))

print("\n--- RAG Retrieval Check ---")
print(rag.get_table_schema_string(schema.keys()))
