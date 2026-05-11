from typing import TypedDict, List, Optional, Any
from langgraph.graph import StateGraph, END
import rag
import database
import agents

class AgentState(TypedDict):
    question: str
    relevant_tables: List[str]
    table_schema: str
    sql_query: str
    sql_valid: bool
    sql_error: Optional[str]
    query_result: Optional[List[dict]]
    final_answer: str
    iterations: int



def extract_schema(state: AgentState):
    print(f"--- Extracting Schema for: {state['question']} ---")
    tables = rag.retrieve_relevant_tables(state['question'])
    schema_str = rag.get_table_schema_string(tables)
    return {
        "relevant_tables": tables,
        "table_schema": schema_str,
        "iterations": 0
    }

def generate_sql(state: AgentState):
    print("--- Generating SQL ---")
    query = agents.sql_gen_chain.invoke({
        "table_schema": state["table_schema"],
        "question": state["question"]
    })
    query = query.replace("```sql", "").replace("```", "").strip()
    return {"sql_query": query}

def validate_sql(state: AgentState):
    print(f"--- Validating SQL: {state['sql_query']} ---")
    
    clean_query = state["sql_query"].replace("```sql", "").replace("```", "").strip()
    
    exec_result = database.execute_sql_query(clean_query)
    
    error_msg = "None"
    if isinstance(exec_result, dict) and "error" in exec_result:
        error_msg = exec_result["error"]
        print(f"Execution Error: {error_msg}")
    
    if error_msg == "None":
        print("SQL executed successfully. Fast-tracking validation.")
        return {
             "sql_valid": True, 
             "sql_error": None, 
             "query_result": exec_result,
             "sql_query": clean_query,
             "iterations": state["iterations"]
        }


    validation_output = agents.sql_validate_chain.invoke({
        "question": state["question"],
        "table_schema": state["table_schema"],
        "query": state["sql_query"],
        "error": error_msg
    })
    

    lines = validation_output.strip().split("\n")
    status = lines[0].strip().upper()
    new_query = "\n".join(lines[1:]).strip() if len(lines) > 1 else state["sql_query"]
    
    new_query = new_query.replace("```sql", "").replace("```", "").strip()

    if status.startswith("VALID") and error_msg == "None":
        if not isinstance(exec_result, dict) or "error" not in exec_result:
             return {
                 "sql_valid": True, 
                 "sql_error": None, 
                 "query_result": exec_result,
                 "sql_query": state["sql_query"]
             }
    
    return {
        "sql_valid": False, 
        "sql_error": f"LLM says {status} / DB Error: {error_msg}", 
        "sql_query": new_query,
        "iterations": state["iterations"] + 1
    }

def execute_and_synthesize(state: AgentState):
    print("--- Executing and Synthesizing ---")

    
    results = state.get("query_result")
    if results is None: 
         results = database.execute_sql_query(state["sql_query"])
    
    if isinstance(results, dict) and "error" in results:
        return {"final_answer": f"I could not generate a valid query. Error: {results['error']}"}

    answer = agents.result_chain.invoke({
        "question": state["question"],
        "query": state["sql_query"],
        "result": str(results)[:2000] 
    })
    
    return {"final_answer": answer, "query_result": results}



workflow = StateGraph(AgentState)

workflow.add_node("extract_schema", extract_schema)
workflow.add_node("generate_sql", generate_sql)
workflow.add_node("validate_sql", validate_sql)
workflow.add_node("execute_and_synthesize", execute_and_synthesize)

workflow.set_entry_point("extract_schema")
workflow.add_edge("extract_schema", "generate_sql")
workflow.add_edge("generate_sql", "validate_sql")

def should_retry(state: AgentState):
    if state["sql_valid"]:
        return "execute_and_synthesize"
    if state["iterations"] > 3:
        return "execute_and_synthesize" 
    return "validate_sql"
    
workflow.add_conditional_edges(
    "validate_sql",
    should_retry,
    {
        "execute_and_synthesize": "execute_and_synthesize",
        "validate_sql": "validate_sql" 
    }
)

workflow.add_edge("execute_and_synthesize", END)

app = workflow.compile()
