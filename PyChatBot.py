import nltk
import random
import datetime
import requests
from nltk.chat.util import Chat, reflections

# Download necessary NLTK data
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')

# --- Rule-Based Responses ---
rules = [
    (r'hi|hello|hey', ['Hello!', 'Hi there!', 'Hey!']),
    (r'how are you?', ["I'm good, thanks!", "Doing well!", "All systems go!"]),
    (r'what is your name?', ["I'm ChatBot 3000.", "Call me CB.", "I'm your digital assistant."]),
    (r'bye|goodbye', ['Goodbye!', 'See you later!', 'Bye!']),
]

# --- API Integration Example (Weather) ---
def get_weather(city):
    API_KEY = "YOUR_API_KEY"  # Replace with your OpenWeatherMap API key
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
    try:
        response = requests.get(url)
        data = response.json()
        temp = data['main']['temp']
        return f"Weather in {city}: {temp}°C, {data['weather'][0]['description']}"
    except Exception:
        return "Sorry, I couldn't fetch the weather."

# --- Enhanced Chatbot Class ---
class AdvancedChatBot(Chat):
    def __init__(self):
        super().__init__(rules, reflections)

    def respond(self, user_input):
        # Check for weather queries
        if 'weather' in user_input.lower():
            tokens = nltk.word_tokenize(user_input)
            cities = [word for word, pos in nltk.pos_tag(tokens) if pos == 'NNP']
            if cities:
                return get_weather(cities[0])
            return "Please specify a city for weather info."
        
        # Check for time query dynamically
        if 'time' in user_input.lower():
            return f"Current time: {datetime.datetime.now().strftime('%H:%M')}"
        
        # Fallback to rule-based responses
        return super().respond(user_input)

# --- Main Interaction Loop ---
if __name__ == "__main__":
    bot = AdvancedChatBot()
    print("ChatBot: Hello! Ask me about the weather or chat normally. Type 'quit' to exit.")
    
    while True:
        user_input = input("You: ")
        if user_input.lower() == 'quit':
            print("ChatBot: Goodbye!")
            break

        response = bot.respond(user_input)
        if not response:  # Handle unknown inputs
            response = random.choice([
                "Could you rephrase that?",
                "I'm still learning!",
                "Interesting, tell me more."
            ])
        
        print(f"ChatBot: {response}")