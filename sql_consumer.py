import json
import sqlite3
from kafka import KafkaConsumer

DB_NAME = "threats.db"
TOPIC = "structured-data"
BROKER = "localhost:9092"

consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers=BROKER,
    auto_offset_reset="earliest",
    group_id="sql-writer",
    value_deserializer=lambda v: json.loads(v.decode("utf-8"))
)

conn = sqlite3.connect(DB_NAME)
cur = conn.cursor()

print("[SQL] Consumer started")

for msg in consumer:
    doc = msg.value

    try:
        # Insert threat metadata
        cur.execute("""
            INSERT OR IGNORE INTO threats
            (doc_id, source, title, tlp, created_at, ingested_at, is_phishing, text)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            doc["doc_id"],
            doc["source"],
            doc.get("title"),
            doc.get("tlp"),
            doc.get("created_at"),
            doc.get("ingested_at"),
            int(doc.get("is_phishing", False)),
            doc.get("text")
        ))

        # Insert IoCs
        for ioc in doc.get("iocs", []):
            cur.execute("""
                INSERT INTO iocs (doc_id, ioc_type, ioc_value)
                VALUES (?, ?, ?)
            """, (
                doc["doc_id"],
                ioc["type"],
                ioc["value"]
            ))

        conn.commit()
        print(f"[SQL] Stored threat {doc['doc_id']}")

    except Exception as e:
        print(f"[SQL] Error storing {doc.get('doc_id')}: {e}")
