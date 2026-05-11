from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
import re
import database


llm = ChatOllama(
    model="phi3:mini", 
    temperature=0, 
    num_ctx=512,  # Maximum squeeze to fit in 2.3GB available RAM
    base_url="http://127.0.0.1:11434",
    timeout=600 
)


def extract_limit(question: str):
    """
    Extracts a number to use as LIMIT from the question.
    """
    match = re.search(r"\b(\d+)\b", question)
    return int(match.group(1)) if match else 5 

def clean_sql_output(text: str):
    """
    Highly robust cleaner for noisy models. 
    Finds the first SELECT and extracts until the end or semicolon.
    """
    if not text:
        return ""

    # Remove code blocks if present
    text = text.replace("```sql", "").replace("```", "").strip()

    # Look for the first SELECT statement (case-insensitive)
    match = re.search(r"(SELECT\s+.*)", text, re.IGNORECASE | re.DOTALL)
    if not match:
        return "INVALID_SQL_GENERATED"
    
    sql = match.group(1).strip()

    # Remove any trailing non-SQL text (heuristically)
    # If there's a semicolon, take everything before it.
    if ";" in sql:
        sql = sql.split(";")[0].strip()
    
    # Final check
    if not sql.upper().startswith("SELECT"):
        return "INVALID_SQL_GENERATED"
        
    return sql + ";"

def clean_validator_output(text: str):
    """
    Parses the validator output to get status and query.
    """

    garbage_phrases = [
        "(if incorrect, followed by FIXED SQL)",
        "(if correct)",
        "INVALID (if incorrect, followed by FIXED SQL)"
    ]
    for phrase in garbage_phrases:
        text = text.replace(phrase, "")


    text = text.replace("```sql", "").replace("```", "").strip()
    

    is_valid = text.upper().startswith("VALID")
    is_invalid = "INVALID" in text.upper()
    
    if is_valid:
        return "VALID"
        
    if is_invalid:
        parts = text.split("INVALID")
        if len(parts) > 1:
            candidate = parts[1].strip()
            return f"INVALID\n{clean_sql_output(candidate)}"
        return "INVALID" 
        
    return "VALID"



sql_gen_template = """
You are a SQLite generator. Convert QUESTION to SQL using ONLY the provided SCHEMA.
Output NOTHING except the raw SQL query. Do not add explanations.
Start your answer immediately with SELECT.

SCHEMA:
{table_schema}

Example 1:
QUESTION: 5 best action movies
SQL: SELECT m.title FROM movies m JOIN ratings r ON m.movieId = r.movieId WHERE m.genres LIKE '%Action%' GROUP BY m.movieId ORDER BY AVG(r.rating) DESC LIMIT 5;

QUESTION: {question}
SQL:
"""
sql_gen_prompt = ChatPromptTemplate.from_template(sql_gen_template)

def generate_with_limit_fn(inputs):

    chain = sql_gen_prompt | llm | StrOutputParser() | clean_sql_output
    sql = chain.invoke(inputs)
    
    if sql.startswith("INVALID_SQL"):
        return sql
    

    limit = extract_limit(inputs["question"])
    if limit and "limit" not in sql.lower():

        sql = sql.rstrip(";")
        sql = f"{sql} LIMIT {limit};"
    elif ";" not in sql:
        sql = f"{sql};"
        
    return sql


sql_gen_chain = RunnableLambda(generate_with_limit_fn)




sql_validate_template = """
You are a SQL Repair Agent.
Given a Broken SQL Query and an Error, FIX the query using the Schema.

Schema:
{table_schema}

Broken Query: {query}
Error: {error}

REPAIR STRATEGIES:
1. **Missing Table**: If error says "no such table", look for the correct table name in Schema.
2. **Missing Column (CRITICAL)**: If error says "no such column: X":
   - Check if Column X exists in *another* table in the Schema.
   - If yes, you MUST `JOIN` that table.
   - Example: If `ORDER BY relevance` fails on `movies`, `JOIN genome_scores` because `relevance` is there.
3. **Implicit Joins**: If error implies join issues, rewrite using explicit `JOIN table ON ...`.
4. **Ambiguity**: If error says "ambiguous column", prefix the column with the Table Name/Alias (e.g. `movies.title`).
5. **Success**: If Error is "None", output VALID.

Output Format:
VALID
(OR)
INVALID
SELECT ...
"""
sql_validate_prompt = ChatPromptTemplate.from_template(sql_validate_template)
sql_validate_chain = sql_validate_prompt | llm | StrOutputParser() | clean_validator_output




result_template = """
Data:
{result}

Question: {question}

Instructions:
1. The 'Data' above is the SQL query result (in JSON format).
2. Synthesize the answer into a **single natural language paragraph**.
3. Do NOT use bullet points or lists (the user sees the table below).
4. Briefly mention the top results naturally (e.g., "The top movies are X, Y, and Z").
5. Be concise and friendly.

Answer:
"""
result_prompt = ChatPromptTemplate.from_template(result_template)
result_chain = result_prompt | llm | StrOutputParser()
