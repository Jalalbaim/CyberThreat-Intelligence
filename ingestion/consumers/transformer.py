import json
import sqlite3
import chromadb
from kafka import KafkaConsumer

# 1. Database Connections
sql_conn = sqlite3.connect('./data/threat_archive.db', check_same_thread=False)
cursor = sql_conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS archive 
                  (id INTEGER PRIMARY KEY, source TEXT, description TEXT, iocs TEXT, severity TEXT, timestamp REAL)''')

chroma_client = chromadb.PersistentClient(path="./data/chroma_db")
collection = chroma_client.get_or_create_collection(name="threat_intel")

# 2. Kafka Consumer Setup
consumer = KafkaConsumer(
    'raw_threats',
    bootstrap_servers=['localhost:9092'],
    auto_offset_reset='latest',
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

print("🚀 Transformer Consumer is listening...")

for message in consumer:
    threat = message.value
    
    # --- WRITE 1: SQL Archive ---
    cursor.execute(
        "INSERT INTO archive (source, description, iocs, severity, timestamp) VALUES (?, ?, ?, ?, ?)",
        (threat['source'], threat['description'], str(threat['iocs']), threat['severity'], threat['timestamp'])
    )
    sql_conn.commit()

    # --- WRITE 2: ChromaDB (Vector Store) ---
    collection.add(
        documents=[threat['description']],
        metadatas=[{
            "timestamp": threat['timestamp'], 
            "severity": threat['severity'], 
            "source": threat['source']
        }],
        ids=[f"id_{threat['timestamp']}"]
    )
    
    print(f"Processed: {threat['source']} - {threat['threat_type']} at {threat['timestamp']}")