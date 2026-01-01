<div align="center">

# CyberThreat Intelligence System

### Real-Time Threat Detection & Analysis with RAG Architecture

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python)](https://www.python.org/)
[![Kafka](https://img.shields.io/badge/Apache%20Kafka-3.6.0-black?style=for-the-badge&logo=apache-kafka)](https://kafka.apache.org/)
[![Ollama](https://img.shields.io/badge/Ollama-Gemma%203:4b-purple?style=for-the-badge)](https://ollama.com/)

</div>

## 💡 What is This?

A **RAG (Retrieval-Augmented Generation)** system that continuously monitors cyber threats from **AlienVault OTX**, processes them in real-time using **Apache Kafka**, and delivers AI-powered intelligence reports through **Ollama's Gemma 3:4b** LLM.

## ✨ Key Features

<table>
<tr>
<td width="50%">

### 🚀 Real-Time Processing

- **Live ingestion** from AlienVault OTX (and other APIs)
- **Kafka streaming** for scalable data flow
- **60-minute time window** for fresh intelligence

</td>
<td width="50%">

### 🧠 AI-Powered Analysis

- **Hybrid search** (semantic + keyword)
- **Vector embeddings** with ChromaDB
- **LLM reports** with IoCs & recommendations

</td>
</tr>
<tr>
<td width="50%">

### 🔍 Smart Detection

- Automatic **deduplication**
- **Severity classification** (Low/Med/High)
- **IOC extraction** (IPs, domains, hashes)

</td>
<td width="50%">

### 💾 Dual Storage

- **SQLite** for long-term archival
- **ChromaDB** for fast retrieval
- **Timestamp-based filtering**

</td>
</tr>
</table>

---

## 🏗️ Architecture

```mermaid
%%{init: {'theme':'dark'}}%%
graph LR
    A[AlienVault OTX] -->|REST API| B[Producer]
    B -->|ThreatRecord| C[Kafka Topic<br/>raw_threats]
    C -->|Stream| D[Transformer]
    D -->|Vectors| E[(ChromaDB<br/>Vector Store)]
    D -->|Archive| F[(SQLite<br/>threat_archive.db)]
    G[Security Analyst] -->|Query| H[RAG App]
    H -->|Hybrid Search| E
    E -->|Context| H
    H -->|Prompt| I[Ollama LLM<br/>Gemma 3:4b]
    I -->|Report| J[Intelligence Brief]

    style A fill:#ff6b6b,stroke:#c92a2a,color:#fff
    style C fill:#4ecdc4,stroke:#087f5b,color:#fff
    style E fill:#95e1d3,stroke:#0ca678,color:#000
    style F fill:#ffd93d,stroke:#fab005,color:#000
    style I fill:#a78bfa,stroke:#7c3aed,color:#fff
    style J fill:#38d9a9,stroke:#12b886,color:#fff
```

### 🔄 How It Works

```
┌─────────────────┐
│  1. INGESTION   │  OTX Producer fetches threat pulses every
└────────┬────────┘
         │
┌────────▼────────┐
│  2. STREAMING   │  Kafka distributes ThreatRecord messages
└────────┬────────┘
         │
┌────────▼────────┐
│ 3. PROCESSING   │  Transformer extracts IOCs & stores data
└────────┬────────┘
         │
┌────────▼────────┐
│  4. RETRIEVAL   │  Hybrid search finds relevant threats
└────────┬────────┘
         │
┌────────▼────────┐
│ 5. GENERATION   │  Gemma 3:4b creates actionable intelligence report
└─────────────────┘
```

---

## 📁 Project Structure

```
CyberThreat-Intelligence/
│
├── app.py
├── requirements.txt          # Python dependencies
│
├── brain/                    # LLM
│   ├── retriever.py
│   └── generator.py
│
├── ingestion/                # Ingestion pipeline
│   ├── producers/
│   │   └── otx_producer.py
│   └── consumers/
│       └── transformer.py
│
└── data/
    ├── threat_archive.db     # SQLite
    └── chroma_db/            # ChromaDB
```

## 🎬 Running the System

<details>
<summary><b>Click to expand step-by-step guide</b></summary>

#### Terminal 1️⃣: Zookeeper

```bash
bin/zookeeper-server-start.sh config/zookeeper.properties
```

#### Terminal 2️⃣: Kafka Broker

```bash
bin/kafka-server-start.sh config/server.properties
```

#### Terminal 3️⃣: Create Kafka Topic

```bash
bin/kafka-topics.sh --bootstrap-server localhost:9092 \
  --create --topic raw_threats --partitions 1 --replication-factor 1
```

#### Terminal 4️⃣: Ollama Server

```bash
ollama serve
```

#### Terminal 5️⃣: OTX Producer

```bash
python CyberThreat-Intelligence/ingestion/producers/otx_producer.py
```

**Expected output:**

```
[INGESTION] OTX ingestion started
[INGESTION] Sent 15 new pulses (received 20)
```

#### Terminal 6️⃣: Transformer (CRITICAL)

```bash
python CyberThreat-Intelligence/ingestion/consumers/transformer.py
```

**Expected output:**

```
🚀 Transformer Consumer is listening...
Processed: OTX - Phishing at 1703456789.123
```

⏳ **Wait 30-60 seconds** for data to populate before querying!

#### Terminal 7️⃣: Launch Application

```bash
python CyberThreat-Intelligence/app.py
```

</details>

---

## 🎯 Demo

### Example Query Session

```bash
$ python CyberThreat-Intelligence/app.py

Enter your query: What are the latest phishing campaigns?

Searching last 60 minutes of data...
Generating intelligence report via Gemma 3:4b...

===========================================================
              FINAL THREAT BRIEF
===========================================================

📌 SUMMARY
In the past hour, 12 new phishing campaigns were detected
targeting financial institutions. Primary vectors include
credential harvesting via fake login portals.

🎯 INDICATORS OF COMPROMISE (IOCs)
• IPs: 192.168.1.100, 10.0.0.45
• Domains: fake-bank-login[.]com, secure-verify[.]net
• Hashes: a1b2c3d4e5f6...

⚠️ SEVERITY: HIGH

🛠️ RECOMMENDED ACTIONS
1. Block listed IPs at perimeter firewall
2. Add domains to DNS blacklist
3. Alert security awareness training team
4. Monitor for similar patterns in next 24h

===========================================================
```

## II. Enriched Threat Intelligence Pipeline

In this part, the system was **architecturally designed to support multiple threat intelligence sources**
(AlienVault OTX, VirusTotal, MISP) , each intelligence source is isolated in its own Kafka producer
and normalized into a shared ThreatRecord schema, ensuring downstream components remain source-agnostic.

## 🔹 AlienVault OTX

**Role:** Primary ingestion source

AlienVault OTX is the main threat intelligence feed actively used by the system. It provides Indicators of Compromise (IoCs), campaign context, and threat-related metadata.

- Actively ingested via a Kafka producer (`otx_producer.py`)

## 🔹 Explored but Not Fully Integrated Sources

The following sources were explored during development but were **not enabled in the final
ingestion pipeline due to practical limitations**.

### 🔸 VirusTotal

**Role:** IoC enrichment

VirusTotal was intended to enrich IoCs with reputation information such as detection counts and antivirus verdicts.

It was excluded from the live ingestion pipeline due to the following constraints:

- **Strict API rate limits** on free access tiers
- **Commercial licensing requirements** for sustained or large-scale usage

As a result, VirusTotal was deemed incompatible with the project’s runtime ingestion requirements and operational goals.

### 🔸 MISP (CERT-FR Public Feed)

**Role:** Supplementary threat intelligence source

MISP ingestion was explored using the CERT-FR public feed, but practical limitations prevented effective integration:

- **Full event context** (relationships, timelines, campaign structure) is unavailable
- **Real-time ingestion** is limited and inconsistent and do not change frequently.

Effective use of MISP would require deploying and maintaining a **private MISP instance** with full event access, synchronization, and governance.  
Such a setup would be complex and resource-intensive for a small-scale project.

## 🏗️ Overall Pipeline Design (Multi-Source)

```
┌──────────────────────────┐
│       1. INGESTION       │
│                          │
│ • OTX Producer           │
│ • MISP Producer          │
│ • VT Producer            │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│       2. STREAMING       │
│                          │
│ Topic: raw_threats       │
│ Unified ThreatRecord     │
│ (IOC, source, timestamp) │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│      3. ENRICHMENT       │
│                          │
│ vt_enricher.py           │    • Consumer from raw_threats
│ Consumer and Producer    │    • Producer to enriched_threats
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│       4. STREAMING       │
│                          │
│ Topic: enriched_threats  │
│ Fully enriched records   │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│      5. INDEXING         │
│                          │
│ enriched_transformer.py  │
│ • SQLite (metadata)      │
│ • ChromaDB (embeddings)  │
│ • IOC → Vector mapping   │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│      6. RETRIEVAL        │
│                          │
│ RAG Query Engine         │
│ • Hybrid search          │
│   (time + similarity)    │
│ • IOC / campaign aware   │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│      7. GENERATION       │
└──────────────────────────┘
```

# Conclusion of Multi-Source RAG Design

In the final implementation, **AlienVault OTX** was selected as the sole active threat intelligence ingestion source.  
This decision was driven by practical constraints related to accessibility, cost, and operational feasibility rather than theoretical completeness.

## 👥 Contributors

<table>
<tr>
<td align="center">
<a href="https://github.com/Jalalbaim">
<img src="https://github.com/Jalalbaim.png" width="100px;" alt=""/><br />
<sub><b>MJ. BAIM</b></sub>
</a><br />
💻 🔧 📖
</td>
<td align="center">
<a href="https://github.com/ayman-orkhis">
<img src="https://github.com/ayman-orkhis.png" width="100px;" alt=""/><br />
<sub><b>A. ORKHIS</b></sub>
<br />
💻 🔧 📖
</td>
</tr>
</table>

---

<div align="center">

### 🌟 If this project helped you, consider giving it a star!

Made with ❤️ by enthusiasts

**[⬆ Back to Top](#-cyberthreat-intelligence-system)**

</div>
