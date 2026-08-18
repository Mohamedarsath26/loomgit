import json
import re
from groq import Groq
from loomgit.config import get_key

# Budget constants for Groq free tier (100K tokens/day, 12K tokens/min)
MAX_CHARS_PER_FILE_DIFF = 800   # ~300 tokens per file
MAX_TOTAL_DIFF_CHARS = 10000    # ~4K tokens total diff budget

class GroqLLMClient:
    """A real LLM client that talks to Groq's API."""
    
    def __init__(self):
        api_key = get_key("groq_api_key")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found! Run 'loomgit setup' first.")
        
        self.client = Groq(api_key=api_key)

    def _split_diff_per_file(self, raw_diff: str) -> dict[str, str]:
        """Splits a raw git diff into per-file chunks keyed by filename."""
        chunks: dict[str, str] = {}
        
        # Split on 'diff --git a/... b/...' headers
        parts = re.split(r'(?=^diff --git a/)', raw_diff, flags=re.MULTILINE)
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
            
            # Extract filename from 'diff --git a/path b/path'
            header_match = re.match(r'diff --git a/(.+?) b/(.+)', part)
            if header_match:
                filename = header_match.group(2)
                chunks[filename] = part
            else:
                # Non-diff content (e.g., binary file notices)
                if chunks:
                    last_key = list(chunks.keys())[-1]
                    chunks[last_key] += "\n" + part
        
        return chunks

    def _build_structured_diff(self, metadata: dict) -> str:
        """Builds a structured per-file diff section with smart truncation."""
        raw_diff = metadata.get('diff', '')
        changed_files = metadata.get('changed_files', [])
        
        if not raw_diff:
            return "No diff available."
        
        file_diffs = self._split_diff_per_file(raw_diff)
        
        # Calculate per-file budget based on number of files
        num_files = max(len(file_diffs), len(changed_files), 1)
        per_file_limit = min(MAX_CHARS_PER_FILE_DIFF, MAX_TOTAL_DIFF_CHARS // num_files)
        
        sections = []
        total_chars = 0
        
        for filename in changed_files:
            if total_chars >= MAX_TOTAL_DIFF_CHARS:
                sections.append(f"--- {filename} ---\n(skipped — token budget reached)")
                continue
                
            diff_text = file_diffs.get(filename, "")
            
            if not diff_text:
                # Try partial match (changed_files uses paths, diff may use different separator)
                for key, val in file_diffs.items():
                    if filename.replace("\\", "/") in key or key in filename:
                        diff_text = val
                        break
            
            if diff_text and len(diff_text) > per_file_limit:
                diff_text = diff_text[:per_file_limit] + "\n... (truncated)"
            elif not diff_text:
                diff_text = "(no diff content — binary or new file)"
            
            sections.append(f"--- {filename} ---\n{diff_text}")
            total_chars += len(diff_text)
        
        # Include any files in diff but not in changed_files list
        for filename, diff_text in file_diffs.items():
            if filename not in changed_files and total_chars < MAX_TOTAL_DIFF_CHARS:
                if len(diff_text) > per_file_limit:
                    diff_text = diff_text[:per_file_limit] + "\n... (truncated)"
                sections.append(f"--- {filename} ---\n{diff_text}")
                total_chars += len(diff_text)
        
        return "\n\n".join(sections)

    def extract_memory_record(self, raw_text: str, source: str, metadata: dict) -> dict:
        """Sends the raw text to Groq and asks the AI to extract structured memory data."""
        
        # Build structured per-file diff (smart chunking)
        structured_diff = self._build_structured_diff(metadata)

        # Format changed files as a clear numbered list
        changed_files = metadata.get('changed_files', [])
        files_list = "\n".join(f"  {i+1}. {f}" for i, f in enumerate(changed_files)) if changed_files else "  None"

        prompt = f"""You are a developer memory assistant. Analyze this git commit diff and extract structured data.
Be SPECIFIC about this project's code — mention actual function names, class names, and concrete changes.
Do NOT write generic descriptions or copy the raw commit message as the summary/what_changed.
Analyze the actual CODE DIFF and summarize what the code changes did across each file.

Commit message context: "{raw_text}"
Source: {source}
Changed files:
{files_list}

Per-file diffs:
{structured_diff}

Respond ONLY with a valid JSON object with these exact keys:
- "type": one of ["decision", "bug_fix", "architecture", "tool_usage", "lesson_learned", "note"]
- "summary": a clear 1-sentence summary written in plain English describing what code changes were made
- "what_changed": a FILE-BY-FILE breakdown. ONLY describe files whose actual code changes you can see above. For each file write: "• filename: what was changed and why". Be specific — mention function names, class names, and concrete modifications. Do NOT describe files marked as skipped or truncated beyond what you can see.
- "reasoning": why this is worth remembering for future development
- "tags": a list of relevant keyword tags
- "related_files": MUST include ALL files from the "Changed files" list above. Do not omit any.

CRITICAL: Ensure ALL string values are enclosed in valid double quotes. Output strictly valid JSON."""

        try:
            response = self.client.chat.completions.create(
                model="qwen/qwen3.6-27b",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                response_format={"type": "json_object"},
                extra_body={"chat_template_kwargs": {"enable_thinking": False}}
            )
            ai_answer = response.choices[0].message.content.strip()
        except Exception:
            # Fallback without response_format if Groq's strict validator rejects syntax
            try:
                response = self.client.chat.completions.create(
                    model="qwen/qwen3.6-27b",
                    messages=[{"role": "user", "content": prompt + "\n\n/no_think"}],
                    temperature=0.1
                )
                ai_answer = response.choices[0].message.content.strip()
            except Exception:
                response = self.client.chat.completions.create(
                    model="qwen/qwen3.6-27b",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1
                )
                ai_answer = response.choices[0].message.content.strip()
        
        # Strip <think>...</think> blocks that Qwen3.6 may produce
        ai_answer = re.sub(r'<think>.*?</think>', '', ai_answer, flags=re.DOTALL).strip()

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


