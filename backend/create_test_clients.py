import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

TEST_USER_EMAIL = "test@example.com"  # adjust if your test user uses a different email

clients_to_create = [
    {
        "name": "Acme Corp",
        "industry": "Manufacturing",
        "contract_value": 25000.00,
        "payment_terms": 30,
        "historical_payment_delay": 5,
        "engagement_score": 4.2,
    },
    {
        "name": "Northwind Traders",
        "industry": "Retail",
        "contract_value": 18000.00,
        "payment_terms": 15,
        "historical_payment_delay": 2,
        "engagement_score": 4.8,
    },
    {
        "name": "Globex Inc",
        "industry": "SaaS",
        "contract_value": 42000.00,
        "payment_terms": 45,
        "historical_payment_delay": 10,
        "engagement_score": 3.9,
    },
]


def seed_clients_for_test_user():
    if not DATABASE_URL:
        print("ERROR: DATABASE_URL not found in your environment variables.")
        return

    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    cur = conn.cursor()

    try:
        cur.execute("SELECT id, email FROM users WHERE email = %s;", (TEST_USER_EMAIL,))
        user = cur.fetchone()

        if not user:
            print(f"ERROR: No user found with email '{TEST_USER_EMAIL}'.")
            print("Update TEST_USER_EMAIL in this script to match your actual test user.")
            return

        user_id = user["id"]
        print(f"Found user: {user['email']} (id={user_id})")

        created = []
        for client in clients_to_create:
            cur.execute(
                """
                INSERT INTO clients (
                    user_id, name, industry, contract_value,
                    payment_terms, historical_payment_delay, engagement_score
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id, name;
                """,
                (
                    user_id,
                    client["name"],
                    client["industry"],
                    client["contract_value"],
                    client["payment_terms"],
                    client["historical_payment_delay"],
                    client["engagement_score"],
                ),
            )
            created.append(cur.fetchone())

        conn.commit()

        print("\nCreated clients for this user:")
        for c in created:
            print(f"  id={c['id']}  name={c['name']}")

        print("\nUpdate ProjectModal.vue's hardcoded clientOptions with these id/name pairs.")

    except Exception as e:
        conn.rollback()
        print(f"ERROR: {e}")
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    seed_clients_for_test_user()