# /backend/create_tables.py
from sqlalchemy import text
from database import engine

# CORRECTED: Removed TimescaleDB-specific commands.
# We will now create a standard PostgreSQL table and add a high-performance index.
create_table_and_index_sql = text("""
    CREATE TABLE IF NOT EXISTS air_quality_data (
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
    
    -- This creates a standard, efficient index on the 'time' column for fast queries.
    CREATE INDEX IF NOT EXISTS idx_air_quality_data_time ON air_quality_data (time DESC);
""")

def main():
    print("Connecting to the database to create/update tables...")
    with engine.connect() as connection:
        with connection.begin() as transaction:
            try:
                # We no longer need to create the extension.
                connection.execute(create_table_and_index_sql)
                print("Table 'air_quality_data' and index created successfully.")
            except Exception as e:
                print(f"An error occurred: {e}")
                transaction.rollback()

if __name__ == "__main__":
    main()