"""
MISP CERT-FR Feed Producer (ATTRIBUTES-BASED)
=============================================

CERT-FR public MISP feed does NOT expose full events.
Only attribute-based JSON files are available.

This producer:
- Reads manifest metadata
- Filters recent events (last 24h)
- Downloads attribute-based events
- Deduplicates events across polling runs
- Builds unified ThreatRecord objects
- Publishes to Kafka (raw_threats)
"""

import time
import json
import os
import sys
import requests
from kafka import KafkaProducer

# ------------------------------------------------------------------
# Project path setup
# ------------------------------------------------------------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, PROJECT_ROxOT)

from schemas.threat_model import ThreatRecord

# ------------------------------------------------------------------
# Time filtering & deduplication
# ------------------------------------------------------------------
MAX_AGE = 24 * 3600  # 24 hours
SEEN_EVENTS = set()  # Prevent duplicates across runs

# ------------------------------------------------------------------
# CERT-FR MISP Feed Configuration
# ------------------------------------------------------------------
MISP_FEED_BASE = "https://misp.cert.ssi.gouv.fr/feed-misp"
MANIFEST_URL = f"{MISP_FEED_BASE}/manifest.json"
MAX_EVENTS = 20  # Safety cap per poll

# ------------------------------------------------------------------
# Kafka Producer
# ------------------------------------------------------------------
producer = KafkaProducer(
    bootstrap_servers=["localhost:9092"],
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

# ------------------------------------------------------------------
# Allowed IoC types (VT-enrichable)
# ------------------------------------------------------------------
ALLOWED_TYPES = {
    "ip-src",
    "ip-dst",
    "domain",
    "url",
    "sha256"
}

# ------------------------------------------------------------------
# Severity mapping (MISP → SOC)
# ------------------------------------------------------------------
THREAT_LEVEL_MAP = {
    "1": "Critical",
    "2": "High",
    "3": "Medium",
    "4": "Low"
}

# ------------------------------------------------------------------
# Core logic
# ------------------------------------------------------------------
def fetch_misp_attributes():
    print("📡 Fetching CERT-FR MISP attributes...")

    try:
        manifest = requests.get(MANIFEST_URL, timeout=30).json()
    except Exception as e:
        print(f"❌ Failed to fetch manifest: {e}")
        return

    now = time.time()

    # Filter recent events only
    event_ids = [
        event_id
        for event_id, meta in manifest.items()
        if now - int(meta.get("timestamp", 0)) < MAX_AGE
    ][:MAX_EVENTS]

    sent = 0

    for event_id in event_ids:
        # ----------------------------------------------------------
        # Deduplication across polling runs
        # ----------------------------------------------------------
        if event_id in SEEN_EVENTS:
            continue
        SEEN_EVENTS.add(event_id)

        try:
            event_url = f"{MISP_FEED_BASE}/{event_id}.json"
            r = requests.get(event_url, timeout=30)
            r.raise_for_status()

            data = r.json()
            event = data.get("Event", {})

            # Collect attributes (top-level + objects)
            attributes = event.get("Attribute", [])
            for obj in event.get("Object", []):
                attributes.extend(obj.get("Attribute", []))

        except Exception as e:
            print(f"⚠️ Failed to load attributes {event_id}: {e}")
            continue

        # Extract IoCs
        iocs = [
            attr["value"]
            for attr in attributes
            if attr.get("type") in ALLOWED_TYPES
        ][:10]

        if not iocs:
            continue

        # Build unified ThreatRecord
        threat = ThreatRecord(
            source="MISP-CERT-FR",
            threat_type="Incident",
            description=event.get("info", "CERT-FR Threat Intelligence"),
            iocs=iocs,
            severity=THREAT_LEVEL_MAP.get(
                str(event.get("threat_level_id", "3")),
                "Medium"
            ),
            timestamp=now
        )

        producer.send("raw_threats", threat.model_dump())
        sent += 1

    print(f"✅ CERT-FR MISP: Sent {sent} attribute-based threats to Kafka")

# ------------------------------------------------------------------
# Main loop
# ------------------------------------------------------------------
if __name__ == "__main__":
    while True:
        fetch_misp_attributes()
        time.sleep(300)  # Poll every 5 minutes
