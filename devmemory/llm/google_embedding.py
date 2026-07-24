import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

class GoogleEmbeddingClient:
    """A real embedding client using Google's text-embedding-004 model."""
    
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in .env file!")
        
        # Initialize Google GenAI client
        self.client = genai.Client(api_key=api_key)
        
    def embed_text(self, text: str) -> list[float]:
        """Converts raw text into a list of floating-point numbers (embedding vector)."""
        response = self.client.models.embed_content(
            model="models/gemini-embedding-001",
            contents=text,
        )
        # Extract the list of numbers from the response
        return response.embeddings[0].values
