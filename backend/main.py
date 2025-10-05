from fastapi import FastAPI, Depends, Form, UploadFile, File, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text, inspect
from pydantic import BaseModel, Field
from typing import List, Optional
from typing import List, Optional, Dict, Any
import json
import os
import requests
import shutil
import io
import numpy as np
import matplotlib.pyplot as plt
import mercantile
import rasterio
from rasterio.vrt import WarpedVRT
from rasterio.enums import Resampling
import xarray as xr
from dotenv import load_dotenv
from urllib.parse import quote

# Load all environment variables from .env
load_dotenv()

from forecasting_engine import generate_forecast
from database import get_db, engine
from lib.mockData import mockLocationForecast
from personalization_engine import generate_alert
from ai_guide import get_gemini_response

app = FastAPI()

# --- Environment API Keys ---
WAQI_API_KEY = os.getenv("WAQI_API_KEY")
MAPTILER_API_KEY = os.getenv("MAPTILER_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
API_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
# --- Serve Static Files for Uploaded Images ---
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# --- CORS SETTINGS ---
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://10.104.236.87:3000",
    "http://10.202.253.162:3000",
     
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models ---
class Location(BaseModel):
    lat: float
    lon: float

class UserProfile(BaseModel):
    name: str
    age_group: Optional[str] = None
    persona: Optional[str] = None
    healthConditions: Optional[List[str]] = Field(default_factory=list, alias='healthConditions')
    work_location: Optional[Location] = None
    outdoor_schedule: Optional[Dict[str, Any]] = None # To handle objects like {"days": [], "time": ""}
    podcast_keywords: Optional[List[str]] = Field(default_factory=list)

class ChatRequest(BaseModel):
    userId: int
    question: str
    lat: float
    lon: float
class ForecastDataPoint(BaseModel):
    hour: str
    predicted_aqi: float

# --- API Endpoints ---
NETCDF_FILE = r"backend\data\TEMPO_NO2_L2_V03_20250916T214329Z_S012G07.nc"

if os.path.exists(NETCDF_FILE):
    ds = xr.open_dataset(NETCDF_FILE)
    variable = "NO2_column_number_density"
    da = ds[variable].isel(time=0) if "time" in ds.dims else ds[variable]

    tif_path = "tempo.tif"
    if not os.path.exists(tif_path):
        da.rio.to_raster(tif_path)
else:
    tif_path = None
    da = None
    variable = None

@app.get("/api/v1/tempo/metadata")
def get_tempo_metadata():
    if not da:
        return {"error": "TEMPO NetCDF file not found"}
    return {
        "variable": variable,
        "shape": da.shape,
        "bounds": da.rio.bounds(),
        "crs": str(da.rio.crs)
    }

@app.get("/api/v1/tempo/tiles/{z}/{x}/{y}.png")
def get_tempo_tile(z: int, x: int, y: int):
    if not tif_path:
        return {"error": "TEMPO GeoTIFF not generated"}
    with rasterio.open(tif_path) as src:
        with WarpedVRT(src, crs="EPSG:3857", resampling=Resampling.bilinear) as vrt:
            tile_bounds = mercantile.xy_bounds(x, y, z)
            window = vrt.window(*tile_bounds)
            data = vrt.read(1, window=window, out_shape=(256, 256), resampling=Resampling.bilinear)

            arr = np.where(data == src.nodata, np.nan, data)
            vmin, vmax = np.nanpercentile(arr, (5, 95))
            norm = plt.Normalize(vmin=vmin, vmax=vmax)
            cmap = plt.cm.inferno
            rgba = cmap(norm(arr))

            img_bytes = io.BytesIO()
            plt.imsave(img_bytes, rgba, format="png")
            img_bytes.seek(0)
            return Response(content=img_bytes.getvalue(), media_type="image/png")

@app.post("/api/v1/users/register")
def register_user(profile: UserProfile, db: Session = Depends(get_db)):
    """
    Receives user profile data from the form, including work location,
    and saves it to the database.
    """
    work_location_wkt = None
    if profile.work_location:
        lon = profile.work_location.lon
        lat = profile.work_location.lat
        work_location_wkt = f"POINT({lon} {lat})"

    query = text("""
        INSERT INTO users (
            name, health_conditions, age_group, persona, work_location, 
            outdoor_schedule, podcast_keywords
        )
        VALUES (
            :name, :health_conditions, :age_group, :persona, ST_GeomFromText(:work_location, 4326),
            :outdoor_schedule, :podcast_keywords
        )
        RETURNING id;
    """)
    try:
        # --- UPDATED PARAMETERS ---
        result = db.execute(query, {
            "name": profile.name,
            "health_conditions": json.dumps(profile.healthConditions),
            "age_group": profile.age_group,
            "persona": profile.persona,
            "work_location": work_location_wkt,
            "outdoor_schedule": json.dumps(profile.outdoor_schedule),
            "podcast_keywords": json.dumps(profile.podcast_keywords)
        })
        user_id = result.scalar()
        db.commit()
        return {"message": "User profile created successfully", "user_id": user_id}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}

@app.get("/api/v1/pollutants/available")
def get_available_pollutants(db: Session = Depends(get_db)):
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns('air_quality_data')]
    available = []
    for pollutant in ['pm25', 'pm10', 'o3', 'no2', 'so2', 'co']:
        if pollutant in columns:
            query = text(f"SELECT EXISTS (SELECT 1 FROM air_quality_data WHERE {pollutant} IS NOT NULL)")
            if db.execute(query).scalar():
                available.append(pollutant.upper())
    return available

@app.get("/api/v1/grid/current")
def get_current_grid_data(
    db: Session = Depends(get_db),
    pollutant: str = 'auto',
    time_offset: int = 0
):
    pollutant_to_query = "COALESCE(pm25, pm10, o3, no2, so2, co)"
    if pollutant != 'auto':
        safe_pollutant = "".join(filter(str.isalnum, pollutant)).lower()
        if safe_pollutant in ['pm25', 'pm10', 'o3', 'no2', 'so2', 'co']:
            pollutant_to_query = safe_pollutant
    query = text(f"""
        SELECT
            latitude as lat,
            longitude as lon,
            {pollutant_to_query} as aqi
        FROM 
            air_quality_data
        WHERE 
            {pollutant_to_query} IS NOT NULL
            AND time BETWEEN 
                ((SELECT MAX(time) FROM air_quality_data) + (INTERVAL '1 hour' * :time_offset) - INTERVAL '3 hours')
                AND 
                ((SELECT MAX(time) FROM air_quality_data) + (INTERVAL '1 hour' * :time_offset) + INTERVAL '3 hours')
        LIMIT 2000;
    """)
    
    result = db.execute(query, {"time_offset": time_offset}).mappings().all()
    return list(result)


@app.get("/api/v1/users/{user_id}/personalized_alert")
def get_personalized_alert(user_id: int, lat: float, lon: float, db: Session = Depends(get_db)):
    user_profile_query = text("SELECT name, health_conditions, persona, age_group FROM users WHERE id = :user_id")
    user_profile = db.execute(user_profile_query, {"user_id": user_id}).mappings().first()

    if not user_profile:
        return {"error": "User not found"}

    air_quality_query = text("""
        WITH recent_data AS (
            SELECT * FROM air_quality_data
            WHERE time > (SELECT MAX(time) FROM air_quality_data) - INTERVAL '12 hours'
            AND COALESCE(pm25, pm10, o3, no2, so2, co) IS NOT NULL
        )
        SELECT COALESCE(pm25, pm10, o3, no2, so2, co) as aqi
        FROM recent_data
        ORDER BY ST_Distance(ST_MakePoint(longitude, latitude), ST_MakePoint(:lon, :lat))
        LIMIT 1;
    """)
    air_quality = db.execute(air_quality_query, {"lat": lat, "lon": lon}).mappings().first()
    
    if not air_quality:
        return {"risk_level": "Unknown", "recommendation": "No recent air quality data found..."}

    alert = generate_alert(dict(user_profile), dict(air_quality))
    return alert

@app.post("/api/v1/ai_guide/chat")
def chat_with_ai_guide(request: ChatRequest, db: Session = Depends(get_db)):
    user_query = text("SELECT name, health_conditions, persona FROM users WHERE id = :user_id")
    user_profile = db.execute(user_query, {"user_id": request.userId}).mappings().first()

    aq_query = text("""
        WITH recent_data AS (
            SELECT * FROM air_quality_data
            WHERE time > (SELECT MAX(time) FROM air_quality_data) - INTERVAL '12 hours'
            AND COALESCE(pm25, pm10, o3, no2, so2, co) IS NOT NULL
        )
        SELECT COALESCE(pm25, pm10, o3, no2, so2, co) as aqi
        FROM recent_data
        ORDER BY ST_Distance(ST_MakePoint(longitude, latitude), ST_MakePoint(:lon, :lat))
        LIMIT 1;
    """)
    air_quality = db.execute(aq_query, {"lat": request.lat, "lon": request.lon}).mappings().first()

    if not user_profile or not air_quality:
        return {"error": "Could not retrieve context for the AI."}

    ai_response = get_gemini_response(dict(user_profile), dict(air_quality), request.question)
    return {"response": ai_response}

@app.get("/api/v1/point/details")
def get_point_details(lat: float, lon: float):
    return mockLocationForecast

@app.get("/api/v1/location/name")
def get_location_name(lat: float, lon: float):
    if not MAPTILER_API_KEY:
        return {"name": "Location lookup unavailable"}
    
    url = f"https://api.maptiler.com/geocoding/{lon},{lat}.json?key={MAPTILER_API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        place_name = data['features'][0]['place_name'] if data.get('features') else "Unknown Location"
        return {"name": place_name}
    except Exception:
        return {"name": "Location lookup failed"}

@app.post("/api/v1/users/{user_id}/generate_podcast")
def generate_podcast_for_user(user_id: int):
    print(f"Podcast generation requested for user {user_id}. Feature not yet implemented.")
    return {
        "status": "in_progress", 
        "message": "Your personalized audio briefing is being generated."
    }

@app.post("/api/v1/hooks/google/location")
def receive_google_location_data(data: dict):
    print("Received Google Location data:", data)
    return {"status": "received"}

@app.get("/api/v1/stations/live")
def get_live_station_data():
    """
    Fetches live data for all stations in a region from the WAQI API.
    """
    if not WAQI_API_KEY:
        return {"error": "WAQI API key not configured."}
    
    bounds = "8.0,68.0,37.0,97.0" # Bounding box for India
    url = f"https://api.waqi.info/map/bounds/?latlng={bounds}&token={WAQI_API_KEY}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('status') != 'ok':
            return {"error": "Failed to fetch data from WAQI API."}
        
        valid_stations = []
        for station in data.get('data', []):
            try:
                aqi_value = int(station.get('aqi'))
                if station.get('lat') is not None and station.get('lon') is not None:
                    valid_stations.append({
                        "uid": station.get('uid'),
                        "lat": station.get('lat'),
                        "lon": station.get('lon'),
                        "aqi": aqi_value,
                        "name": station.get('station', {}).get('name')
                    })
            except (ValueError, TypeError):
                continue
        
        return valid_stations
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

@app.get("/api/v1/stations/details/{station_id}")
def get_station_details(station_id: int):
    """
    Fetches detailed, real-time data for a single station from the WAQI API.
    """
    if not WAQI_API_KEY:
        return {"error": "WAQI API key not configured."}
    
    url = f"https://api.waqi.info/feed/@{station_id}/?token={WAQI_API_KEY}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('status') != 'ok':
            return {"error": "Failed to fetch station details from WAQI API."}
        
        station_data = data.get('data', {})
        
        cleaned_data = {
            "placeName": station_data.get('city', {}).get('name'),
            "currentAQI": station_data.get('aqi'),
            "dominantPollutant": station_data.get('dominentpol'),
            "pollutantDetails": station_data.get('iaqi', {}),
            "forecast": station_data.get('forecast', {}).get('daily', {})
        }
        return cleaned_data
        
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


@app.get("/api/v1/forecast/simulate")
def get_simulation_forecast(
    lat: float, 
    lon: float, 
    pollutant: str, # e.g., 'no2'
    reduction: int, # e.g., 20
    db: Session = Depends(get_db)
):
    """
    Generates two forecasts: a baseline and a simulation with a pollutant reduction.
    """
    # 1. Generate the baseline forecast (with no simulation)
    baseline_forecast = generate_forecast(db, lat, lon, hours=48)
    
    # 2. Generate the simulated forecast by passing the simulation parameters
    simulation_params = {"pollutant": pollutant.lower(), "reduction": reduction}
    simulated_forecast = generate_forecast(db, lat, lon, hours=48, simulation=simulation_params)

    if not baseline_forecast or not simulated_forecast:
        return {"error": "Could not generate forecast. Insufficient baseline data."}

    # 3. Combine the results for easy comparison on the frontend chart
    combined_forecast = []
    for i in range(min(len(baseline_forecast), len(simulated_forecast))):
        combined_forecast.append({
            "hour": baseline_forecast[i]['hour'],
            "baseline_aqi": baseline_forecast[i]['predicted_aqi'],
            "simulated_aqi": simulated_forecast[i]['predicted_aqi'],
        })
        
    return combined_forecast

# --- (Ensure all your other endpoints like /register, /grid/current, /forecast/point etc. are also in this file) ---

@app.post("/api/v1/reports/submit")
async def submit_report(
    lat: float = Form(...),
    lon: float = Form(...),
    description: str = Form(...),
    user_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """
    Receives a new citizen science report and saves it to the database.
    """
    # In a full production app, you would handle an image file here
    # and upload it to an S3 bucket to get a real URL.
    image_url_placeholder = "https://placehold.co/600x400/27272a/FFFFFF?text=Report+Image"

    query = text("""
        INSERT INTO citizen_reports (user_id, latitude, longitude, description, image_url, status)
        VALUES (:user_id, :lat, :lon, :description, :image_url, 'verified')
        RETURNING id;
    """)
    
    try:
        result = db.execute(query, {
            "user_id": user_id,
            "lat": lat,
            "lon": lon,
            "description": description,
            "image_url": image_url_placeholder
        })
        report_id = result.scalar()
        db.commit()
        return {"message": "Report submitted successfully", "report_id": report_id}
    except Exception as e:
        db.rollback()
        # Return a more informative error
        return {"error": f"Database error: {e}"}

@app.get("/api/v1/reports/verified")
def get_verified_reports(db: Session = Depends(get_db)):
    """
    Returns all verified citizen science reports to be displayed on the map.
    """
    query = text("SELECT id, latitude as lat, longitude as lon, description, created_at FROM citizen_reports WHERE status = 'verified' ORDER BY created_at DESC")
    try:
        reports = db.execute(query).mappings().all()
        return list(reports)
    except Exception as e:
        return {"error": f"Database error: {e}"}

# --- (All your other existing endpoints like /register, /grid/current, etc. remain here) ---


@app.post("/api/v1/reports/submit")
async def submit_report(
    db: Session = Depends(get_db),
    lat: float = Form(...), 
    lon: float = Form(...), 
    description: str = Form(...),
    user_id: int = Form(...),
    file: Optional[UploadFile] = File(None)
):
    """
    Receives a new citizen science report, saves the image,
    and stores the report in the database.
    """
    image_url = None
    if file and file.filename:
        file_location = f"uploads/{file.filename}"
        with open(file_location, "wb+") as file_object:
            shutil.copyfileobj(file.file, file_object)
        image_url = f"http://127.0.0.1:8000/{file_location}"

    query = text("""
        INSERT INTO citizen_reports (user_id, latitude, longitude, description, image_url, status)
        VALUES (:user_id, :lat, :lon, :description, :image_url, 'verified')
        RETURNING id;
    """)
    
    try:
        result = db.execute(query, {
            "user_id": user_id, "lat": lat, "lon": lon,
            "description": description, "image_url": image_url
        })
        report_id = result.scalar()
        db.commit()
        return {"message": "Report submitted successfully", "report_id": report_id}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}

@app.get("/api/v1/reports/verified")
def get_verified_reports(db: Session = Depends(get_db)):
    """
    Returns all verified citizen science reports to be displayed on the map.
    """
    query = text("SELECT id, latitude as lat, longitude as lon, description, created_at, image_url FROM citizen_reports WHERE status = 'verified' ORDER BY created_at DESC")
    reports = db.execute(query).mappings().all()
    return list(reports)



@app.get("/api/v1/auth/google")
def auth_google():
    return {"message": "Placeholder: Redirect to Google for authentication."}

@app.get("/api/v1/auth/google/callback")
def auth_google_callback(code: str, db: Session = Depends(get_db)):
    print(f"Received Google auth code: {code}")
    return {"message": "Placeholder: Authentication successful."}
    
@app.post("/api/v1/users/{user_id}/generate_podcast")
def generate_podcast_for_user(user_id: int):
    return {
        "status": "in_progress", 
        "message": "Podcast generation feature not yet implemented."
    }
@app.post("/api/v1/context/location")
def get_unified_location_context(location: Location, db: Session = Depends(get_db)):
    """
    Accepts a location and returns a unified object containing the latest
    air quality from the database and live weather from an external API.
    """
    # 1. Fetch latest air quality data from our database for the given location
    air_quality_data = None
    try:
        air_quality_query = text("""
            SELECT aqi, pm25, pm10, o3, no2, so2, co, source, time
            FROM air_quality_data
            WHERE COALESCE(aqi, pm25, pm10, o3, no2, so2, co) IS NOT NULL
            ORDER BY ST_Distance(ST_MakePoint(longitude, latitude), ST_MakePoint(:lon, :lat))
            LIMIT 1;
        """)
        result = db.execute(air_quality_query, {"lat": location.lat, "lon": location.lon}).mappings().first()
        if result:
            air_quality_data = dict(result)
    except Exception as e:
        print(f"Database Error fetching AQ data: {e}")


    # 2. Fetch live, real-time weather from Open-Meteo API
    weather_data = {}
    weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={location.lat}&longitude={location.lon}&current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m"
    try:
        response = requests.get(weather_url, timeout=5)
        response.raise_for_status()
        current_weather = response.json().get('current', {})
        weather_data = {
            "temperature": current_weather.get('temperature_2m'),
            "humidity": current_weather.get('relative_humidity_2m'),
            "precipitation": current_weather.get('precipitation'),
            "wind_speed": current_weather.get('wind_speed_10m'),
        }
    except requests.exceptions.RequestException as e:
        print(f"Weather API Error: {e}")
        weather_data = {"error": "Could not fetch live weather data."}

    # 3. Combine into a single, unified response object
    return {
        "location": {"lat": location.lat, "lon": location.lon},
        "air_quality": air_quality_data,
        "weather": weather_data
    }
@app.get("/api/v1/stations/global")
def get_global_station_data():
    """
    Fetches live data for a specific list of important global stations.
    """
    if not WAQI_API_KEY:
        return {"error": "WAQI API key not configured."}

    # The list of important global station IDs you provided
    STATION_IDS = ["2554", "3307", "6323", "14518"]
    
    global_stations = []
    
    with requests.Session() as session:
        for station_id in STATION_IDS:
            url = f"https://api.waqi.info/feed/@{station_id}/?token={WAQI_API_KEY}"
            try:
                response = session.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()

                if data.get('status') != 'ok':
                    print(f"API error for station @{station_id}: {data.get('message')}")
                    continue

                station_data = data.get('data', {})
                aqi_value = int(station_data.get('aqi', 0))
                city_geo = station_data.get('city', {}).get('geo', [])
                
                if len(city_geo) == 2:
                    global_stations.append({
                        "uid": station_data.get('idx'),
                        "lat": city_geo[0],
                        "lon": city_geo[1],
                        "aqi": aqi_value,
                        "name": station_data.get('city', {}).get('name')
                    })
            except (requests.exceptions.RequestException, ValueError, TypeError) as e:
                print(f"Failed to process station @{station_id}: {e}")
                continue
    
    return global_stations

@app.get("/api/v1/tempo/no2_grid")
def get_tempo_no2_grid(db: Session = Depends(get_db)):
    """
    Fetches the most recent, high-resolution NO2 grid from the dedicated TEMPO table.
    """
    # This query finds the most recent timestamp in the tempo_grid_data table
    # and selects all records that match that timestamp.
    query = text("""
        SELECT 
            latitude as lat,
            longitude as lon,
            no2_tropospheric as aqi -- Use 'aqi' as the alias for consistency with the frontend
        FROM tempo_grid_data
        WHERE time = (SELECT MAX(time) FROM tempo_grid_data);
    """)
    
    try:
        result = db.execute(query).mappings().all()
        return list(result)
    except Exception as e:
        print(f"Error fetching TEMPO grid data: {e}")
        return {"error": "Could not retrieve TEMPO data from the database."}

# --- (Other endpoints would continue here) ---
# ...

@app.get("/api/v1/location/geocode")
def geocode_address(address: str):
    """
    Performs forward geocoding to get coordinates from a place name using MapTiler.
    """
    if not MAPTILER_API_KEY:
        return {"error": "Geocoding service unavailable."}
    
    # URL encode the address to handle spaces and special characters
    encoded_address = quote(address)
    
    url = f"https://api.maptiler.com/geocoding/{encoded_address}.json?key={MAPTILER_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('features'):
            # The coordinates are in [longitude, latitude] format
            coordinates = data['features'][0]['center']
            return {"lon": coordinates[0], "lat": coordinates[1]}
        else:
            return {"error": "Location not found."}
    except Exception as e:
        print(f"Geocoding Error: {e}")
        return {"error": "Geocoding lookup failed."}
@app.post("/api/v1/users/{user_id}/generate_podcast")
def generate_podcast_for_user(user_id: int):
    """
    Placeholder for the AI podcast generation feature.
    """
    # In the future, this will:
    # 1. Get user profile and check their interests/persona.
    # 2. Get latest AQI data.
    # 3. Generate a script with Gemini.
    # 4. Convert script to audio with a TTS service.
    # 5. Return the audio file URL.
    print(f"Podcast generation requested for user {user_id}. Feature not yet implemented.")
    return {
        "status": "in_progress", 
        "message": "Your personalized audio briefing is being generated."
    }
@app.get("/api/v1/maps/combined_view")
def get_combined_map_view(db: Session = Depends(get_db)):
    """
    Fetches the most recent TEMPO data and the most recent ground-station data
    and combines them into a single response for a global heatmap.
    """
    # 1. Get the latest high-resolution TEMPO grid data
    tempo_query = text("""
        SELECT 
            latitude as lat,
            longitude as lon,
            no2_tropospheric as aqi
        FROM tempo_grid_data
        WHERE time = (SELECT MAX(time) FROM tempo_grid_data);
    """)
    
    # 2. Get the latest ground-station data (from WAQI, OpenAQ, etc.)
    ground_query = text("""
        SELECT DISTINCT ON (source)
            latitude as lat,
            longitude as lon,
            COALESCE(aqi, pm25, pm10, o3, no2, so2, co) as aqi
        FROM air_quality_data
        WHERE COALESCE(aqi, pm25, pm10, o3, no2, so2, co) IS NOT NULL
        ORDER BY source, time DESC;
    """)
    
    try:
        tempo_result = db.execute(tempo_query).mappings().all()
        ground_result = db.execute(ground_query).mappings().all()
        
        # 3. Combine both lists and return
        combined_data = list(tempo_result) + list(ground_result)
        return combined_data
        
    except Exception as e:
        print(f"Error fetching combined map data: {e}")
        return {"error": "Could not retrieve combined data."}

@app.get("/api/v1/forecast/point")
def get_point_forecast(lat: float, lon: float):
    """
    Generates and returns a 48-hour AQI forecast for a specific point
    by calling the live Open-Meteo Air Quality API via our forecasting engine.
    """
    # Note: We no longer need the database (db: Session) for this endpoint
    forecast_data = generate_forecast(lat, lon, hours=48)
    
    if not forecast_data:
        return {"error": "Could not generate forecast from the live API."}
    
    return forecast_data

def generate_forecast(lat: float, lon: float, hours: int):
    # Your real function that returns hourly forecast list with "time" and "value" keys
    # Example stub:
    from datetime import datetime, timedelta
    base_time = datetime.utcnow()
    return [{
        "time": (base_time + timedelta(hours=i)).isoformat(timespec='minutes'),
        "value": 50 + i * 0.5  # dummy AQI values
    } for i in range(hours)]

def simulate_aqi(original: float, reduction_pct: int) -> float:
    return round(original * (1 - reduction_pct / 100), 2)

@app.get("/api/v1/forecast/simulate")
def simulate_policy(
    lat: float = Query(...),
    lon: float = Query(...),
    pollutant: str = Query("no2"),  # pollutant param can be used for advanced sim logic
    reduction: int = Query(20)
) -> List[Dict[str, Any]]:

    forecast_data = generate_forecast(lat, lon, hours=48)
    if not forecast_data:
        return {"error": "Could not generate forecast."}

    simulation = []
    for hourly_data in forecast_data:
        baseline_aqi = hourly_data["value"]
        simulated_aqi = simulate_aqi(baseline_aqi, reduction)
        simulation.append({
            "hour": hourly_data["time"][11:16],
            "baseline_aqi": baseline_aqi,
            "simulated_aqi": simulated_aqi
        })

    return simulation
