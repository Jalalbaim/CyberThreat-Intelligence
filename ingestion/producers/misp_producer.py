import time
import json
from pymisp import PyMISP
from kafka import KafkaProducer
import os
import sys


project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)

from schemas.threat_model import ThreatRecord  

MISP_URL = "https://misp.example.com"
MISP_KEY = "your_misp_api_key"

producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def fetch_misp_events():
    misp = PyMISP(MISP_URL, MISP_KEY, ssl=False)
    # Fetch events from the last 1 hour
    events = misp.get_last_events(last="1h")
    
    if events and 'errors' not in events:
        for event in events:
            e = event['Event']
            threat = ThreatRecord(
                source="MISP",
                threat_type="Incident",
                description=e['info'],
                iocs=[attr['value'] for attr in e.get('Attribute', [])[:5]], # Limit IoCs for snippet
                severity="Critical" if e['threat_level_id'] == "1" else "Medium"
            )
            producer.send('raw_threats', threat.dict())
        print(f"MISP: Sent {len(events)} events to Kafka.")

if __name__ == "__main__":
    while True:
        fetch_misp_events()
        time.sleep(300)