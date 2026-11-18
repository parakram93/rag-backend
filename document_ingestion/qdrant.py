import uuid

from langchain_core.documents import Document
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, FieldCondition, Filter, MatchValue, PointStruct, VectorParams,
)

from document_ingestion.embeddings import embedding_model

COLL = "documents"
client = QdrantClient(host="localhost", port=6333)


def ensure_collection() -> None:
    if not client.collection_exists(COLL):
        client.create_collection(
            COLL, vectors_config=VectorParams(size=384, distance=Distance.COSINE)
        )


def store_chunks(doc_id: str, chunks: list[Document]) -> int:
    ensure_collection()
    texts = [c.page_content for c in chunks]
    vectors = embedding_model.encode(texts).tolist()      # one batch call
    points = [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=vec,
            payload={"doc_id": doc_id, "chunk_index": i, "text": text, **chunk.metadata},
        )
        for i, (vec, text, chunk) in enumerate(zip(vectors, texts, chunks))
    ]
    client.upsert(COLL, points=points)
    return len(points)


def delete_document(doc_id: str) -> None:
    client.delete(
        COLL,
        points_selector=Filter(must=[FieldCondition(key="doc_id", match=MatchValue(value=doc_id))]),
    )