import requests
import os
from sqlalchemy import text
from database import SessionLocal
from dotenv import load_dotenv
from datetime import datetime, timezone

# Load environment variables from your .env file
load_dotenv()

# --- CONFIGURATION ---
WAQI_API_KEY = os.getenv("WAQI_API_KEY")

# UPDATED: The API URL now points to the specific feed for the New Delhi station (@2554)
API_URL = f"https://api.waqi.info/feed/@2554/?token={WAQI_API_KEY}"

# The list of pollutant columns that exist in our database table
ACCEPTED_PARAMS = ['pm25', 'no2', 'o3', 'pm10', 'so2', 'co']

def fetch_and_store_india_data():
    """
    Fetches detailed data for the New Delhi station from the WAQI API
    and inserts or updates it in the database.
    """
    if not WAQI_API_KEY:
        raise ValueError("WAQI_API_KEY not found. Please add it to your .env file.")

    print(f"Fetching latest data for New Delhi from: {API_URL}")
    
    try:
        response = requests.get(API_URL, timeout=15)
        response.raise_for_status()
        data = response.json()

        if data.get('status') != 'ok':
            print(f"API returned an error: {data.get('message', 'Unknown error')}")
            return

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return

    db = SessionLocal()
    
    try:
        station_data = data.get('data', {})
        iaqi = station_data.get('iaqi', {}) # Individual Air Quality Index (for each pollutant)
        
        # Extract the necessary information from the new API response structure
        timestamp = station_data.get('time', {}).get('s', datetime.now(timezone.utc).isoformat())
        lat = station_data.get('city', {}).get('geo', [None, None])[0]
        lon = station_data.get('city', {}).get('geo', [None, None])[1]
        overall_aqi = station_data.get('aqi')

        if lat is None or lon is None:
            print("Skipping station due to missing coordinates.")
            return

        # Create a single record dictionary to hold all pollutant data
        record_to_insert = {
            "time": timestamp,
            "lat": lat,
            "lon": lon,
            "source": f"WAQI-@{station_data.get('idx', '2554')}",
            "aqi": overall_aqi
        }

        # Add each individual pollutant measurement to the record
        for pollutant, details in iaqi.items():
            if pollutant in ACCEPTED_PARAMS and 'v' in details:
                try:
                    record_to_insert[pollutant] = float(details['v'])
                except (ValueError, TypeError):
                    continue

        # Dynamically build the SQL query based on the pollutants we found
        columns = record_to_insert.keys() - {'lat', 'lon'}
        db_cols_str = ", ".join(columns)
        values_str = ", ".join([f":{k}" for k in columns])
        update_str = ", ".join([f"{k} = EXCLUDED.{k}" for k in columns if k not in ['source', 'time']])

        insert_query = text(f"""
            INSERT INTO air_quality_data (latitude, longitude, {db_cols_str})
            VALUES (:lat, :lon, {values_str})
            ON CONFLICT (time, latitude, longitude) DO UPDATE SET {update_str};
        """)
        
        db.execute(insert_query, record_to_insert)
        db.commit()
        
        print(f"✅ Successfully inserted/updated data for {station_data.get('city', {}).get('name')}.")

    except Exception as e:
        print(f"An error occurred during database insertion: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fetch_and_store_india_data()

