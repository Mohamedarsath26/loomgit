import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

class GroqLLMClient:
    """A real LLM client that talks to Groq's API."""
    
    def __init__(self):
        # Grab the API key from the .env file
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in .env file!")
        
        # Create the Groq client
        self.client = Groq(api_key=api_key)

    def extract_memory_record(self, raw_text: str, source: str, metadata: dict) -> dict:
        """Sends the raw text to Groq and asks the AI to extract structured memory data."""
        
        # This is the "prompt" — the instructions we give to the AI
        prompt = f"""You are a developer memory assistant. Analyze this developer note and extract structured data.

        Developer note: "{raw_text}"
        Source: {source}

        Respond ONLY with a valid JSON object (no markdown, no extra text) with these exact keys:
        - "type": one of ["decision", "bug_fix", "architecture", "tool_usage", "lesson_learned", "note"]
        - "summary": a clear 1-sentence summary
        - "reasoning": why this is worth remembering
        - "tags": a list of relevant keyword tags
        - "related_files": a list of any file paths mentioned (empty list if none)
        """
        
        # Send the prompt to Groq's AI!
        response = self.client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1  # Low temperature = more predictable, structured output
        )
        
        # The AI's answer is a JSON string, so we parse it into a Python dictionary
        ai_answer = response.choices[0].message.content
        return json.loads(ai_answer)





