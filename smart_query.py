import duckdb
import pandas as pd
import json
import re
import os
from difflib import get_close_matches
import google.generativeai as genai

# Configure Gemini API (ensure your GEMINI_API_KEY is set in the environment)
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-2.0-flash")

def generate_sql_query(user_input: str, eda_metadata: dict) -> str:
    """
    Generate a valid SQL query based on the provided EDA metadata and user natural language query.
    
    IMPORTANT:
    - Output MUST be ONLY a valid SQL query (no commentary, explanation, or extra text).
    - Use the table name 'dataset' for querying the CSV.
    - Use the column names EXACTLY as provided in the EDA metadata.
    - If no valid query can be generated, output a fallback query that returns an empty result.
    """
    prompt = (
        "You are an SQL generator. Given the dataset schema below and a user query, "
        "generate ONLY a valid SQL query that extracts a subset from a table named 'dataset'.\n\n"
        "Dataset Schema (as JSON):\n"
        f"{json.dumps(eda_metadata)}\n\n"
        "User Query:\n"
        f"{user_input}\n\n"
        "IMPORTANT: Output ONLY the SQL query without any commentary or explanation. "
        "If no valid query can be generated, output: SELECT * FROM dataset WHERE 1=0;\n"
    )
    
    response = model.generate_content(prompt)
    raw_output = response.text.strip()
    
    # Extract SQL: find the first occurrence of a string starting with SELECT and ending with a semicolon.
    match = re.search(r'(SELECT\s.*?;)', raw_output, re.IGNORECASE | re.DOTALL)
    if match:
        sql_query = match.group(1).strip()
    else:
        sql_query = "SELECT * FROM dataset WHERE 1=0;"
    return sql_query

def validate_and_fix_query(sql_query: str, eda_metadata: dict) -> str:
    """
    Validates the AI-generated SQL query against the dataset schema.
    If a column name is incorrect, replace it with the closest match from the valid columns.
    """
    valid_columns = list(eda_metadata["columns"].keys())
    
    # Extract potential column names from the SQL query (simple regex for words)
    sql_columns = re.findall(r'\b[A-Za-z_][A-Za-z0-9_]*\b', sql_query)
    
    fixed_query = sql_query
    for col in sql_columns:
        # Check for case-insensitive match; if not, try to auto-correct
        if col.upper() in [vc.upper() for vc in valid_columns]:
            # Replace with the correctly-cased column name if needed
            for vc in valid_columns:
                if col.upper() == vc.upper() and col != vc:
                    fixed_query = re.sub(r'\b' + re.escape(col) + r'\b', vc, fixed_query)
                    break
        else:
            closest_match = get_close_matches(col, valid_columns, n=1, cutoff=0.7)
            if closest_match:
                fixed_query = re.sub(r'\b' + re.escape(col) + r'\b', closest_match[0], fixed_query)
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

if __name__ == "__main__":
    # Example usage:
    # Assume we have an EDA metadata dictionary and a DataFrame loaded from CSV.
    eda_metadata = {
        "columns": {
            "Product": {"dtype": "object"},
            "Sales": {"dtype": "number"},
            "Year": {"dtype": "number"},
            "Region": {"dtype": "object"}
        }
    }
    
    # For demonstration, load CSV data into a DataFrame
    csv_file_path = "data.csv"  # Replace with your actual CSV file path.
    df = pd.read_csv(csv_file_path)
    
    user_query = "Show me the top 10 products by total revenue in 2023."
    sql_query = generate_sql_query(user_query, eda_metadata)
    print("Generated SQL Query:\n", sql_query)
    
    result = execute_sql_on_df(df, sql_query, eda_metadata)
    print("Query Result:\n", result)
