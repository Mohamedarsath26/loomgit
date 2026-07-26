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
        prompt = f"""You are a developer memory assistant. Analyze this git commit diff and extract structured data.
Be SPECIFIC about this project's code — mention actual function names, class names, and concrete changes.
Do NOT write generic descriptions or copy the raw commit message as the summary/what_changed.
Analyze the actual CODE DIFF and summarize what the code changes did across each file.

Commit message context: "{raw_text}"
Source: {source}
Changed files:
{files_list}

Code diff:
{diff}

Respond ONLY with a valid JSON object with these exact keys:
- "type": one of ["decision", "bug_fix", "architecture", "tool_usage", "lesson_learned", "note"]
- "summary": a clear 1-sentence summary written in plain English describing what code changes were made
- "what_changed": a FILE-BY-FILE breakdown. For EACH changed file, write one line in this exact format: "• filename: what was changed and why". Cover every file. Be specific — mention function names, class names, and concrete modifications.
- "reasoning": why this is worth remembering for future development
- "tags": a list of relevant keyword tags
- "related_files": MUST include ALL files from the "Changed files" list above. Do not omit any.
"""

        # Send the prompt to Groq's AI!
        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,  # Low temperature = more predictable, structured output
            response_format={"type": "json_object"}
        )
        
        # The AI's answer is a JSON string, so we parse it into a Python dictionary
        ai_answer = response.choices[0].message.content.strip()
        
        # Robustly extract JSON substring ({...} or [...])
        start_idx = min([i for i in [ai_answer.find('{'), ai_answer.find('[')] if i != -1], default=-1)
        end_idx = max(ai_answer.rfind('}'), ai_answer.rfind(']'))
        
        if start_idx != -1 and end_idx != -1 and end_idx >= start_idx:
            ai_answer = ai_answer[start_idx:end_idx + 1]
            
        try:
            return json.loads(ai_answer)
        except json.JSONDecodeError:
            return {
                "type": "note",
                "summary": raw_text[:100],
                "what_changed": raw_text,
                "reasoning": "Captured from Git commit",
                "tags": ["git", "commit"],
                "related_files": metadata.get("changed_files", [])
            }






