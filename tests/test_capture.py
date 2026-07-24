from pathlib import Path
from devmemory import Memory

from devmemory.models import MemoryType

def test_manual_capture_end_to_end(tmp_path: Path):
    db_path = tmp_path / "test_store.db"
    
    # 1. Initialize our main library class
    memory = Memory(db_path=db_path)
    
    # 2. Trigger a manual capture
    test_note = "I switched from ChromaDB to Qdrant because filtering was too slow"
    memory.capture(source="manual", raw_text=test_note)
    
    # 3. Look inside the database to see if it actually saved!
    # (In a real app, we wouldn't access memory.store directly, but it's okay for testing)
    cursor = memory.store.conn.cursor()
    cursor.execute("SELECT * FROM raw_events WHERE source = 'manual'")
    rows = cursor.fetchall()
    
    # 4. Prove it worked
    assert len(rows) == 1
    assert rows[0]["raw_text"] == test_note
    assert rows[0]["processed"] == 1 # It hasn't been extracted by AI yet!

    # 5. Check if the MemoryRecord was actually created by our AI Pipeline!
    cursor.execute("SELECT * FROM memory_records")
    memories = cursor.fetchall()
    assert len(memories) == 1
    # Verify the type is a valid MemoryType (the real LLM picks the best classification)
    valid_types = [t.value for t in MemoryType]
    assert memories[0]["type"] in valid_types
    assert len(memories[0]["summary"]) > 0

    # 6. Check if the Vector Store got the embedding!
    collection_info = memory.vector_store.client.get_collection(memory.vector_store.collection_name)
    assert collection_info.points_count == 1
