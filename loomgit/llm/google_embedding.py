from google import genai
from loomgit.config import get_key

class GoogleEmbeddingClient:
    """A real embedding client using Google's text-embedding-004 model."""
    
    def __init__(self):
        api_key = get_key("google_api_key")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found! Run 'loomgit setup' first.")
        
        self.client = genai.Client(api_key=api_key)
        
    def embed_text(self, text: str) -> list[float]:
        """Converts raw text into a list of floating-point numbers (embedding vector)."""
        response = self.client.models.embed_content(
            model="models/gemini-embedding-001",
            contents=text,
        )
        # Extract the list of numbers from the response
        return response.embeddings[0].values
