from pathlib import Path

from devmemory.store.sqlite_store import SQLiteStore
from devmemory.capture.manual import create_manual_event
from devmemory.extract.pipeline import ExtractionPipeline
from devmemory.llm.client import DummyLLMClient

class Memory:
    """The main entrypoint for the devmemory library."""
    
    def __init__(self, db_path: str | Path):
        # 1. Initialize our database connection and hide it inside this class
        self.store = SQLiteStore(db_path)

    def capture(self, source: str, raw_text: str, metadata: dict | None = None) -> None:
        """Captures a raw event and saves it to the database."""
        if metadata is None:
            metadata = {}
            
        if source == "manual":
            # 1. Use our new function to build the RawEvent object
            event = create_manual_event(raw_text)
            
            # 2. Save it to the database!
            self.store.save_raw_event(event)
            print(f"Captured manual memory: '{raw_text}'")
        else:
            # We will handle other sources (like git commits) later!
            raise NotImplementedError(f"Source '{source}' is not supported yet!")

