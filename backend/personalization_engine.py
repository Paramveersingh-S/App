# /backend/personalization_engine.py

def generate_alert(user_profile: dict, air_quality: dict) -> dict:
    """
    Generates a personalized health alert based on user profile and air quality.
    
    Args:
        user_profile (dict): A dictionary containing user data (e.g., name, health_conditions).
        air_quality (dict): A dictionary containing the latest AQI data.

    Returns:
        dict: A dictionary containing the risk level and a personalized recommendation.
    """
    if not user_profile or not air_quality:
        return {
            "risk_level": "Unknown",
            "recommendation": "Could not retrieve user or air quality data."
        }

    aqi = air_quality.get('aqi')
    health_conditions = user_profile.get('health_conditions', [])
    is_sensitive = any(condition in ['Asthma', 'Allergies', 'Heart Condition', 'Pregnancy'] for condition in health_conditions)

    if aqi is None:
        return {"risk_level": "Unknown", "recommendation": "No AQI data available for this location."}

    # --- This is our simple rules engine ---
    if aqi <= 50:
        return {"risk_level": "Good", "recommendation": "Air quality is good. It's a great day for outdoor activities!"}
    
    elif aqi <= 100:
        if is_sensitive:
            return {"risk_level": "Moderate", "recommendation": "Air quality is moderate. Sensitive individuals should consider reducing prolonged outdoor exertion."}
        else:
            return {"risk_level": "Moderate", "recommendation": "Air quality is acceptable. Unusually sensitive people should consider reducing outdoor exertion."}
            
    elif aqi <= 150:
        if is_sensitive:
            return {"risk_level": "High", "recommendation": "Unhealthy for sensitive groups. Limit your time outdoors and avoid strenuous activities."}
        else:
            return {"risk_level": "Moderate", "recommendation": "Members of sensitive groups may experience health effects. The general public is not likely to be affected."}

    else: # aqi > 150
        if is_sensitive:
            return {"risk_level": "Very High", "recommendation": "Health alert: everyone may experience more serious health effects. You should avoid all outdoor exertion."}
        else:
            return {"risk_level": "High", "recommendation": "Health alert: the risk of health effects is increased for everyone. Avoid prolonged outdoor exertion."}