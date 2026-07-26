from pathlib import Path
from devmemory import Memory

def _get_memory() -> Memory:
    """Creates and returns a Memory instance with the default database path."""
    db_path = Path.home() / ".devmemory" / "store.db"
    return Memory(db_path=db_path)


def search_developer_memory(query: str) -> dict:
    """Search the developer's memory for past decisions, bug fixes, lessons learned, and code changes.
    
    Use this tool when:
    - The developer asks about past work or previous changes
    - You need context about how something was previously implemented
    - The developer mentions fixing something before
    - You want to avoid repeating past mistakes
    
    Args:
        query: A natural language search query describing what to find.
    
    Returns:
        A dictionary containing the search results with summaries, reasoning, and file changes.
    """
    memory = _get_memory()
    results = memory.search(query)
    
    if not results:
        return {"status": "no_results", "message": f"No memories found for: '{query}'"}
    
    memories = []
    for record in results:
        memories.append({
            "type": record.type.value,
            "summary": record.summary,
            "what_changed": record.what_changed,
            "files": record.related_files,
            "tags": record.tags,
            "reasoning": record.reasoning,
            "date": record.timestamp.isoformat(),
        })
    
    return {"status": "success", "count": len(memories), "memories": memories}


def capture_developer_memory(note: str) -> dict:
    """Save a developer note, decision, or lesson learned into the memory database.
    
    Use this tool when:
    - The developer asks you to remember something
    - An important technical decision is made during conversation
    - A bug fix or workaround is discussed that should be saved
    
    Args:
        note: The text to save as a developer memory.
    
    Returns:
        A dictionary confirming the memory was saved.
    """
    memory = _get_memory()
    memory.capture(source="manual", raw_text=note)
    return {"status": "success", "message": f"Saved memory: '{note}'"}

