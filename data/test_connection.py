import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def verify_connection():
    print("Checking connection to your personal Neon branch...")
    
    if not DATABASE_URL:
        print("ERROR: DATABASE_URL not found in your environment variables.")
        print("Please make sure you have a '.env' file in this directory.")
        return

    conn = None
    try:
        # Attempt to establish connection
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # Run a simple, lightweight test query
        cur.execute("SELECT version();")
        db_version = cur.fetchone()
        
        print("\nSUCCESS: Connection Successful!")
        print(f"Database PostgreSQL Version: {db_version[0]}")
        
        cur.close()
    except Exception as e:
        print(f"\nERROR: Connection failed: {e}")
    finally:
        if conn:
            conn.close()
            print("Connection cleanly closed.")

if __name__ == "__main__":
    verify_connection()