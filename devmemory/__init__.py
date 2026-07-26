from pathlib import Path

from devmemory.store.sqlite_store import SQLiteStore
from devmemory.qdrant_store import QdrantVectorStore
from devmemory.capture.manual import create_manual_event
from devmemory.capture.git import create_git_event
from devmemory.extract.pipeline import ExtractionPipeline
from devmemory.llm.groq_client import GroqLLMClient
from devmemory.llm.google_embedding import GoogleEmbeddingClient

class Memory:
    """The main entrypoint for the devmemory library."""
    
    def __init__(self, db_path: str | Path):
        db_path = Path(db_path)
        # 1. Initialize our database connection and hide it inside this class
        self.store = SQLiteStore(db_path)
        self.llm = GroqLLMClient()
        self.embedder = GoogleEmbeddingClient()
        
        # 2. Real persistent Qdrant Vector Store saved to disk!
        self.vector_store = QdrantVectorStore(storage_dir=db_path.parent)
        self.pipeline = ExtractionPipeline(self.store, self.llm, self.vector_store, self.embedder)

    def capture(self, source: str, raw_text: str = "", metadata: dict | None = None) -> None:
        """Captures a raw event and saves it to the database."""
        if metadata is None:
            metadata = {}
            
        if source == "manual":
            # 1. Use our new function to build the RawEvent object
            event = create_manual_event(raw_text)
            
            # 2. Save it to the database!
            self.store.save_raw_event(event)
            print(f"Captured manual memory: '{raw_text}'")

            self.pipeline.process_event(event.id)

        elif source == "git":
            repo_path = metadata.get("repo_path")
            event = create_git_event(repo_path=repo_path)
            commit_hash = event.metadata.get("commit_hash")

            if commit_hash and self.store.has_commit_hash(commit_hash):
                print(f"Commit {commit_hash[:7]} has already been captured. Skipping.")
                return False

            self.store.save_raw_event(event)
            print(f"Captured git memory: '{event.raw_text}'")

            self.pipeline.process_event(event.id)
            return True

        else:
            # We will handle other sources (like git commits) later!
            raise NotImplementedError(f"Source '{source}' is not supported yet!")

    def search(self, query: str, limit: int = 5) -> list:
        """Searches the database for memories matching the query."""
        
        # 1. Turn user query into real Google Embeddings!
        query_embedding = self.embedder.embed_text(query)
        
        # 2. Search the Vector Database for the closest IDs
        matching_ids = self.vector_store.search(query_embedding, limit=limit)
        
        # 3. Grab the full MemoryRecord data from SQLite for each matching ID
        results = []
        for record_id in matching_ids:
            record = self.store.get_memory_record(record_id)
            if record:
                results.append(record)
                
        return results

    def list_all(self, limit: int = 50, order: str = "DESC") -> list:
        """Retrieves all memory records sorted by date and time (newest first by default)."""
        return self.store.get_all_memory_records(limit=limit, order=order)

