# scripts/05_embed_to_qdrant.py
import requests
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import os
from pathlib import Path


def load_dotenv_value(key: str) -> str | None:
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return None

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        name, value = line.split("=", 1)
        if name.strip() == key:
            return value.strip().strip('"').strip("'")

    return None

EMBED_URL = os.getenv("EMBED_NGROK_URL") or load_dotenv_value("EMBED_NGROK_URL")
if not EMBED_URL:
    raise RuntimeError("EMBED_NGROK_URL is not set. Add it to .env or export it before running this script.")
qdrant = QdrantClient(host="localhost", port=6333)

# Tạo collection
qdrant.recreate_collection(
    collection_name="documents",
    vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
)

def embed_and_store(records: list[dict]):
    # Gọi Kaggle embedding service
    response = requests.post(
        f"{EMBED_URL}/embeddings",
        json={
            "model": "Qwen/Qwen2.5-0.5B-Instruct",
            "input": [r["text"] for r in records],
        },
        timeout=60,
    )
    response.raise_for_status()

    payload = response.json()
    embeddings = payload.get("embeddings")

    if embeddings is None and isinstance(payload.get("data"), list):
        embeddings = [item["embedding"] for item in payload["data"] if "embedding" in item]

    if not embeddings:
        raise RuntimeError(
            f"Unexpected embedding response from {EMBED_URL}/embeddings: {payload}"
        )

    points = [
        PointStruct(id=i, vector=emb, payload=rec)
        for i, (emb, rec) in enumerate(zip(embeddings, records))
    ]
    qdrant.upsert(collection_name="documents", points=points)
    print(f"Integration 5 OK: {len(points)} vectors stored in Qdrant")

# Test với sample data
embed_and_store([
    {"id": "doc_001", "text": "AI platform integration test"},
    {"id": "doc_002", "text": "Kafka to Airflow pipeline"},
])
