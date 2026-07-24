import uuid
from datetime import datetime

from devmemory.store.sqlite_store import SQLiteStore
from devmemory.store.vector_store import VectorStore
from devmemory.llm.client import LLMClient
from devmemory.models import MemoryType, MemoryRecord

class ExtractionPipeline:
    def __init__(self,store:SQLiteStore,llm: LLMClient,vector_store:VectorStore, embedder=None):

        self.store = store
        self.llm = llm
        self.vector_store = vector_store
        self.embedder=embedder
    
    def process_event(self, event_id:str) -> None:

        event = self.store.get_raw_event(event_id)
        if not event:
            return

        extracted_data = self.llm.extract_memory_record(
            raw_text=event.raw_text,
            source=event.source,
            metadata=event.metadata
        )

        # Parse type with fallback if LLM returns unknown string
        raw_type = extracted_data.get("type", "note")
        try:
            record_type = MemoryType(raw_type)
        except ValueError:
            record_type = MemoryType.NOTE

        record = MemoryRecord(
            id=str(uuid.uuid4()),
            raw_event_id=event.id,
            type=record_type,
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

       
        # 5. Turn the summary into real numbers using Google Embeddings!
        if self.embedder:
            # We embed both the summary and reasoning together for better search results
            text_to_embed = f"{record.summary} {record.reasoning}"
            embedding = self.embedder.embed_text(text_to_embed)
        else:
            embedding = [0.1, 0.2, 0.3]
            
        self.vector_store.upsert(record, embedding)


