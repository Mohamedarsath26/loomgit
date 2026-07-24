from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from devmemory.models import MemoryRecord

class QdrantVectorStore:
    """A real vector database using local Qdrant (saved to disk!)."""
    
    def __init__(self, storage_dir: Path):
        # Local Qdrant stored on disk next to sqlite!
        self.client = QdrantClient(path=str(storage_dir / "qdrant_db"))
        self.collection_name = "memories"
        
        # Create collection if it doesn't exist (3072 vector size for Google Embeddings)
        collections = [c.name for c in self.client.get_collections().collections]
        if self.collection_name not in collections:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=3072, distance=Distance.COSINE)
            )

    def upsert(self, record: MemoryRecord, embedding: list[float]) -> None:
        """Saves a record's vector embedding into Qdrant."""
        # Qdrant accepts valid UUID strings directly as point IDs!
        point_id = record.id
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={"record_id": record.id}
                )
            ]
        )

    def search(self, query_embedding: list[float], limit: int = 5) -> list[str]:
        """Performs real mathematical cosine similarity search!"""
        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_embedding,
            limit=limit
        ).points
        return [hit.payload["record_id"] for hit in results]
