import unittest
from gemini_api import GeminiAPI

class TestGeminiAPI(unittest.TestCase):

    def setUp(self):
        """Initialize the GeminiAPI instance before each test."""
        self.gemini = GeminiAPI()

    def test_fetch_response(self):
        """Test if the fetch_response method returns a valid response."""
        prompt = "Hello, how are you?"
        
        # Simulated response test
        response = self.gemini.fetch_response(prompt)  # Only pass 'prompt'
        
        self.assertIsInstance(response, str)  # Ensure response is a string
        self.assertNotEqual(response, "")  # Response should not be empty
        self.assertNotEqual(response, "Sorry, I couldn't fetch the response.")  # Ensure it is not an error response

if __name__ == "__main__":
    unittest.main()
