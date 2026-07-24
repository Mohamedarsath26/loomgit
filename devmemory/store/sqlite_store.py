import sqlite3
import json
from pathlib import Path
from datetime import datetime

from devmemory.models import RawEvent, MemoryRecord, MemoryType


class SQLiteStore:
    def __init__(self, db_path:str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True,exist_ok=True)

        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

        self._init_db()

    def _init_db(self):
        """Creates the necessary tables if they don't exist."""
        cursor = self.conn.cursor()
        
        # Create raw_events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS raw_events (
                id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                raw_text TEXT NOT NULL,
                metadata TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                processed INTEGER DEFAULT 0
            )
        """)
        
        # Create memory_records table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory_records (
                id TEXT PRIMARY KEY,
                raw_event_id TEXT NOT NULL REFERENCES raw_events(id),
                type TEXT NOT NULL,
                summary TEXT NOT NULL,
                reasoning TEXT NOT NULL,
                tags TEXT NOT NULL,
                related_files TEXT NOT NULL,
                source_ref TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                what_changed TEXT NOT NULL DEFAULT ''
            )
        """)
        
        # Create indices for faster lookups
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_memory_type ON memory_records(type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_memory_timestamp ON memory_records(timestamp)")
        
        self.conn.commit()

    def save_raw_event(self, event: RawEvent) -> None:
        """Saves a RawEvent into the database."""
        cursor = self.conn.cursor()
        
        # We use ? as placeholders to prevent SQL injection attacks
        cursor.execute("""
            INSERT INTO raw_events (id, source, raw_text, metadata, timestamp, processed)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            event.id,
            event.source,
            event.raw_text,
            json.dumps(event.metadata),  # Convert the python dict to a JSON string
            event.timestamp.isoformat(), # Convert datetime to string
            int(event.processed)         # Convert True/False to 1/0
        ))
        
        self.conn.commit()

    def get_raw_event(self,event_id:str) -> RawEvent | None:
        
        cursor = self.conn.cursor()

        cursor.execute("SELECT * FROM raw_events WHERE id = ?", (event_id,))
        row = cursor.fetchone()

        if row is None:
            return None
        
        return RawEvent(
            id=row["id"],
            source=row["source"],
            raw_text=row["raw_text"],
            metadata=json.loads(row["metadata"]), # Convert JSON string back to dict
            timestamp=datetime.fromisoformat(row["timestamp"]), # Convert string back to datetime
            processed=bool(row["processed"]) # Convert 1/0 back to True/False
        )

    def save_memory_record(self, record: MemoryRecord) -> None:
            """Saves a MemoryRecord into the database."""
            cursor = self.conn.cursor()
            
            cursor.execute("""
                INSERT INTO memory_records (
                    id, raw_event_id, type, summary, reasoning, tags, 
                    related_files, source_ref, timestamp, what_changed
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.id,
                record.raw_event_id,
                record.type.value,           # Convert Enum to string
                record.summary,
                record.reasoning,
                json.dumps(record.tags),           # Convert list of strings to JSON string
                json.dumps(record.related_files),  # Convert list of strings to JSON string
                record.source_ref,
                record.timestamp.isoformat(),     # Convert datetime to string
                record.what_changed
            ))
            
            self.conn.commit()

    def get_memory_record(self, record_id: str) -> MemoryRecord | None:
        """Retrieves a MemoryRecord by its ID."""
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT * FROM memory_records WHERE id = ?", (record_id,))
        row = cursor.fetchone()
        
        if row is None:
            return None
            
        # Rebuild the Pydantic Object using the data from the database
        return MemoryRecord(
            id=row["id"],
            raw_event_id=row["raw_event_id"],
            type=MemoryType(row["type"]),             # Convert string back to Enum
            summary=row["summary"],
            reasoning=row["reasoning"],
            tags=json.loads(row["tags"]),             # Convert JSON string back to list
            related_files=json.loads(row["related_files"]), # Convert JSON string back to list
            source_ref=row["source_ref"],
            timestamp=datetime.fromisoformat(row["timestamp"]), # Convert string back to datetime
            what_changed=row["what_changed"],
            embedding=None # We will handle embeddings in Phase 4!
        )


    

