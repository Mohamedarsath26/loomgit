import json
from groq import Groq
from devmemory.config import get_key

class GroqLLMClient:
    """A real LLM client that talks to Groq's API."""
    
    def __init__(self):
        api_key = get_key("groq_api_key")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found! Run 'devmemory setup' first.")
        
        self.client = Groq(api_key=api_key)

    def extract_memory_record(self, raw_text: str, source: str, metadata: dict) -> dict:
        """Sends the raw text to Groq and asks the AI to extract structured memory data."""
        
        # Limit diff size to prevent overwhelming the AI
        diff = metadata.get('diff', 'No diff available')
        if len(diff) > 5000:
            diff = diff[:5000] + "\n... (diff truncated, see full diff in git log)"

        # Format changed files as a clear numbered list
        changed_files = metadata.get('changed_files', [])
        files_list = "\n".join(f"  {i+1}. {f}" for i, f in enumerate(changed_files)) if changed_files else "  None"

        # This is the "prompt" — the instructions we give to the AI
        prompt = f"""You are a developer memory assistant. Analyze this git commit and extract structured data.
Be SPECIFIC about this project's code — mention actual function names, class names, and concrete changes.
Do NOT write generic descriptions. Cover ALL changes across ALL files, not just the most prominent one.

Commit message: "{raw_text}"
Source: {source}
Changed files:
{files_list}

Code diff:
{diff}

Respond ONLY with a valid JSON object (no markdown, no extra text) with these exact keys:
- "type": one of ["decision", "bug_fix", "architecture", "tool_usage", "lesson_learned", "note"]
- "summary": a clear 1-sentence summary that covers the FULL scope of changes (mention all major changes, not just one)
- "what_changed": a FILE-BY-FILE breakdown. For EACH changed file, write one line in this exact format: "• filename: what was changed and why". Cover every file. Be specific — mention function names, class names, and concrete modifications.
- "reasoning": why this is worth remembering for future development
- "tags": a list of relevant keyword tags
- "related_files": MUST include ALL files from the "Changed files" list above. Do not omit any.
"""

        
        # Send the prompt to Groq's AI!
        response = self.client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1  # Low temperature = more predictable, structured output
        )
        
        # The AI's answer is a JSON string, so we parse it into a Python dictionary
        ai_answer = response.choices[0].message.content
        # Clean up markdown-wrapped JSON (e.g., ```json ... ```)
        ai_answer = ai_answer.strip()
        if ai_answer.startswith("```"):
            ai_answer = ai_answer.split("\n", 1)[1]
            ai_answer = ai_answer.rsplit("```", 1)[0]
        return json.loads(ai_answer)






