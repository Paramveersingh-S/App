import requests
from typing import List, Dict, Any, Optional

# The dedicated Air Quality API URL from Open-Meteo
API_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

def generate_forecast(
    lat: float, 
    lon: float, 
    hours: int = 72, # Defaulting to 3 days (72 hours)
    simulation: Optional[dict] = None
) -> List[Dict[str, Any]]:
    """
    Generates a forecast by fetching live, historical, and forecast data directly 
    from the Open-Meteo Air Quality API using an expanded parameter set.
    """
    print(f"Fetching extended air quality forecast for lat={lat}, lon={lon} from Open-Meteo...")

    # --- THIS IS THE KEY UPGRADE ---
    # Using the new, more powerful parameter set you provided.
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": ["pm10", "pm2_5", "carbon_monoxide", "nitrogen_dioxide", "carbon_dioxide", "sulphur_dioxide", "ozone", "us_aqi"],
        "current": "us_aqi",
        "past_days": 1,
        "forecast_days": 3,
    }
    # --- END OF UPGRADE ---

    try:
        response = requests.get(API_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        current_data = data.get('current', {})
        hourly_data = data.get('hourly', {})
        
        if not hourly_data or not hourly_data.get('time'):
            print("API did not return sufficient forecast data.")
            return []

        # --- (Simulation and data transformation logic remains the same,
        # but now operates on a richer dataset) ---
        reduction_delta = 0
        if simulation and simulation.get('pollutant'):
            pollutant_to_reduce = simulation['pollutant']
            # Handle naming differences (e.g., pm25 vs pm2_5)
            if pollutant_to_reduce == 'pm25':
                pollutant_to_reduce = 'pm2_5'
            
            reduction_percent = simulation['reduction']
            current_pollutant_value = current_data.get(pollutant_to_reduce, 0)
            if current_pollutant_value is not None:
                reduction_delta = current_pollutant_value * (reduction_percent / 100.0)

        forecast_output = []
        times = hourly_data.get('time', [])
        us_aqi_values = hourly_data.get('us_aqi', [])

        # The API returns past days + current day + forecast days, so we have more data
        for i in range(len(times)):
            original_aqi = float(us_aqi_values[i]) if i < len(us_aqi_values) and us_aqi_values[i] is not None else 0
            simulated_aqi = original_aqi - reduction_delta
            
            # Create a record for each hour
            record = {
                "time": times[i], # Include the full timestamp
                "hour": i - 24 if i < 24 else f"+{i-23}", # Label past hours negatively, future positively
                "baseline_aqi": round(max(0, original_aqi)),
                "simulated_aqi": round(max(0, simulated_aqi))
            }

            # Add all other pollutant data to the record
            for key, values in hourly_data.items():
                if key not in ['time', 'us_aqi'] and i < len(values) and values[i] is not None:
                     record_key = key.replace('pm2_5', 'pm25').replace('_dioxide', 'o2').replace('_monoxide', 'o')
                     record[record_key] = values[i]

            forecast_output.append(record)

        print(f"Successfully generated a {len(forecast_output)}-hour forecast from live API.")
        return forecast_output

    except Exception as e:
        print(f"An error occurred while processing the forecast: {e}")
        return []

