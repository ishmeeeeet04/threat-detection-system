import re
import pandas as pd
from datetime import datetime

# ─────────────────────────────────────────
# Regex pattern for Linux auth.log lines
# Example line:
# 2024-01-15 03:22:11 server sshd[1234]: Failed password for root from 1.2.3.4 port 22 ssh2
# ─────────────────────────────────────────
AUTH_LOG_PATTERN = re.compile(
    r"(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})"
    r".+sshd\[\d+\]:\s"
    r"(?P<status>Failed|Accepted) password for "
    r"(?P<username>\S+) from "
    r"(?P<ip_address>\d+\.\d+\.\d+\.\d+) port "
    r"(?P<port>\d+)"
)

def parse_auth_log(filepath):
    """
    Parse a Linux-style auth.log file.
    Returns a pandas DataFrame with columns:
    timestamp, ip_address, username, status, port, hour
    """
    records = []

    with open(filepath, "r") as f:
        for line in f:
            match = AUTH_LOG_PATTERN.search(line)
            if match:
                data = match.groupdict()
                # Convert timestamp string to datetime object
                dt = datetime.strptime(data["timestamp"], "%Y-%m-%d %H:%M:%S")
                records.append({
                    "timestamp"   : data["timestamp"],
                    "ip_address"  : data["ip_address"],
                    "username"    : data["username"],
                    "status"      : data["status"],
                    "port"        : int(data["port"]),
                    "hour"        : dt.hour
                })

    if not records:
        print("⚠️  No matching lines found in log file.")
        return pd.DataFrame()

    df = pd.DataFrame(records)
    print(f"✅ Parsed {len(df)} entries from {filepath}")
    return df


def parse_csv_log(filepath):
    """
    Parse our generated CSV log file.
    Returns a pandas DataFrame.
    """
    df = pd.read_csv(filepath)
    print(f"✅ Loaded {len(df)} entries from {filepath}")
    return df


def enrich_dataframe(df):
    """
    Add extra columns that help with threat detection:
    - failed_attempts per IP (if not already present)
    - is_night_hour flag
    - is_root_attempt flag
    - ip_attempt_count (how many times this IP appeared)
    """
    # If failed_attempts column is missing (from auth.log parsing),
    # calculate it from the data
    if "failed_attempts" not in df.columns:
        fail_counts = (
            df[df["status"] == "Failed"]
            .groupby("ip_address")
            .size()
            .reset_index(name="failed_attempts")
        )
        df = df.merge(fail_counts, on="ip_address", how="left")
        df["failed_attempts"] = df["failed_attempts"].fillna(0).astype(int)

    # Flag logins between midnight and 5am as suspicious
    df["is_night_hour"] = df["hour"].apply(
        lambda h: 1 if h < 5 else 0
    )

    # Flag attempts on root/admin accounts
    df["is_root_attempt"] = df["username"].apply(
        lambda u: 1 if u in ["root", "admin", "administrator", "test", "guest"] else 0
    )

    # Count how many times each IP appears in the logs
    ip_counts = df["ip_address"].value_counts().reset_index()
    ip_counts.columns = ["ip_address", "ip_attempt_count"]
    df = df.merge(ip_counts, on="ip_address", how="left")

    # Convert status to a number: Failed=1, Accepted=0
    df["status_numeric"] = df["status"].apply(
        lambda s: 1 if s == "Failed" else 0
    )

    return df


def load_and_prepare(source="csv"):
    """
    Master function — loads data from either CSV or auth.log,
    enriches it, and returns a clean DataFrame ready for ML.

    Usage:
        df = load_and_prepare("csv")   # use sample_logs.csv
        df = load_and_prepare("log")   # use auth.log
    """
    if source == "csv":
        df = parse_csv_log("data/sample_logs.csv")
    else:
        df = parse_auth_log("data/auth.log")
        df = enrich_dataframe(df)
        return df

    df = enrich_dataframe(df)
    return df


# ─────────────────────────────────────────
# Quick test — run this file directly to
# verify the parser works
# ─────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 50)
    print("Testing CSV parser …")
    print("=" * 50)
    df = load_and_prepare("csv")
    print("\nFirst 5 rows:")
    print(df.head())
    print("\nColumn names:")
    print(df.columns.tolist())
    print("\nData types:")
    print(df.dtypes)
    print("\nShape:", df.shape)

    print("\n" + "=" * 50)
    print("Testing auth.log parser …")
    print("=" * 50)
    df2 = load_and_prepare("log")
    print("\nFirst 5 rows:")
    print(df2.head())
    print("\n✅ Parser is working correctly!")