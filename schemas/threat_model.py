from pydantic import BaseModel
from typing import List, Optional
import time

class ThreatRecord(BaseModel):
    source: str          # 'VirusTotal', 'OTX'
    threat_type: str     # 'Phishing', 'Malware'
    description: str     # Main text for the LLM to read
    iocs: List[str]      # IPs, Hashes, Domains
    severity: str        # 'Low', 'Medium', 'High', 'Critical'
    timestamp: float = time.time() 