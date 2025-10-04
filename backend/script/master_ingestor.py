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

# The list of important global station IDs you provided
STATION_IDS = [
    "2554",  # New Delhi, India
    "3307",  # New York, USA
    "6323",  # Denver, USA
    "14518"  # A station in Europe
]

# A list of the pollutant columns that exist in our database table
ACCEPTED_PARAMS = ['pm25', 'pm10', 'o3', 'no2', 'so2', 'co']

def run_master_waqi_ingestion():
    """
    Fetches detailed data for a specific list of global stations and
    stores all their individual pollutant measurements in the database.
    """
    if not WAQI_API_KEY:
        raise ValueError("WAQI_API_KEY not found. Please add it to your .env file.")

    all_records_to_insert = []
    
    print(f"--- Starting Master WAQI Ingestion for {len(STATION_IDS)} stations ---")

    for station_id in STATION_IDS:
        url = f"https://api.waqi.info/feed/@{station_id}/?token={WAQI_API_KEY}"
        print(f"Fetching data for station @{station_id}...")

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get('status') != 'ok':
                print(f"  -> API returned an error for station @{station_id}: {data.get('message')}")
                continue

            station_data = data.get('data', {})
            iaqi = station_data.get('iaqi', {}) # Individual Air Quality Index (for each pollutant)
            
            # Use the station's timestamp, or the current time as a fallback
            timestamp = station_data.get('time', {}).get('s', datetime.now(timezone.utc).isoformat())
            lat = station_data.get('city', {}).get('geo', [None, None])[0]
            lon = station_data.get('city', {}).get('geo', [None, None])[1]

            if lat is None or lon is None:
                print(f"  -> Skipping station @{station_id} due to missing coordinates.")
                continue

            # Create a base record with location and time info
            base_record = {
                "time": timestamp,
                "lat": lat,
                "lon": lon,
                "source": f"WAQI-@{station_id}",
                "aqi": station_data.get('aqi')
            }

            # Add each individual pollutant measurement to the record
            for pollutant, details in iaqi.items():
                # Check if the pollutant is one we want to store and has a valid value
                if pollutant in ACCEPTED_PARAMS and 'v' in details:
                    try:
                        base_record[pollutant] = float(details['v'])
                    except (ValueError, TypeError):
                        continue # Skip if the value is not a valid number
            
            all_records_to_insert.append(base_record)
            print(f"  -> Successfully processed data for {station_data.get('city', {}).get('name')}.")

        except requests.exceptions.RequestException as e:
            print(f"  -> Failed to fetch data for station @{station_id}: {e}")
    
    if not all_records_to_insert:
        print("\nNo new records found to insert.")
        return

    # --- Bulk insert all collected data ---
    print(f"\nTotal valid records from all stations: {len(all_records_to_insert)}. Inserting into database...")
    db = SessionLocal()
    try:
        # This dynamic query will handle records with different sets of pollutants
        for record in all_records_to_insert:
            columns = record.keys() - {'lat', 'lon'} # Get all keys except lat/lon
            db_cols_str = ", ".join(columns)
            values_str = ", ".join([f":{k}" for k in columns])
            update_str = ", ".join([f"{k} = EXCLUDED.{k}" for k in columns if k != 'source'])
            
            insert_query = text(f"""
                INSERT INTO air_quality_data (latitude, longitude, {db_cols_str})
                VALUES (:lat, :lon, {values_str})
                ON CONFLICT (time, latitude, longitude) DO UPDATE SET {update_str};
            """)
            db.execute(insert_query, record)
        
        db.commit()
        print(f"✅ Successfully inserted/updated {len(all_records_to_insert)} records.")
    except Exception as e:
        print(f"Database error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    run_master_waqi_ingestion()
