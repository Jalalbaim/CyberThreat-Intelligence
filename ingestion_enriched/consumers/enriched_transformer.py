import os
import sys
import json
import sqlite3
from kafka import KafkaConsumer
import chromadb
from chromadb.utils import embedding_functions
import time

# ---------------- PATH FIX ----------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, PROJECT_ROOT)

# ---------------- SQLITE ----------------
DB_PATH = os.path.join(PROJECT_ROOT, "data", "threat_archive.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

sql_conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = sql_conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS enriched_threats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT,
    threat_type TEXT,
    severity TEXT,
    description TEXT,
    vt_summary TEXT,
    timestamp REAL
)
""")
sql_conn.commit()

# ---------------- CHROMADB ----------------
chroma_client = chromadb.PersistentClient(
    path=os.path.join(PROJECT_ROOT, "data", "chroma_db")
)

embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

collection = chroma_client.get_or_create_collection(
    name="threat_intel",
    embedding_function=embedding_function
)

# ---------------- KAFKA CONSUMER ----------------
consumer = KafkaConsumer(
    "enriched_threats",
    bootstrap_servers="localhost:9092",
    auto_offset_reset="earliest",
    enable_auto_commit=True,
    value_deserializer=lambda m: json.loads(m.decode())
)

print("🧠 Enriched Transformer running...")

# ---------------- HELPERS ----------------
def build_vt_summary(vt_data):
    if not vt_data:
        return "No VirusTotal enrichment available."

    high = [ioc for ioc in vt_data if ioc.get("malicious", 0) >= 30]
    medium = [ioc for ioc in vt_data if 10 <= ioc.get("malicious", 0) < 30]

    parts = []

    if high:
        parts.append(
            f"{len(high)} indicators flagged by more than 30 VirusTotal engines."
        )
    if medium:
        parts.append(
            f"{len(medium)} indicators flagged by 10–30 VirusTotal engines."
        )

    return " ".join(parts)

# ---------------- MAIN LOOP ----------------
for msg in consumer:
    threat = msg.value

    vt_summary = build_vt_summary(threat.get("vt_enrichment", []))

    # --------- SQLITE STORE ---------
    cursor.execute("""
        INSERT INTO enriched_threats
        (source, threat_type, severity, description, vt_summary, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        threat.get("source"),
        threat.get("threat_type"),
        threat.get("severity"),
        threat.get("description"),
        vt_summary,
        threat.get("timestamp", time.time())
    ))
    sql_conn.commit()

    # --------- TEXT FOR RAG ---------
    rag_text = f"""
SOURCE: {threat['source']}
Threat Type: {threat.get('threat_type')}
Source: {threat.get('source')}
Severity: {threat.get('severity')}

Description:
{threat.get('description')}

VirusTotal Analysis:
{vt_summary}
""".strip()

    # --------- CHROMADB INDEX ---------
    collection.add(
        documents=[rag_text],
        metadatas=[{
            "source": threat.get("source"),
            "severity": threat.get("severity"),
            "timestamp": threat.get("timestamp", time.time())
        }],
        ids=[str(time.time())]
    )

    print("✅ Indexed enriched threat into SQLite + ChromaDB")
