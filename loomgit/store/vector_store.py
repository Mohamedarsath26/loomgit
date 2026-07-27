from typing import Protocol
from loomgit.models import MemoryRecord

class VectorStore(Protocol):
    """An interface for storing and searching mathematical embeddings."""
    
    def upsert(self, record: MemoryRecord, embedding: list[float]) -> None:
        """Saves or updates a memory record's embedding in the vector database."""
        ...
        
    def search(self, query_embedding: list[float], limit: int = 5, project_path: str | None = None) -> list[str]:
        """Searches for similar memories and returns a list of their IDs."""
        ...


class DummyVectorStore:
    """A fake vector database for testing our pipeline logic."""
    
    def __init__(self):
        # We will just use a simple python dictionary to fake a real database!
        self.memory_db = {}
        
    def upsert(self, record: MemoryRecord, embedding: list[float]) -> None:
        # Save the list of numbers, using the memory's ID as the key
        self.memory_db[record.id] = embedding
        print(f"Saved dummy embedding for memory: {record.id}")
        
    def search(self, query_embedding: list[float], limit: int = 5, project_path: str | None = None) -> list[str]:
        # A real database would do complex math here to find the closest numbers.
        # But for our dummy test, we will just return the IDs of everything we have!
        return list(self.memory_db.keys())[:limit]
