import pandas as pd
import joblib
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional

# Load the pre-trained model
try:
    model = joblib.load('aqi_forecaster.joblib')
    print("✅ Forecasting model 'aqi_forecaster.joblib' loaded successfully.")
except FileNotFoundError:
    model = None
    print("❌ WARNING: Forecasting model not found.")

def generate_forecast(
    db: Session, 
    lat: float, 
    lon: float, 
    hours: int = 48,
    simulation: Optional[dict] = None
) -> list:
    """
    Generates an AQI forecast. If a simulation is provided, it adjusts the baseline data.
    """
    
    # 1. Get the most recent real data for all pollutants
    latest_pollutants_query = text("""
        SELECT pm25, pm10, o3, no2, so2, co
        FROM air_quality_data
        WHERE COALESCE(pm25, pm10, o3, no2, so2, co) IS NOT NULL
        ORDER BY time DESC, ST_Distance(ST_MakePoint(longitude, latitude), ST_MakePoint(:lon, :lat))
        LIMIT 1;
    """)
    latest_pollutants_result = db.execute(latest_pollutants_query, {"lat": lat, "lon": lon}).mappings().first()
    
    if not latest_pollutants_result:
        return []

    base_pollutants = dict(latest_pollutants_result)

    # Simulation Logic: Adjusts the starting pollutant values if a simulation is active
    if simulation and simulation.get('pollutant') in base_pollutants:
        pollutant_to_reduce = simulation['pollutant']
        reduction_factor = 1 - (simulation['reduction'] / 100.0)
        
        if base_pollutants[pollutant_to_reduce] is not None:
            base_pollutants[pollutant_to_reduce] *= reduction_factor
            
    # Always recalculate the overall starting AQI from the (potentially modified) pollutant values
    pollutant_values = [v for k, v in base_pollutants.items() if v is not None]
    base_aqi = max(pollutant_values) if pollutant_values else 0

    # 2. Get the future weather forecast
    weather_forecast_query = text("""
        SELECT time, temperature_2m, relative_humidity_2m, precipitation, wind_speed_10m
        FROM weather_forecasts
        WHERE time >= NOW() ORDER BY time LIMIT :hours;
    """)
    weather_forecast = db.execute(weather_forecast_query, {"hours": hours}).mappings().all()

    if not model or not weather_forecast:
        # Fallback to a simple "persistence" forecast if model or weather is missing
        return [{"hour": f"+{i+1}h", "predicted_aqi": round(base_aqi)} for i in range(hours)]

    # 3. Use the ML model to predict on the future weather data
    forecast_df = pd.DataFrame(weather_forecast)
    forecast_df['time'] = pd.to_datetime(forecast_df['time'])
    forecast_df['hour'] = forecast_df['time'].dt.hour
    forecast_df['dayofweek'] = forecast_df['time'].dt.dayofweek
    forecast_df['month'] = forecast_df['time'].dt.month
    
    features = ['temperature_2m', 'relative_humidity_2m', 'precipitation', 'wind_speed_10m', 'hour', 'dayofweek', 'month']
    X_forecast = forecast_df[features]
    
    predicted_aqi_values = model.predict(X_forecast)
    
    # 4. Adjust the "shape" of the ML prediction based on our (potentially simulated) starting point
    adjustment_factor = base_aqi / predicted_aqi_values[0] if predicted_aqi_values[0] > 0 else 1
    adjusted_predictions = predicted_aqi_values * adjustment_factor

    forecast = []
    for i, prediction in enumerate(adjusted_predictions):
        safe_prediction = max(0, float(prediction))
        forecast.append({"hour": f"+{i+1}h", "predicted_aqi": round(safe_prediction)})

    return forecast

