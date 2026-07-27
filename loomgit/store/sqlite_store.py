import sqlite3
import json
import uuid
from pathlib import Path
from datetime import datetime

from loomgit.models import RawEvent, MemoryRecord, MemoryType


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

        for table in ["raw_events", "memory_records"]:
            for col in ["project_path", "project_name"]:
                try:
                    cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col} TEXT DEFAULT ''")
                except sqlite3.OperationalError:
                    pass  # Column already exists!
        
        # Backfill legacy historical records created before project-scoping feature
        current_path = str(Path.cwd().resolve())
        current_name = Path.cwd().resolve().name
        cursor.execute("UPDATE memory_records SET project_path = ?, project_name = ? WHERE project_path = '' OR project_path IS NULL", (current_path, current_name))
        cursor.execute("UPDATE raw_events SET project_path = ?, project_name = ? WHERE project_path = '' OR project_path IS NULL", (current_path, current_name))
        
        self.conn.commit()

    def save_raw_event(self, event: RawEvent) -> None:
        """Saves a RawEvent into the database."""
        cursor = self.conn.cursor()
        
        # We use ? as placeholders to prevent SQL injection attacks
        cursor.execute("""
            INSERT INTO raw_events (id, source, raw_text, metadata, timestamp, processed, project_path, project_name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event.id,
            event.source,
            event.raw_text,
            json.dumps(event.metadata),  # Convert the python dict to a JSON string
            event.timestamp.isoformat(), # Convert datetime to string
            int(event.processed),        # Convert True/False to 1/0
            event.project_path,
            event.project_name
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
            processed=bool(row["processed"]), # Convert 1/0 back to True/False,
             project_path=row["project_path"] if "project_path" in row.keys() else "",
            project_name=row["project_name"] if "project_name" in row.keys() else "",
        )

    def save_memory_record(self, record: MemoryRecord) -> None:
            """Saves a MemoryRecord into the database."""
            cursor = self.conn.cursor()
            
            cursor.execute("""
                INSERT INTO memory_records (
                    id, raw_event_id, type, summary, reasoning, tags, 
                    related_files, source_ref, timestamp, what_changed, project_path, project_name
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                record.what_changed,
                record.project_path,
                record.project_name
            ))
            
            self.conn.commit()

    def _safe_get(self, row, key: str, default=None):
        """Safely access a row value by column name, handling both Row and tuple types."""
        try:
            val = row[key]
            return val if val is not None else default
        except (IndexError, KeyError, TypeError):
            return default

    def _row_to_memory_record(self, row) -> MemoryRecord:
        """Safely parses a SQLite row into a MemoryRecord with robust fallbacks for null/legacy data."""
        # 1. Type fallback
        raw_type = self._safe_get(row, "type", "note")
        try:
            rec_type = MemoryType(raw_type)
        except (ValueError, KeyError):
            rec_type = MemoryType.NOTE

        # 2. Tags fallback
        raw_tags = self._safe_get(row, "tags", "")
        if raw_tags:
            try:
                tags = json.loads(raw_tags) if isinstance(raw_tags, str) else list(raw_tags)
            except Exception:
                tags = []
        else:
            tags = []

        # 3. Related files fallback
        raw_files = self._safe_get(row, "related_files", "")
        if raw_files:
            try:
                related_files = json.loads(raw_files) if isinstance(raw_files, str) else list(raw_files)
            except Exception:
                related_files = []
        else:
            related_files = []

        # 4. Strings & Datetime fallbacks
        summary = self._safe_get(row, "summary", "No summary provided")
        reasoning = self._safe_get(row, "reasoning", "")
        what_changed = self._safe_get(row, "what_changed", "")
        source_ref = self._safe_get(row, "source_ref", "")

        timestamp_str = self._safe_get(row, "timestamp", "")
        try:
            timestamp = datetime.fromisoformat(timestamp_str) if timestamp_str else datetime.now()
        except Exception:
            timestamp = datetime.now()

        project_path = self._safe_get(row, "project_path", "")
        project_name = self._safe_get(row, "project_name", "")

        rec_id = self._safe_get(row, "id", str(uuid.uuid4()))

        return MemoryRecord(
            id=rec_id,
            raw_event_id=self._safe_get(row, "raw_event_id", ""),
            type=rec_type,
            summary=summary,
            reasoning=reasoning,
            tags=tags,
            related_files=related_files,
            source_ref=source_ref,
            timestamp=timestamp,
            what_changed=what_changed,
            project_path=project_path,
            project_name=project_name,
            embedding=None
        )

    def get_memory_record(self, record_id: str) -> MemoryRecord | None:
        """Retrieves a MemoryRecord by its ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM memory_records WHERE id = ?", (record_id,))
        row = cursor.fetchone()
        
        if row is None:
            return None
            
        return self._row_to_memory_record(row)

    def get_all_memory_records(self, limit: int = 50, order: str = "DESC", project_path: str | None = None) -> list[MemoryRecord]:
        """Retrieves all MemoryRecords sorted by timestamp."""
        cursor = self.conn.cursor()
        order_str = "ASC" if order.upper() == "ASC" else "DESC"

        query = "SELECT * FROM memory_records"
        params: list = []

        if project_path and project_path.strip():
            query += " WHERE project_path = ?"
            params.append(str(project_path.strip()))

        query += f" ORDER BY timestamp {order_str} LIMIT ?"
        params.append(int(limit))

        try:
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
        except Exception:
            return []

        results = []
        for row in rows:
            try:
                results.append(self._row_to_memory_record(row))
            except Exception:
                continue
        return results

    def has_commit_hash(self, commit_hash: str) -> bool:
        """Checks if a Git commit hash has already been captured in raw_events."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT 1 FROM raw_events WHERE source = 'git' AND metadata LIKE ? LIMIT 1",
            (f'%"commit_hash": "{commit_hash}"%',)
        )
        return cursor.fetchone() is not None

    def search_text_records(self, query: str, limit: int = 15, project_path: str | None = None) -> list[MemoryRecord]:
        """Searches MemoryRecords using SQL LIKE keyword matching."""
        cursor = self.conn.cursor()
        q_wildcard = f"%{query.strip()}%"
        
        sql = """
            SELECT * FROM memory_records 
            WHERE (summary LIKE ? OR reasoning LIKE ? OR what_changed LIKE ? OR tags LIKE ? OR related_files LIKE ?)
        """
        params = [q_wildcard, q_wildcard, q_wildcard, q_wildcard, q_wildcard]
        
        if project_path and project_path.strip():
            sql += " AND project_path = ?"
            params.append(project_path.strip())
            
        sql += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall()
        return [self._row_to_memory_record(row) for row in rows]

    def get_unique_projects(self) -> list[dict]:
        """Returns a list of all distinct project folders captured in memory."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT DISTINCT project_name, project_path FROM memory_records WHERE project_path != ''"
        )
        rows = cursor.fetchall()
        return [{"name": row["project_name"], "path": row["project_path"]} for row in rows]


    

