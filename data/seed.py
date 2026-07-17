import os
import psycopg2
from faker import Faker
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv
# THIS SCRIPT HAS ALREADY BEEN RUN TO SEED THE DATABASE. RUNNING IT AGAIN WILL WIPE AND RESEED ALL DATA.KINDLY DO NOT RUN AGAIN UNLESS YOU INTEND TO WIPE AND RESEED THE DATABASE.
# Load environment variables from the local .env file
load_dotenv()

fake = Faker()

# Fetch the database URL securely from the environment variables
DATABASE_URL = os.getenv("DATABASE_URL")

def seed_db():
    if not DATABASE_URL:
        print("ERROR: DATABASE_URL not found in your environment variables.")
        print("Please make sure you have created a '.env' file in this directory.")
        return

    print("Connecting to Neon database branch...")
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
    except Exception as e:
        print(f"FAILED: Failed to connect to Neon: {e}")
        return
    
    try:
        # Wipe existing data first so old group members and tiny records are cleared
        print("Cleaning up old database records (Truncating existing tables)...")
        cur.execute("""
            TRUNCATE TABLE time_logs, payments, projects, team, clients, users CASCADE;
        """)
        conn.commit()

        # Run Schema to ensure everything is fresh
        print("Ensuring fresh tables from schema...")
        with open("schema.sql", "r") as f:
            cur.execute(f.read())
        conn.commit()

        # 1. SEED CLIENTS (150 entries for diverse ML training patterns)
        print("Seeding 150 clients with distinct risk behavior profiles...")
        industries = ["Fintech", "Retail", "Healthcare", "SaaS", "E-commerce", "Logistics", "Energy", "Real Estate", "Entertainment"]
        clients_data = []
        for _ in range(150):
            # Define risk profiles: 25% Chronically Late, 15% Moderately Slow, 60% Highly Reliable
            profile_roll = random.random()
            if profile_roll < 0.25:
                # High-risk profile
                delay = random.randint(20, 65)
                engagement = round(random.uniform(0.15, 0.49), 2)
                contract_val = random.randint(8000, 45000)
            elif profile_roll < 0.40:
                # Medium-risk profile
                delay = random.randint(8, 19)
                engagement = round(random.uniform(0.50, 0.74), 2)
                contract_val = random.randint(20000, 85000)
            else:
                # Low-risk profile
                delay = random.randint(0, 7)
                engagement = round(random.uniform(0.75, 1.00), 2)
                contract_val = random.randint(40000, 160000)
            
            cur.execute("""
                INSERT INTO clients (name, industry, contract_value, payment_terms, historical_payment_delay, engagement_score)
                VALUES (%s, %s, %s, %s, %s, %s) RETURNING id;
            """, (fake.company(), random.choice(industries), contract_val, 30, delay, engagement))
            clients_data.append(cur.fetchone()[0])
            
        # 2. SEED TEAM (30 fully synthetic staff profiles)
        print("Seeding 30 synthetic staff profiles...")
        roles_pool = [
            ("Data Scientist", 95, ["Python", "scikit-learn", "SQL", "Pandas"]),
            ("ML Engineer", 105, ["PyTorch", "Docker", "AWS", "MLflow"]),
            ("Data Engineer", 85, ["Spark", "Airflow", "PostgreSQL", "dbt"]),
            ("BI Analyst", 70, ["Tableau", "Power BI", "SQL", "Excel"]),
            ("Backend Developer", 80, ["FastAPI", "Django", "PostgreSQL", "Redis"]),
            ("Frontend Developer", 75, ["React", "TypeScript", "Tailwind CSS", "Next.js"]),
            ("Project Manager", 65, ["Agile", "Scrum", "Jira", "Resource Planning"])
        ]
        
        team_ids = []
        for _ in range(30):
            role, base_rate, skills = random.choice(roles_pool)
            adjusted_rate = base_rate + random.randint(-12, 18)
            cur.execute("""
                INSERT INTO team (name, role, hourly_rate, capacity, skills)
                VALUES (%s, %s, %s, %s, %s) RETURNING id;
            """, (fake.name(), role, adjusted_rate, 40, skills))
            team_ids.append(cur.fetchone()[0])

        # 3. SEED PROJECTS (200 records spanning active, completed, and paused states)
        print("Seeding 200 project profiles...")
        project_ids = []
        project_statuses = ["active", "completed", "completed", "paused"]  # Weighted toward completed for history
        for i in range(200):
            client_id = random.choice(clients_data)
            budget = random.randint(10000, 120000)
            status = random.choice(project_statuses)
            
            # Simulate historical over-budget exceptions (essential for anomaly detection models)
            is_runaway = (random.random() < 0.18) and (status == "active" or status == "completed")
            est_hours = random.randint(60, 250)
            logged_hours = est_hours * random.uniform(1.10, 1.50) if is_runaway else est_hours * random.uniform(0.25, 0.95)
            
            # Backdate historical completed projects, set active ones to future deadlines
            if status == "completed":
                deadline = datetime.now().date() - timedelta(days=random.randint(10, 180))
            else:
                deadline = datetime.now().date() + timedelta(days=random.randint(5, 90))
                
            cur.execute("""
                INSERT INTO projects (client_id, name, budget, hours_estimated, hours_logged, deadline, status, margin)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;
            """, (client_id, f"Project {fake.catch_phrase()}", budget, est_hours, logged_hours, 
                  deadline, status, round(random.uniform(5.0, 50.0), 2)))
            project_ids.append(cur.fetchone()[0])

        # 4. SEED PAYMENTS / INVOICES (600 records)
        print("Seeding 600 invoice transactions with payment behaviors...")
        for _ in range(600):
            client_id = random.choice(clients_data)
            invoice_amt = random.randint(3000, 45000)
            
            # Distribute dates over the last year
            invoice_date = datetime.now().date() - timedelta(days=random.randint(15, 365))
            due_date = invoice_date + timedelta(days=30)
            
            # Determine payment outcomes based on typical invoice timelines
            is_currently_unpaid = random.random() < 0.20
            if is_currently_unpaid:
                # If due date has passed, it's overdue, otherwise it's pending
                paid_date = None
            else:
                # Simulate realistic invoice settlement spreads
                settlement_delay = random.randint(-10, 40)
                paid_date = due_date + timedelta(days=settlement_delay)

            cur.execute("""
                INSERT INTO payments (client_id, invoice_date, due_date, paid_date, amount)
                VALUES (%s, %s, %s, %s, %s);
            """, (client_id, invoice_date, due_date, paid_date, invoice_amt))

        # 5. SEED DAILY TIME LOGS (2,500 daily task allocations)
        print("Seeding 2500 daily task time logs...")
        task_statuses = ["completed", "in_progress", "blocked"]
        for _ in range(2500):
            project_id = random.choice(project_ids)
            member_id = random.choice(team_ids)
            
            # Pick a random workday over the past 6 months
            log_date = datetime.now().date() - timedelta(days=random.randint(1, 180))
            hours = round(random.uniform(1.0, 8.0), 1)
            
            cur.execute("""
                INSERT INTO time_logs (team_member_id, project_id, log_date, hours_logged, task_status)
                VALUES (%s, %s, %s, %s, %s);
            """, (member_id, project_id, log_date, hours, random.choice(task_statuses)))

        conn.commit()
        print("\nSUCCESS: Database branch cleanly wiped and seeded with 3,450+ rich historical rows!")

    except Exception as e:
        print(f"\nERROR: An error occurred during database seeding: {e}")
        if 'conn' in locals() and conn:
            conn.rollback()
    finally:
        if 'cur' in locals() and cur:
            cur.close()
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    seed_db()