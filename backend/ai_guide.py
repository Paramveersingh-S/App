# /backend/ai_guide.py
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Configure the Gemini API with your key
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-pro')

def get_gemini_response(user_profile: dict, air_quality: dict, user_question: str) -> str:
    """
    Constructs a detailed prompt and gets a personalized response from Gemini.
    """
    try:
        # --- This is our Prompt Engineering ---
        # We create a detailed context for the AI so it can give a relevant answer.
        prompt = f"""
        You are AURA, a helpful and friendly AI environmental assistant. 
        Your user's name is {user_profile.get('name', 'there')}.
        Their persona is '{user_profile.get('persona', 'a concerned citizen')}'.
        Their known health conditions are: {user_profile.get('health_conditions', 'none')}.

        Current environmental data for their location:
        - Air Quality Index (AQI): {air_quality.get('aqi', 'not available')}

        Based on all this context, please answer the following question from the user in a helpful and concise way.
        
        User's question: "{user_question}"
        """

        response = model.generate_content(prompt)
        return response.text

    except Exception as e:
        print(f"Error communicating with Gemini API: {e}")
        return "I'm sorry, I'm having trouble connecting to my reasoning engine right now. Please try again in a moment."