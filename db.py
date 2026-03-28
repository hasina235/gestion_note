import psycopg2
import streamlit from st

DB_URL = st.secrets["DB_URL"]

def get_connection():
    return psycopg2.connect(DB_URL)
