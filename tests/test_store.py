import uuid
from datetime import datetime
from pathlib import Path

from loomgit.models import RawEvent, MemoryRecord, MemoryType
from loomgit.store.sqlite_store import SQLiteStore

def test_store_raw_event(tmp_path: Path):
    db_path = tmp_path/"test_store.db"
    store = SQLiteStore(db_path=db_path)

    event_id = str(uuid.uuid4())
    original_event = RawEvent(
        id=event_id,
        source="manual",
        raw_text="I fixed a bug in the database",
        metadata={"project": "devmemory"},
        timestamp=datetime.now(),
        processed=False
    )

    store.save_raw_event(original_event)

    loaded_event = store.get_raw_event(event_id)

    assert loaded_event is not None
    assert loaded_event.id == original_event.id
    assert loaded_event.source == original_event.source
    assert loaded_event.raw_text == original_event.raw_text
    assert loaded_event.metadata == original_event.metadata

def test_store_memory_record(tmp_path: Path):
    db_path = tmp_path / "test_store.db"
    store = SQLiteStore(db_path=db_path)
    
    # 1. We have to create a RawEvent first, because our database rule (ForeignKey) 
    # says a MemoryRecord MUST be linked to a real RawEvent!
    raw_id = str(uuid.uuid4())
    store.save_raw_event(RawEvent(
        id=raw_id, source="manual", raw_text="dummy", metadata={}, timestamp=datetime.now()
    ))
    
    # 2. Now we create our fake MemoryRecord
    memory_id = str(uuid.uuid4())
    original_memory = MemoryRecord(
        id=memory_id,
        raw_event_id=raw_id,
        type=MemoryType.BUG_FIX,
        summary="Fixed the database bug",
        reasoning="The index was missing.",
        tags=["database", "sqlite"],
        related_files=["sqlite_store.py"],
        source_ref="manual:123",
        timestamp=datetime.now()
    )
    
    # 3. Save it and read it back
    store.save_memory_record(original_memory)
    loaded_memory = store.get_memory_record(memory_id)
    
    # 4. Prove it worked!
    assert loaded_memory is not None
    assert loaded_memory.id == original_memory.id
    assert loaded_memory.type == MemoryType.BUG_FIX
    assert loaded_memory.tags == ["database", "sqlite"]



    

