# /backend/create_user_table.py
from sqlalchemy import text
from database import engine

# This SQL command creates the users table if it does not already exist.
create_users_table_sql = text("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        health_conditions JSONB,
        created_at TIMESTAMPTZ DEFAULT NOW()
    );
""")

def main():
    """ Connects to the database and creates the 'users' table. """
    print("Attempting to create the 'users' table...")
    try:
        with engine.connect() as connection:
            with connection.begin() as transaction:
                connection.execute(create_users_table_sql)
        print("✅ SUCCESS: The 'users' table now exists in your database.")
    except Exception as e:
        print("❌ FAILED: An error occurred.")
        print(e)

if __name__ == "__main__":
    main()