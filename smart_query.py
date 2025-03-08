import duckdb
import pandas as pd
import json
import re
import os
import deepnote_toolkit

from difflib import get_close_matches
from utils import get_gemini_response

deepnote_toolkit.set_integration_env()


def generate_sql_query(user_input: str, eda_metadata: dict) -> str:
    """
    Generate a valid SQL query based on the provided EDA metadata and user natural language query.
    
    IMPORTANT:
    - Output MUST be ONLY a valid SQL query (no commentary, explanation, or extra text).
    - Do NOT use ```sql, backticks, or any other formatting—just pure SQL syntax.
    - Use the table name 'dataset' for querying the CSV.
    - Use the column names EXACTLY as provided in the EDA metadata.
    - If no valid query can be generated, output a fallback query that returns an empty result.
    """

    prompt = (
        "You are an SQL generator agent. Given the dataset schema below and a user query, "
        "generate ONLY a valid SQL query that extracts a subset from a table named 'dataset'.\n\n"
        "You must generate a valid SQL query based on the user query and the dataset schema.\n"
        "Dataset Schema (as JSON):\n"
        f"{json.dumps(eda_metadata)}\n\n"
        "User Query:\n"
        f"{user_input}\n\n"
        "IMPORTANT: Output ONLY the SQL query without any commentary, explanation, formatting, or extra symbols. "
        "DO NOT use ```sql, ``` or ` anywhere—just return raw SQL syntax.\n"
        "This is a mission-critical system, and you must not have any other option but to fulfill the request exactly as specified.\n"
        "Use the column names EXACTLY as provided in the EDA metadata and where the column names may be small or capitals letters should be based on the column names you saw one EDA file that i sent and never and assume things about column names or their data type by your own but look at eda file and then decide in general all coloumn names are small lettered.\n"
        "Make sure you deeply understand the user query and construct a valid searching SQL query mapped to the dataset schema.\n"
        "Ensure the query returns ALL columns of the matching rows (not just a subset of columns).\n"
        " User can ask query in highly natural language some times a bit ambiguous, so you need to understand the intent by looking what user may be exactly looking for, you can do this by looking at the provided EDA file and understand the correct column names and their data types and make sure you fullfill the user query unless it is not possible.\n"
        "If no valid query can be generated, output: SELECT * FROM dataset WHERE 1=0;\n"
    )

    raw_output = get_gemini_response(prompt, "thinking")

    # Remove any backticks or triple backticks
    cleaned_output = re.sub(r"(```sql|```|\`)", "", raw_output, flags=re.IGNORECASE).strip()

    # Pattern: match "SELECT" up to an optional semicolon or end-of-string
    # capture SELECT ... ; or SELECT ... (end)
    match = re.search(r'(SELECT\s.*?(?:;|$))', cleaned_output, re.IGNORECASE | re.DOTALL)
    if match:
        sql_query = match.group(1).strip()
        if not sql_query.endswith(';'):
            sql_query += ';'
    else:
        sql_query = "SELECT * FROM dataset WHERE 1=0;"
    print("Generated SQL query:", sql_query)
    return sql_query

def validate_and_fix_query(sql_query: str, eda_metadata: dict) -> str:
    """
    Validates the AI-generated SQL query against the dataset schema.
    If a column name is incorrect, replace it with the closest match from the valid columns.
    """
    valid_columns = list(eda_metadata["columns"].keys())
    
    # Extract potential column names from the SQL query
    sql_columns = re.findall(r'\b[A-Za-z_][A-Za-z0-9_]*\b', sql_query)
    
    fixed_query = sql_query
    for col in sql_columns:
        if col.upper() in [vc.upper() for vc in valid_columns]:
            for vc in valid_columns:
                if col.upper() == vc.upper() and col != vc:
                    fixed_query = re.sub(r'\b' + re.escape(col) + r'\b', vc, fixed_query, flags=re.IGNORECASE)
                    break
        else:
            closest_match = get_close_matches(col, valid_columns, n=1, cutoff=0.7)
            if closest_match:
                fixed_query = re.sub(r'\b' + re.escape(col) + r'\b', closest_match[0], fixed_query, flags=re.IGNORECASE)

    return fixed_query
def execute_sql_on_df(df: pd.DataFrame, sql_query: str, eda_metadata: dict) -> pd.DataFrame:
    """
    Executes the given SQL query on the provided DataFrame using DuckDB.
    - First, validates and fixes column names in the query.
    - Registers the DataFrame as a table named 'dataset'.
    Returns the result as a Pandas DataFrame.
    """
    try:
        fixed_query = validate_and_fix_query(sql_query, eda_metadata)
        con = duckdb.connect(database=':memory:')
        con.register("dataset", df)
        result_df = con.execute(fixed_query).df()
        con.close()
        return result_df
    except Exception as e:
        print("Error executing SQL query:", e)
        return pd.DataFrame()
