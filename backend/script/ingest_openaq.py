import requests
import os
from sqlalchemy import text
from database import SessionLocal
from dotenv import load_dotenv

load_dotenv()

# --- CORRECTED URL ---
# This URL uses a lat/lon/radius search over Central Europe, a very data-rich area,
# which is a more stable way to query the API.
OPENAQ_API_URL = "https://api.openaq.org/v2/measurements?limit=1000&page=1&offset=0&sort=desc&radius=1000000&lat=50.1109&lon=8.6821&order_by=datetime"

API_KEY = os.getenv("OPENAQ_API_KEY")

def fetch_and_store_openaq_data():
    """
    Fetches the latest data from OpenAQ and stores it in the database.
    """
    print("Fetching latest air quality data from OpenAQ...")
    
    headers = {
        "X-API-Key": API_KEY
    }
    
    try:
        response = requests.get(OPENAQ_API_URL, headers=headers)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from OpenAQ: {e}")
        return

    db = SessionLocal()
    insert_count = 0
    skipped_count = 0
    
    try:
        if not data.get('results'):
             print("API did not return any results.")
             return

        print(f"Found {len(data['results'])} measurements. Processing...")
        
        for measurement in data['results']:
            param = measurement.get('parameter')
            
            if not measurement.get('coordinates') or not param:
                skipped_count += 1
                continue

            latitude = measurement['coordinates']['latitude']
            longitude = measurement['coordinates']['longitude']
            value = measurement['value']
            last_updated = measurement['date']['utc']
            
            if param in ['pm25', 'no2', 'o3', 'pm10', 'so2', 'co']:
                insert_query = text(f"""
                    INSERT INTO air_quality_data (time, latitude, longitude, source, {param})
                    VALUES (:time, :lat, :lon, :source, :value)
                    ON CONFLICT (time, latitude, longitude) DO UPDATE SET {param} = :value;
                """)
                
                db.execute(insert_query, {
                    "time": last_updated,
                    "lat": latitude,
                    "lon": longitude,
                    "source": "OpenAQ",
                    "value": value
                })
                insert_count += 1
            else:
                skipped_count += 1

        db.commit()
        print(f"Successfully processed records. Inserted/Updated: {insert_count}. Skipped: {skipped_count}.")

    except Exception as e:
        print(f"An error occurred during database insertion: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fetch_and_store_openaq_data()