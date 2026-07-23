from pathlib import Path
from devmemory import Memory

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
    assert rows[0]["processed"] == 0 # It hasn't been extracted by AI yet!
