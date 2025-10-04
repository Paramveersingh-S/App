import requests
from sqlalchemy import text
from database import SessionLocal

# We'll fetch a 7-day forecast for a central point in India (New Delhi)
# as this is where our other data is centered.
LATITUDE = 28.61
LONGITUDE = 77.20
API_URL = f"https://api.open-meteo.com/v1/forecast?latitude={LATITUDE}&longitude={LONGITUDE}&hourly=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m"

def fetch_and_store_weather_forecast():
    """
    Fetches hourly weather forecast data from Open-Meteo and stores it in the database.
    """
    print("Fetching weather forecast data from Open-Meteo...")

    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather data: {e}")
        return

    db = SessionLocal()
    
    try:
        hourly_data = data.get('hourly', {})
        times = hourly_data.get('time', [])
        temperatures = hourly_data.get('temperature_2m', [])
        humidities = hourly_data.get('relative_humidity_2m', [])
        precipitations = hourly_data.get('precipitation', [])
        wind_speeds = hourly_data.get('wind_speed_10m', [])

        if not times:
            print("API did not return any time data. Cannot process.")
            return

        records_to_insert = []
        for i in range(len(times)):
            records_to_insert.append({
                "time": times[i],
                "lat": LATITUDE,
                "lon": LONGITUDE,
                "temp": temperatures[i],
                "humidity": humidities[i],
                "precip": precipitations[i],
                "wind": wind_speeds[i]
            })

        if not records_to_insert:
            print("No forecast data found to insert.")
            return

        print(f"Preparing to insert {len(records_to_insert)} hourly forecast records...")

        # Clear any old forecast data from the table before inserting new data
        print("Clearing old weather forecast data...")
        db.execute(text("DELETE FROM weather_forecasts;"))
        
        insert_query = text("""
            INSERT INTO weather_forecasts (time, latitude, longitude, temperature_2m, relative_humidity_2m, precipitation, wind_speed_10m)
            VALUES (:time, :lat, :lon, :temp, :humidity, :precip, :wind)
        """)
        
        db.execute(insert_query, records_to_insert)
        db.commit()
        
        print(f"✅ Successfully inserted {len(records_to_insert)} weather forecast records.")

    except Exception as e:
        print(f"An error occurred during database insertion: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fetch_and_store_weather_forecast()

