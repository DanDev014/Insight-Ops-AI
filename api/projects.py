import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load env variables
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

app = FastAPI(title="Insight Ops AI - Projects API")

# Allow your React frontend to access this API securely
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_connection():
    if not DATABASE_URL:
        raise HTTPException(status_code=500, detail="Database URL not configured")
    try:
        return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")

@app.get("/api/projects")
def get_projects():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT 
                p.id, 
                p.name AS project_name, 
                c.name AS client_name,
                p.budget, 
                p.hours_estimated, 
                p.hours_logged, 
                p.deadline, 
                p.status, 
                p.margin
            FROM projects p
            JOIN clients c ON p.client_id = c.id
            ORDER BY p.id DESC;
        """)
        projects = cur.fetchall()
        return projects
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query error: {str(e)}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.projects:app", host="127.0.0.1", port=8000, reload=True)