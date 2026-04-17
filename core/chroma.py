import chromadb
from chromadb.config import Settings
from core.config import CHROMA_PATH

_client = None
_collection = None

def get_chroma_collection():
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(
            path=CHROMA_PATH,
            settings=Settings(anonymized_telemetry=False)
        )
        _collection = _client.get_or_create_collection(
            name="aira_memory",
            metadata={"hnsw:space": "cosine"}
        )
    return _collection