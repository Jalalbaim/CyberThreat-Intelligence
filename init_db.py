import sqlite3

DB_NAME = "threats.db"
conn = sqlite3.connect(DB_NAME)
cur = conn.cursor()

# =========================
# Threat documents table
# =========================
cur.execute("""
CREATE TABLE IF NOT EXISTS threats (
    doc_id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    title TEXT,
    tlp TEXT,
    created_at TEXT,
    ingested_at TEXT,
    is_phishing INTEGER,
    text TEXT
)
""")

# =========================
# Indicators of Compromise table
# =========================
cur.execute("""
CREATE TABLE IF NOT EXISTS iocs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id TEXT NOT NULL,
    ioc_type TEXT NOT NULL,
    ioc_value TEXT NOT NULL,
    FOREIGN KEY (doc_id) REFERENCES threats(doc_id)
)
""")

# =========================
# Indexes for performance
# =========================
cur.execute("CREATE INDEX IF NOT EXISTS idx_threats_created_at ON threats(created_at)")
cur.execute("CREATE INDEX IF NOT EXISTS idx_threats_is_phishing ON threats(is_phishing)")
cur.execute("CREATE INDEX IF NOT EXISTS idx_iocs_type ON iocs(ioc_type)")
cur.execute("CREATE INDEX IF NOT EXISTS idx_iocs_value ON iocs(ioc_value)")

conn.commit()
conn.close()

print("Database initialized successfully")
