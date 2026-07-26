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

        # If LLM returned a list instead of a dict, grab the first item
        if isinstance(extracted_data, list):
            extracted_data = extracted_data[0] if extracted_data else {}

        # Parse type with fallback if LLM returns unknown string
        raw_type = extracted_data.get("type", "note")
        try:
            record_type = MemoryType(raw_type)
        except ValueError:
            record_type = MemoryType.NOTE

        # Use actual changed_files from metadata (source of truth) over LLM extraction
        actual_files = event.metadata.get("changed_files", []) if event.metadata else []
        related_files = actual_files if actual_files else extracted_data.get("related_files", [])

        record = MemoryRecord(
            id=str(uuid.uuid4()),
            raw_event_id=event.id,
            type=record_type,
            summary=extracted_data["summary"],
            reasoning=extracted_data["reasoning"],
            tags=extracted_data.get("tags", []),
            related_files=related_files,
            source_ref=f"{event.source}:{event.id}",
            what_changed=extracted_data.get("what_changed", ""),
            timestamp=datetime.now()
        )

        self.store.save_memory_record(record)
        
        # We manually update the raw event table directly
        self.store.conn.execute("UPDATE raw_events SET processed = 1 WHERE id = ?", (event.id,))
        self.store.conn.commit()

       
        # 5. Turn full memory record into real numbers using Google Embeddings!
        if self.embedder:
            tags_str = " ".join(record.tags) if record.tags else ""
            text_to_embed = f"[{record.type.value}] {record.summary}\nWhat changed: {record.what_changed}\nReasoning: {record.reasoning}\nTags: {tags_str}"
            embedding = self.embedder.embed_text(text_to_embed)
        else:
            embedding = [0.1, 0.2, 0.3]
            
        self.vector_store.upsert(record, embedding)


