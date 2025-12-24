import time
import json
import requests
from kafka import KafkaProducer
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)

from schemas.threat_model import ThreatRecord  

VT_API_KEY = "API KEY"
#b5a051b259b69aa9e52070086badd3556360863cbc9d77d265637b8890fd9bdb
producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def fetch_vt_threats():
    print("Fetching VirusTotal threats...")
    url = "https://www.virustotal.com/api/v3/intelligence/search?query=positives:10+"
    headers = {"x-apikey": VT_API_KEY}
    
    response = requests.get(url, headers=headers)
    print(f"VirusTotal API Response: {response.status_code}")
    if response.status_code == 200:
        data = response.json().get('data', [])
        for item in data:
            # Transform VT data to our schema
            threat = ThreatRecord(
                source="VirusTotal",
                threat_type="Malware",
                description=f"File detected with high engines: {item['attributes'].get('meaningful_name', 'Unknown')}",
                iocs=[item['id']], # The SHA256 hash
                severity="High" if item['attributes']['last_analysis_stats']['malicious'] > 20 else "Medium"
            )
            producer.send('raw_threats', threat.dict())
        print(f"✅ VirusTotal: Sent {len(data)} items to Kafka.")

if __name__ == "__main__":
    while True:
        fetch_vt_threats()
        time.sleep(300)