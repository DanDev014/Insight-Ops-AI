import os
import psycopg2
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

email = "test@example.com"
password = "TestPassword123"  # pick whatever you want to log in with
password_hash = generate_password_hash(password)

cur.execute("""
    INSERT INTO users (email, password_hash)
    VALUES (%s, %s)
    ON CONFLICT (email) DO NOTHING;
""", (email, password_hash))

conn.commit()
cur.close()
conn.close()

print(f"Test user created: {email} / {password}")