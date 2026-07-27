from pathlib import Path
from loomgit import Memory
from loomgit.models import MemoryType

def test_search_end_to_end(tmp_path: Path):
    db_path = tmp_path / "test_store.db"
    memory = Memory(db_path=db_path)
    
    # 1. Capture a memory (this saves to SQLite, passes through AI, and saves to Vector Store)
    memory.capture(source="manual", raw_text="I fixed a bug in the database")
    
    # 2. Search for it!
    results = memory.search("Find me database bugs")
    
    # 3. Prove that our search successfully pulled the MemoryRecord all the way out!
    assert len(results) == 1
    # Verify the type is a valid MemoryType (the real LLM picks the best classification)
    valid_types = [t.value for t in MemoryType]
    assert results[0].type.value in valid_types
    assert len(results[0].summary) > 0
