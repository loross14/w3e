
import os
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    """Get a PostgreSQL database connection"""
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def execute_query(query, params=None, fetch=False, fetch_one=False):
    """Execute a database query with proper error handling"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(query, params)
        
        if fetch_one:
            result = cursor.fetchone()
        elif fetch:
            result = cursor.fetchall()
        else:
            result = cursor.rowcount
            
        conn.commit()
        return result
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

def convert_sqlite_to_pg_query(sqlite_query):
    """Convert SQLite queries to PostgreSQL format"""
    # Replace ? with %s for parameters
    pg_query = sqlite_query.replace('?', '%s')
    
    # Replace AUTOINCREMENT with SERIAL (handled in table creation)
    pg_query = pg_query.replace('AUTOINCREMENT', '')
    
    # Replace INTEGER PRIMARY KEY with SERIAL PRIMARY KEY (handled in table creation)
    return pg_query
