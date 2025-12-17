''''This script consumes raw AlienVault OTX pulses from Kafka, transforms each pulse 
into a structured threat-intelligence document by extracting IoCs and phishing indicators,
 and publishes the result to a new Kafka topic for indexing and RAG retrieval.'''
# Libraries
import json
from datetime import datetime, timezone
from kafka import KafkaConsumer, KafkaProducer

# Configuration
IN_TOPIC = "raw-data"
OUT_TOPIC = "structured-data"
BROKER = "localhost:9092"

# Kafka Consumer
consumer = KafkaConsumer(
    IN_TOPIC, # consume from raw-data topic
    bootstrap_servers=BROKER, # Kafka broker address
    auto_offset_reset="earliest", # start from earliest message
    group_id="otx-transformer", # consumer group ID
    value_deserializer=lambda v: json.loads(v.decode("utf-8"))
)
# Kafka Producer
producer = KafkaProducer(
    bootstrap_servers=BROKER, # Kafka broker address
    key_serializer=lambda k: k.encode("utf-8"), # serialize keys as UTF-8
    value_serializer=lambda v: json.dumps(v).encode("utf-8"), # serialize values as JSON
    linger_ms=500 # wait up to 500ms to batch messages
)

print("[STRUCTURED] Transformer started")

def pulse_to_document(pulse: dict) -> dict: 
    # Transform raw pulse to structured document
    # Extract IoCs
    iocs = [
        {
            "type": ind.get("type"), # IOC type
            "value": ind.get("indicator") # IOC value
        }
        for ind in pulse.get("indicators", []) 
        if ind.get("indicator") and ind.get("type") # valid IOC
    ]

    # Simple phishing heuristic
    tags = pulse.get("tags", []) # pulse tags
    is_phishing = any("phish" in tag.lower() for tag in tags) # phishing tag

    # CVE extraction
    # A CVE is a publicly known security vulnerability in software or hardware, identified by a unique ID.
    cves = [
        ref for ref in pulse.get("references", [])# extract CVEs
        if "CVE-" in ref
    ]
    # Compile full text
    text = (
        f"{pulse.get('name', '')}\n\n" # pulse name
        f"{pulse.get('description', '')}\n\n" # pulse description
        f"Tags: {', '.join(tags)}" # pulse tags
    )

    return { # structured document
        "doc_id": f"otx:{pulse.get('id')}",
        "source": "otx",
        "title": pulse.get("name"),
        "description": pulse.get("description"),
        "tags": tags,
        "tlp": pulse.get("tlp"),
        "created_at": pulse.get("created"),
        "is_phishing": is_phishing,
        "cves": cves,
        "iocs": iocs,
        "text": text,
        "ingested_at": datetime.now(timezone.utc).isoformat()
    }

for msg in consumer: # consume messages
    try:
        raw = msg.value # raw pulse data
        pulse = raw.get("pulse") # extract pulse
        pulse_id = raw.get("pulse_id") # extract pulse ID

        if not pulse or not pulse_id: # invalid message
            continue

        doc = pulse_to_document(pulse) # transform to structured document

        producer.send(
            OUT_TOPIC, # send to structured-data topic  
            key=pulse_id,
            value=doc
        )

        print(f"[STRUCTURED] Processed pulse {pulse_id}")

    except Exception as e:
        print(f"[STRUCTURED] Error processing message: {e}")
