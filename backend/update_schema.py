from sqlalchemy import text, inspect
from database import engine

def main():
    """
    Connects to the database and applies all necessary schema updates individually for robustness.
    """
    print("Connecting to the database to apply all schema updates...")

    # --- Each command is now separate for better error reporting ---
    commands = {
        "Enable PostGIS": "CREATE EXTENSION IF NOT EXISTS postgis;",
        "Create air_quality_data": """
            CREATE TABLE IF NOT EXISTS air_quality_data (
                time TIMESTAMPTZ NOT NULL, latitude DOUBLE PRECISION NOT NULL, longitude DOUBLE PRECISION NOT NULL,
                source TEXT, aqi INTEGER, pm25 DOUBLE PRECISION, no2 DOUBLE PRECISION, o3 DOUBLE PRECISION
            );
        """,
        "Create users": """
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY, name VARCHAR(255) NOT NULL, health_conditions JSONB,
                created_at TIMESTAMPTZ DEFAULT NOW(), age_group VARCHAR(50), persona VARCHAR(100),
                work_location GEOMETRY(Point, 4326), google_auth_token TEXT, google_refresh_token TEXT
            );
        """,
        "Create weather_forecasts": """
            CREATE TABLE IF NOT EXISTS weather_forecasts (
                time TIMESTAMPTZ NOT NULL, latitude DOUBLE PRECISION NOT NULL, longitude DOUBLE PRECISION NOT NULL,
                temperature_2m DOUBLE PRECISION, relative_humidity_2m DOUBLE PRECISION,
                precipitation DOUBLE PRECISION, wind_speed_10m DOUBLE PRECISION,
                PRIMARY KEY (time, latitude, longitude)
            );
        """,
        "Create citizen_reports": """
            CREATE TABLE IF NOT EXISTS citizen_reports (
                id SERIAL PRIMARY KEY, user_id INTEGER REFERENCES users(id),
                latitude DOUBLE PRECISION NOT NULL, longitude DOUBLE PRECISION NOT NULL,
                description TEXT, image_url VARCHAR(255), status VARCHAR(50) DEFAULT 'pending',
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
        """,
        "Create tempo_grid_data": """
            CREATE TABLE IF NOT EXISTS tempo_grid_data (
                time TIMESTAMPTZ NOT NULL, latitude DOUBLE PRECISION NOT NULL, longitude DOUBLE PRECISION NOT NULL,
                no2_tropospheric DOUBLE PRECISION, quality_flag INTEGER, terrain_height DOUBLE PRECISION,
                surface_pressure DOUBLE PRECISION, wind_speed DOUBLE PRECISION,
                PRIMARY KEY (time, latitude, longitude)
            );
        """,
        "Add columns to air_quality_data": [
            "ALTER TABLE air_quality_data ADD COLUMN IF NOT EXISTS pm10 DOUBLE PRECISION;",
            "ALTER TABLE air_quality_data ADD COLUMN IF NOT EXISTS so2 DOUBLE PRECISION;",
            "ALTER TABLE air_quality_data ADD COLUMN IF NOT EXISTS co DOUBLE PRECISION;",
            "ALTER TABLE air_quality_data ADD COLUMN IF NOT EXISTS terrain_height DOUBLE PRECISION;",
            "ALTER TABLE air_quality_data ADD COLUMN IF NOT EXISTS surface_pressure DOUBLE PRECISION;",
            "ALTER TABLE air_quality_data ADD COLUMN IF NOT EXISTS wind_speed DOUBLE PRECISION;",
            "ALTER TABLE air_quality_data ADD COLUMN IF NOT EXISTS quality_flag INTEGER;"
        ],
        "Add columns to users": [
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS age_group VARCHAR(50);",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS persona VARCHAR(100);",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS work_location GEOMETRY(Point, 4326);",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS google_auth_token TEXT;",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS google_refresh_token TEXT;",
             "ALTER TABLE users ADD COLUMN IF NOT EXISTS outdoor_schedule JSONB;",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS podcast_keywords JSONB;",
        ],
        "Add constraint to air_quality_data": """
            ALTER TABLE air_quality_data 
            ADD CONSTRAINT unique_measurement UNIQUE (time, latitude, longitude);
        """
    }

    with engine.connect() as connection:
        for name, command_or_list in commands.items():
            print(f"- Running: {name}...")
            try:
                with connection.begin() as transaction:
                    if isinstance(command_or_list, list):
                        for command in command_or_list:
                            connection.execute(text(command))
                    else:
                        connection.execute(text(command_or_list))
                print(f"  ...OK")
            except Exception as e:
                # Handle specific, expected errors gracefully
                if 'already exists' in str(e) or 'multiple primary keys' in str(e):
                    print(f"  ...Already exists, skipping.")
                else:
                    print(f"  ...AN ERROR OCCURRED: {e}")
                    # We don't stop, we try the next command
    
    print("\n✅ Schema update process complete.")


if __name__ == "__main__":
    main()

