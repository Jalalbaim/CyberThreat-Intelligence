import os
import json
from kafka import KafkaConsumer
from sentence_transformers import SentenceTransformer
from vector_store import VectorStore # your class from vectorstore.py

# =======================
# CONFIG
# =======================
BROKER = "localhost:9092"
TOPIC = "structured-data"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_db")

# =======================
# LOAD MODEL
# =======================
print("[EMBEDDING] Loading model...")
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# =======================
# VECTOR STORE
# =======================
store = VectorStore(
    persist_dir=CHROMA_DIR, # directory for ChromaDB persistence doesn’t disappear when your program stops
    collection_name="threat-intelligence" 
)

# =======================
# KAFKA CONSUMER
# =======================
consumer = KafkaConsumer(
    TOPIC, # consume from structured-data topic
    bootstrap_servers=BROKER,
    auto_offset_reset="earliest",
    group_id="embedding-consumer", # consumer group ID
    value_deserializer=lambda v: json.loads(v.decode("utf-8"))
)

print("[EMBEDDING] Consumer started")

# =======================
# STREAM LOOP
# =======================
for msg in consumer:
    try:
        doc = msg.value # structured document

        text = doc.get("text") # get full text
        if not text: 
            continue

        embedding = model.encode(text).tolist() # generate embedding

        store.upsert(
            ids=[doc["doc_id"]], # unique ID
            embeddings=[embedding], # embedding vector
            documents=[text], # original text
            metadatas=[{
                "source": doc["source"], 
                "created_at": doc["created_at"],
                "ingested_at": doc["ingested_at"],
                "is_phishing": doc.get("is_phishing", False)
            }]
        )

        print(f"[EMBEDDING] Stored embedding {doc['doc_id']}")

    except Exception as e:
        print(f"[EMBEDDING] Error: {e}")
