from pathlib import Path

from loomgit.store.sqlite_store import SQLiteStore
from loomgit.qdrant_store import QdrantVectorStore
from loomgit.capture.manual import create_manual_event
from loomgit.capture.git import create_git_event
from loomgit.extract.pipeline import ExtractionPipeline
from loomgit.llm.groq_client import GroqLLMClient
from loomgit.llm.google_embedding import GoogleEmbeddingClient

class Memory:
    """The main entrypoint for the loomgit library."""
    
    def __init__(self, db_path: str | Path):
        db_path = Path(db_path)
        # 1. Initialize our database connection and hide it inside this class
        self.store = SQLiteStore(db_path)
        self.llm = GroqLLMClient()
        self.embedder = GoogleEmbeddingClient()
        
        # 2. Real persistent Qdrant Vector Store saved to disk!
        self.vector_store = QdrantVectorStore(storage_dir=db_path.parent)
        self.pipeline = ExtractionPipeline(self.store, self.llm, self.vector_store, self.embedder)

    def capture(self, source: str, raw_text: str = "", metadata: dict | None = None, cwd: Path | str | None = None) -> None:
        """Captures a raw event and saves it to the database."""
        if metadata is None:
            metadata = {}
            
        if source == "manual":
            # 1. Use our new function to build the RawEvent object
            event = create_manual_event(raw_text,cwd=cwd)
            
            # 2. Save it to the database!
            self.store.save_raw_event(event)
            print(f"Captured manual memory: '{raw_text}'")

            self.pipeline.process_event(event.id)

        elif source == "git":
            repo_path = metadata.get("repo_path") or cwd
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

    def search(self, query: str, limit: int = 15, project_path: str | None = None) -> list:
        """Hybrid search across developer memories using both vector similarity and SQL text matching."""
        if not query or not query.strip():
            return self.list_all(limit=limit, project_path=project_path)

        seen_ids = set()
        results = []

        # 1. Vector Search
        try:
            query_embedding = self.embedder.embed_text(query)
            matching_ids = self.vector_store.search(query_embedding, limit=limit, project_path=project_path)
            for record_id in matching_ids:
                record = self.store.get_memory_record(record_id)
                if record and record.id not in seen_ids:
                    results.append(record)
                    seen_ids.add(record.id)
        except Exception:
            pass

        # 2. Text Keyword Search (Fallback & Supplement)
        try:
            text_matches = self.store.search_text_records(query, limit=limit, project_path=project_path)
            for record in text_matches:
                if record.id not in seen_ids:
                    results.append(record)
                    seen_ids.add(record.id)
        except Exception:
            pass

        return results[:limit]

    def list_all(self, limit: int = 50, order: str = "DESC", project_path: str | None = None) -> list:
        """Retrieves all memory records sorted by date and time (newest first by default)."""
        return self.store.get_all_memory_records(limit=limit, order=order, project_path=project_path)

