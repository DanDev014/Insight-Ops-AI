import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


def verify_connection():

    print("Checking connection to Neon database...")

    if not DATABASE_URL:
        print("ERROR: DATABASE_URL not found.")
        print("Create a .env file and add your connection string.")
        return

    conn = None

    try:
        # Connect
        conn = psycopg2.connect(DATABASE_URL)

        cur = conn.cursor()

        # Test query
        cur.execute("SELECT version();")

        db_version = cur.fetchone()

        print("\nSUCCESS: Connected Successfully!\n")

        print(db_version[0])

        cur.close()

    except Exception as e:

        print(f"\nERROR:\n{e}")

    finally:

        if conn:

            conn.close()

            print("\nConnection closed.")


if __name__ == "__main__":
    verify_connection()