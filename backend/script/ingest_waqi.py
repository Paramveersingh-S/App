import requests
import os
from sqlalchemy import text
from database import SessionLocal
from dotenv import load_dotenv
from datetime import datetime, timezone # <-- 1. New import for generating timestamps

load_dotenv()

API_KEY = os.getenv("WAQI_API_KEY")
API_URL = f"https://api.waqi.info/map/bounds/?latlng=8.0,68.0,37.0,97.0&token={API_KEY}"

def fetch_and_store_waqi_data():
    if not API_KEY:
        raise ValueError("WAQI_API_KEY not found. Please add it to your .env file.")

    print(f"Fetching data from WAQI API for India...")

    try:
        response = requests.get(API_URL)
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
        stations = data.get('data', [])
        print(f"Found {len(stations)} stations. Processing...")

        records_to_insert = []
        for station in stations:
            # First, try to get the real timestamp from the station data
            timestamp = station.get('time', {}).get('s')
            
            # --- 2. THE FIX ---
            # If the station has no timestamp, use the current time as a fallback.
            if not timestamp:
                timestamp = datetime.now(timezone.utc).isoformat()

            try:
                aqi_value = int(station.get('aqi'))
            except (ValueError, TypeError):
                continue # Still skip stations with invalid AQI values

            records_to_insert.append({
                "time": timestamp,
                "lat": station.get('lat'),
                "lon": station.get('lon'),
                "source": "WAQI",
                "aqi": aqi_value
            })
        
        if not records_to_insert:
            print("No valid station data found to insert.")
            return
            
        print(f"Preparing to insert/update {len(records_to_insert)} valid records...")

        insert_query = text("""
            INSERT INTO air_quality_data (time, latitude, longitude, source, aqi)
            VALUES (:time, :lat, :lon, :source, :aqi)
            ON CONFLICT (time, latitude, longitude) DO UPDATE SET aqi = :aqi;
        """)
        
        db.execute(insert_query, records_to_insert)
        db.commit()
        
        print(f"✅ Successfully processed and inserted/updated {len(records_to_insert)} records from WAQI.")

    except Exception as e:
        print(f"An error occurred during database insertion: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fetch_and_store_waqi_data()