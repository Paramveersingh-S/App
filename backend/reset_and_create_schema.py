# /backend/reset_and_create_schema.py
from sqlalchemy import text
from database import engine

# This single SQL block contains all commands to reset and create the schema
reset_and_create_sql = text("""
    -- Drop the old tables if they exist to ensure a clean start
    DROP TABLE IF EXISTS users;
    DROP TABLE IF EXISTS air_quality_data;

    -- Enable PostGIS for geographic queries
    CREATE EXTENSION IF NOT EXISTS postgis;

    -- Create the air_quality_data table with all columns
    CREATE TABLE air_quality_data (
        time TIMESTAMPTZ NOT NULL,
        latitude DOUBLE PRECISION NOT NULL,
        longitude DOUBLE PRECISION NOT NULL,
        source TEXT,
        aqi INTEGER,
        pm25 DOUBLE PRECISION,
        no2 DOUBLE PRECISION,
        o3 DOUBLE PRECISION,
        pm10 DOUBLE PRECISION,
        so2 DOUBLE PRECISION,
        co DOUBLE PRECISION
    );
    
    -- Add the unique constraint to the air_quality_data table
    ALTER TABLE air_quality_data 
    ADD CONSTRAINT unique_measurement UNIQUE (time, latitude, longitude);

    -- Create the users table with all the final columns
    CREATE TABLE users (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        health_conditions JSONB,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        age_group VARCHAR(50),
        persona VARCHAR(100)
    );
""")

def main():
    """ Connects to the database, drops old tables, and creates the new schema. """
    print("Connecting to the database to reset and create the schema...")
    with engine.connect() as connection:
        with connection.begin() as transaction:
            try:
                connection.execute(reset_and_create_sql)
                print("✅ SUCCESS: Database schema has been reset and created successfully.")
            except Exception as e:
                print(f"❌ FAILED: An error occurred: {e}")
                transaction.rollback()

if __name__ == "__main__":
    main()