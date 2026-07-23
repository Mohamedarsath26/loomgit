import uuid
from datetime import datetime

from devmemory.store.sqlite_store import SQLiteStore
from devmemory.llm.client import LLMClient
from devmemory.models import MemoryType, MemoryRecord

class ExtractionPipeline:
    def __init__(self,store:SQLiteStore,llm: LLMClient):

        self.store = store
        self.llm = llm
    
    def process_event(self, event_id:str) -> None:

        event = self.store.get_raw_event(event_id)
        if not event:
            return

        extracted_data = self.llm.extract_memory_record(
            raw_text=event.raw_text,
            source=event.source,
            metadata=event.metadata
        )

        record = MemoryRecord(
            id=str(uuid.uuid4()),
            raw_event_id=event.id,
            type=MemoryType(extracted_data["type"]),
            summary=extracted_data["summary"],
            reasoning=extracted_data["reasoning"],
            tags=extracted_data.get("tags", []),
            related_files=extracted_data.get("related_files", []),
            source_ref=f"{event.source}:{event.id}",
            timestamp=datetime.now()
        )

        self.store.save_memory_record(record)
        
        # We manually update the raw event table directly
        self.store.conn.execute("UPDATE raw_events SET processed = 1 WHERE id = ?", (event.id,))
        self.store.conn.commit()

