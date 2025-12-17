'''The script continuously fetches real-time threat intelligence pulses from AlienVault OTX,
 removes duplicates, and streams only new pulses into a Kafka topic for downstream security analysis.'''
# 
import time
import json
import requests
import os
from datetime import datetime, timezone
from kafka import KafkaProducer
from requests.exceptions import RequestException

# =======================
# CONFIGURATION
# =======================
BROKER = "localhost:9092"
TOPIC = "raw-data"
OTX_API_URL = "https://otx.alienvault.com/api/v1/pulses/subscribed?limit=20"

POLL_INTERVAL = 60          # seconds
MAX_BACKOFF = 900           # 15 minutes

OTX_API_KEY = os.getenv("OTX_API_KEY")
if not OTX_API_KEY:
    raise RuntimeError("OTX_API_KEY not set")

HEADERS = {
    "X-OTX-API-KEY": OTX_API_KEY
}

# =======================
# KAFKA PRODUCER
# =======================
producer = KafkaProducer(
    bootstrap_servers=BROKER,
    key_serializer=lambda k: k.encode("utf-8"),
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    linger_ms=500, # wait up to 500ms to batch messages
    batch_size=32768, # 32KB batch size
    retries=5 # retry up to 5 times on failure
)

print("[INGESTION] OTX ingestion started")

# =======================
# STATE
# =======================
seen_pulses = set() # to track already sent pulse IDs
backoff = POLL_INTERVAL # initial backoff

# =======================
# STREAMING LOOP
# =======================
while True: # main loop
    try:
        response = requests.get( 
            OTX_API_URL,# Fetch subscribed pulses
            headers=HEADERS,
            timeout=30
        )
        response.raise_for_status() # raise error for bad responses

        data = response.json() # parse JSON response
        pulses = data.get("results", []) # get list of pulses

        sent_count = 0

        for pulse in pulses: # process each pulse
            pulse_id = pulse.get("id") # unique pulse ID 
            if not pulse_id or pulse_id in seen_pulses: ###### skip if already seen
                continue

            seen_pulses.add(pulse_id)# mark as seen

            message = {
                "source": "otx",
                "type": "pulse",
                "pulse_id": pulse_id,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "pulse": pulse
            }

            producer.send(
                TOPIC,# send to Kafka topic
                key=pulse_id,
                value=message
            )

            sent_count += 1 # increment sent count

        print(
            f"[INGESTION] Sent {sent_count} new pulses "
            f"(received {len(pulses)})"
        )

        # reset backoff on success
        backoff = POLL_INTERVAL

    except RequestException as e:
        print(f"[INGESTION] Network/API error: {e}")

    except Exception as e:
        print(f"[INGESTION] Unexpected error: {e}")

    time.sleep(backoff)
    backoff = min(backoff * 2, MAX_BACKOFF)
