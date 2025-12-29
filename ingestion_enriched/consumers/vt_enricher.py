import os
import sys
import json
import time
import re
import requests
from kafka import KafkaConsumer, KafkaProducer

# ==============================
# Project root (IMPORTANT)
# ==============================
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, PROJECT_ROOT)

# ==============================
# VirusTotal API key (ENV VAR)
# ==============================
VT_API_KEY = os.getenv("VT_API_KEY")
if not VT_API_KEY:
    raise RuntimeError("VT_API_KEY not set (export VT_API_KEY=...)")

headers = {"x-apikey": VT_API_KEY}

# ==============================
# Kafka Consumer / Producer
# ==============================
consumer = KafkaConsumer(
    "raw_threats",
    bootstrap_servers="localhost:9092",
    group_id="vt_enricher",
    auto_offset_reset="earliest",
    enable_auto_commit=True,
    value_deserializer=lambda m: json.loads(m.decode())
)

producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

# ==============================
# IOC type detection
# ==============================
def ioc_type(ioc: str) -> str:
    if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", ioc):
        return "ip"
    if len(ioc) == 64:
        return "hash"
    if "." in ioc:
        return "domain"
    return "unknown"

# ==============================
# VirusTotal enrichment
# ==============================
def enrich_iocs(iocs):
    enriched = []

    for ioc in iocs:
        t = ioc_type(ioc)
        print(f"🔍 IOC detected: {ioc} (type={t})")

        if t == "domain":
            url = f"https://www.virustotal.com/api/v3/domains/{ioc}"
        elif t == "ip":
            url = f"https://www.virustotal.com/api/v3/ip_addresses/{ioc}"
        elif t == "hash":
            url = f"https://www.virustotal.com/api/v3/files/{ioc}"
        else:
            continue

        try:
            r = requests.get(url, headers=headers, timeout=10)
            time.sleep(15)  # VirusTotal FREE rate limit

            if r.status_code == 200:
                attrs = r.json()["data"]["attributes"]
                stats = attrs.get("last_analysis_stats", {})

                enriched.append({
                    "ioc": ioc,
                    "type": t,
                    "malicious": stats.get("malicious", 0),
                    "suspicious": stats.get("suspicious", 0),
                    "harmless": stats.get("harmless", 0),
                    "undetected": stats.get("undetected", 0)
                })

                print(f"✅ VT enriched: {ioc}")

            else:
                print(f"⚠️ VT error {r.status_code} for {ioc}")

        except Exception as e:
            print(f"❌ VT request failed for {ioc}: {e}")

    return enriched

# ==============================
# Main loop
# ==============================
print("🧠 VirusTotal Enricher is listening...")

for msg in consumer:
    threat = msg.value
    print("📥 Received threat from raw_threats")

    threat["vt_enrichment"] = enrich_iocs(threat.get("iocs", []))

    producer.send("enriched_threats", threat)
    producer.flush()

    print("📤 Sent enriched threat to enriched_threats\n")
