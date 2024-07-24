import os
from urllib.parse import quote_plus
import streamlit as st
import pandas as pd
from langchain.chains import create_sql_query_chain
from langchain_google_genai import GoogleGenerativeAI
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError, OperationalError
from dotenv import load_dotenv
from langchain_community.utilities import SQLDatabase
load_dotenv()
db_user = "root"
db_password = quote_plus("jarvis@123")
db_host = "localhost"
db_name = "retail_sales_db"
engine = create_engine(f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}")
try:
    with engine.connect() as connection:
        st.success("Connected successfully to the database!")
except OperationalError as e:
    st.error(f"Failed to connect to the database: {e}")
    st.stop()
db = SQLDatabase(engine, sample_rows_in_table_info=3)

# Initialize LLM
llm = GoogleGenerativeAI(model="gemini-pro", google_api_key=os.environ["GOOGLE_API_KEY"])

# Create SQL query chain
chain = create_sql_query_chain(llm, db)

def clean_sql_query(query):
    query = query.strip('`').lstrip('sql').strip()
    query = query.replace('`', '')
    query = query.replace('Number of Customers', 'Number_of_Customers')
    
    return query

def execute_query(question):
    try:
        generated_query = chain.invoke({"question": question})
        
        st.write("Raw Generated SQL Query:")
        st.code(generated_query, language="sql")
        cleaned_query = clean_sql_query(generated_query)
        
        st.write("Cleaned SQL Query:")
        st.code(cleaned_query, language="sql")
        
        # Execute the query
        with engine.connect() as connection:
            result = connection.execute(text(cleaned_query))
            columns = result.keys()
            data = result.fetchall()
            return cleaned_query, columns, data
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return generated_query, None, None

def display_result(columns, data):
    if columns and data:
        df = pd.DataFrame(data, columns=columns)
        st.write("Query Result:")
        st.dataframe(df)
        
        # Additional visualizations based on the data
        if len(df.columns) == 2:
            if df.dtypes[1] in ['int64', 'float64']:
                st.bar_chart(df.set_index(df.columns[0]))
st.title("Retail Sales Question Answering App")
question = st.text_input("Enter your question about the retail sales database:")
if st.button("Execute"):
    if question:
        generated_query, columns, query_result = execute_query(question)
        
        if query_result is not None:
            display_result(columns, query_result)
        else:
            st.write("No result returned due to an error.")
    else:
        st.write("Please enter a question.")
st.sidebar.title("Example Questions")
st.sidebar.write("1. How many unique customers are in the sales table?")
st.sidebar.write("2. What is the total revenue for each product category?")
st.sidebar.write("3. Who are the top 5 customers by total purchase amount?")
st.sidebar.write("4. What is the average order value?")
st.sidebar.write("5. Which day of the week has the highest sales?")
