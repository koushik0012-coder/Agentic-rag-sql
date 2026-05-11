from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
import database


embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

vector_store = None

def index_schema():
    """
    Reads the current database schema, converts it into documents, 
    and indexes them using FAISS.
    """
    global vector_store
    schema_info = database.get_schema_info()
    documents = []
    
    for table_name, columns in schema_info.items():
        if "-" in table_name:
            continue
            
        if isinstance(columns, list):
             raw_cols = columns
        else:
             raw_cols = columns.get("columns", [])
        
        column_descriptions = ", ".join([f"{col['name']} ({col['type']})" for col in raw_cols])
        content = f"Table Name: {table_name}\nColumns: {column_descriptions}"
        
        doc = Document(
            page_content=content,
            metadata={"table_name": table_name}
        )
        documents.append(doc)
    
    if documents:
        vector_store = FAISS.from_documents(documents, embeddings)
        print("Schema indexed successfully.")
    else:
        print("No schema to index.")

def retrieve_relevant_tables(query: str, k: int = 3):
    """
    Bypass vector search and return all core tables. 
    Since our database schema is very small (only ~6 tables), providing the entire 
    schema is more token-efficient and GUARANTEES the LLM never hallucinates or misses 
    vital tables like 'ratings' when asked for top rated movies.
    """
    schema_info = database.get_schema_info()
    relevant_tables = [table for table in schema_info.keys() if "-" not in table]
    
    return relevant_tables

def get_table_schema_string(table_names):
    """
    Compact schema string that includes tables, columns, and relationships (Foreign Keys)
    so the LLM knows exactly how to JOIN them.
    """
    schema_info = database.get_schema_info()
    schema_str = ""
    for table in table_names:
        if table in schema_info:
            info = schema_info[table]
            if isinstance(info, list):
                 cols = [c['name'] for c in info]
                 fks = []
            else:
                 cols = [c['name'] for c in info.get("columns", [])]
                 fks = info.get("foreign_keys", [])
            
            fks_str = " | " + " ".join(fks) if fks else ""
            schema_str += f"{table}({','.join(cols)}){fks_str}\n"
    return schema_str
