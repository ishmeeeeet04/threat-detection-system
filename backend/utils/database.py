import sqlite3
import os
import pandas as pd

DB_PATH = "data/threats.db"


def get_connection():
    """Create and return a SQLite database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Makes rows behave like dictionaries
    return conn


def init_database():
    """
    Create the database tables if they don't exist yet.
    This is safe to call multiple times — it won't delete existing data.
    """
    os.makedirs("data", exist_ok=True)
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp       TEXT,
            ip_address      TEXT,
            username        TEXT,
            status          TEXT,
            failed_attempts INTEGER DEFAULT 0,
            port            INTEGER,
            hour            INTEGER,
            threat_score    INTEGER DEFAULT 0,
            threat_level    TEXT DEFAULT 'LOW',
            threat_color    TEXT DEFAULT '#22c55e',
            is_anomaly      INTEGER DEFAULT 0,
            created_at      TEXT DEFAULT (datetime('now'))
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            log_id       INTEGER,
            timestamp    TEXT,
            ip_address   TEXT,
            username     TEXT,
            threat_score INTEGER,
            threat_level TEXT,
            threat_color TEXT,
            description  TEXT,
            is_read      INTEGER DEFAULT 0,
            created_at   TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (log_id) REFERENCES logs(id)
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Database initialised successfully")


def load_scored_logs_to_db():
    """
    Read the scored_logs.csv file produced by the ML training
    and load it into our SQLite database.
    Clears existing data first so we don't get duplicates.
    """
    scored_path = "data/scored_logs.csv"
    if not os.path.exists(scored_path):
        print("⚠️  scored_logs.csv not found. Run ml/train_model.py first.")
        return 0

    df = pd.read_csv(scored_path)

    conn = get_connection()
    cursor = conn.cursor()

    # Clear existing data
    cursor.execute("DELETE FROM logs")
    cursor.execute("DELETE FROM alerts")

    # Insert each log entry
    inserted = 0
    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO logs
            (timestamp, ip_address, username, status,
             failed_attempts, port, hour,
             threat_score, threat_level, threat_color, is_anomaly)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(row.get("timestamp", "")),
            str(row.get("ip_address", "")),
            str(row.get("username", "")),
            str(row.get("status", "")),
            int(row.get("failed_attempts", 0)),
            int(row.get("port", 22)),
            int(row.get("hour", 12)),
            int(row.get("threat_score", 0)),
            str(row.get("threat_level", "LOW")),
            str(row.get("threat_color", "#22c55e")),
            int(row.get("is_anomaly", 0))
        ))
        log_id = cursor.lastrowid
        inserted += 1

        # If HIGH or CRITICAL, also create an alert
        level = str(row.get("threat_level", "LOW"))
        if level in ["HIGH", "CRITICAL"]:
            description = generate_alert_description(row)
            cursor.execute("""
                INSERT INTO alerts
                (log_id, timestamp, ip_address, username,
                 threat_score, threat_level, threat_color, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                log_id,
                str(row.get("timestamp", "")),
                str(row.get("ip_address", "")),
                str(row.get("username", "")),
                int(row.get("threat_score", 0)),
                level,
                str(row.get("threat_color", "#ef4444")),
                description
            ))

    conn.commit()
    conn.close()
    print(f"✅ Loaded {inserted} log entries into database")
    return inserted


def generate_alert_description(row):
    """Generate a human-readable alert description."""
    parts = []
    failed = int(row.get("failed_attempts", 0))
    hour   = int(row.get("hour", 12))
    user   = str(row.get("username", "unknown"))
    ip     = str(row.get("ip_address", "unknown"))

    if failed >= 10:
        parts.append(f"Brute force attack detected ({failed} failed attempts)")
    elif failed >= 3:
        parts.append(f"Multiple failed login attempts ({failed})")

    if hour < 5:
        parts.append(f"Suspicious login time ({hour:02d}:00)")

    if user in ["root", "admin", "administrator"]:
        parts.append(f"Targeting privileged account '{user}'")

    parts.append(f"Source IP: {ip}")

    return " | ".join(parts) if parts else f"Anomalous activity from {ip}"


def query(sql, params=()):
    """Run a SELECT query and return results as a list of dicts."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(sql, params)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


if __name__ == "__main__":
    print("Initialising database …")
    init_database()
    count = load_scored_logs_to_db()
    print(f"\nDatabase ready with {count} entries")

    # Quick check
    results = query(
        "SELECT threat_level, COUNT(*) as count FROM logs GROUP BY threat_level"
    )
    print("\nThreat level breakdown in database:")
    for r in results:
        print(f"  {r['threat_level']:<10}: {r['count']}")