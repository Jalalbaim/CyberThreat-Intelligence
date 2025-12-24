from pydantic import BaseModel
from typing import List, Optional
import time

class ThreatRecord(BaseModel):
    source: str          # e.g., 'VirusTotal', 'OTX'
    threat_type: str     # e.g., 'Phishing', 'Malware'
    description: str     # Main text for the LLM to read
    iocs: List[str]      # IPs, Hashes, Domains
    severity: str        # 'Low', 'Medium', 'High', 'Critical'
    timestamp: float = time.time()  # Unix timestamp (essential for 60-min filter)