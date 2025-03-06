import requests
import logging
from config import GEMINI_API_URL

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class GeminiAPI:
    """Handles Gemini AI interactions"""

    def fetch_response(self, prompt):
        try:
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            response = requests.post(GEMINI_API_URL, headers={"Content-Type": "application/json"}, json=payload)
            response.raise_for_status()
            data = response.json()
            ai_response = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "I'm not sure.")
            logging.info("AI response fetched successfully.")
            return ai_response
        except requests.RequestException as e:
            logging.error(f"Error fetching AI response: {e}")
            return "Sorry, I couldn't fetch the response."
