from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Any
import uvicorn
import os


import rag
import graph
import agents

app = FastAPI(title="Agentic SQL-RAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



class QueryRequest(BaseModel):
    question: str

class SchemaRequest(BaseModel):
    question: str
    relevant_tables: List[str]

class SqlRequest(BaseModel):
    question: str
    table_schema: str

class ValidationRequest(BaseModel):
    question: str
    table_schema: str
    sql_query: str

class ExecutionRequest(BaseModel):
    question: str
    sql_query: str



@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Backend is running"}

@app.post("/ingest")
def ingest_data():
    """
    Triggers the CSV ingestion process.
    """
    tables = database.ingest_csv_data()
    rag.index_schema()
    return {"message": "Ingestion complete", "tables": tables}

@app.post("/pipeline/step/schema")
def step_schema(req: QueryRequest):
    """
    Step 1: Extract relevant schema based on question.
    """
    result = graph.extract_schema({"question": req.question})
    return result

@app.post("/pipeline/step/generate_sql")
def step_generate_sql(req: SqlRequest):
    """
    Step 2: Generate SQL from schema and question.
    """
    result = graph.generate_sql({
        "question": req.question, 
        "table_schema": req.table_schema
    })
    return result

@app.post("/pipeline/step/validate_sql")
def step_validate_sql(req: ValidationRequest):
    """
    Step 3: Validate and potentially fix SQL.
    """
    state = {
        "question": req.question,
        "table_schema": req.table_schema,
        "sql_query": req.sql_query,
        "iterations": 0,
        "sql_valid": False # Default
    }
    result = graph.validate_sql(state)
    return result

@app.post("/pipeline/step/execute")
def step_execute(req: ExecutionRequest):
    """
    Step 4: Execute SQL and synthesize answer.
    """
    state = {
        "question": req.question,
        "sql_query": req.sql_query,
        "query_result": None 
    }
    result = graph.execute_and_synthesize(state)
    return result

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
