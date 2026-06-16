import pandas as pd
import numpy as np

def engineer_features(df):
    """
    Convert raw log DataFrame into numerical features
    that the Isolation Forest model can understand.

    Input  : enriched DataFrame from log_parser.py
    Output : DataFrame with only numerical feature columns
    """

    features = pd.DataFrame()

    # ── Feature 1: Number of failed attempts ──────────────────
    # High number = very suspicious (brute force attack)
    features["failed_attempts"] = df["failed_attempts"].fillna(0)

    # ── Feature 2: Login hour ─────────────────────────────────
    # Logins at 2am are more suspicious than logins at 10am
    features["hour"] = df["hour"].fillna(12)

    # ── Feature 3: Is it a night hour? ───────────────────────
    # Binary flag: 1 = midnight to 5am, 0 = normal hours
    features["is_night_hour"] = df["is_night_hour"].fillna(0)

    # ── Feature 4: Is the target a root/admin account? ───────
    # Attackers almost always target root and admin first
    features["is_root_attempt"] = df["is_root_attempt"].fillna(0)

    # ── Feature 5: How many times has this IP appeared? ──────
    # An IP that appears 200 times is more suspicious than one
    # that appears twice
    features["ip_attempt_count"] = df["ip_attempt_count"].fillna(1)

    # ── Feature 6: Did this login fail? ──────────────────────
    # 1 = Failed, 0 = Accepted
    features["status_numeric"] = df["status_numeric"].fillna(0)

    # ── Feature 7: Port number ────────────────────────────────
    # Attackers almost always use port 22 (SSH)
    # Normal users may use various ports
    features["port"] = df["port"].fillna(22)
    features["is_ssh_port"] = (features["port"] == 22).astype(int)

    # ── Feature 8: Failed attempt rate per IP ────────────────
    # failed_attempts divided by total IP appearances
    # High rate = strong brute force signal
    features["fail_rate"] = (
        features["failed_attempts"] /
        features["ip_attempt_count"].replace(0, 1)
    ).fillna(0)

    # ── Feature 9: Suspicious combination score ───────────────
    # If MULTIPLE suspicious things are true at once,
    # that is much more dangerous than just one
    features["combo_score"] = (
        features["is_night_hour"] +
        features["is_root_attempt"] +
        features["status_numeric"] +
        features["is_ssh_port"]
    )

    print(f"✅ Feature engineering complete — {features.shape[1]} features created")
    print(f"   Feature columns: {features.columns.tolist()}")

    return features


def get_feature_names():
    """Returns the list of feature column names — used when loading model later."""
    return [
        "failed_attempts",
        "hour",
        "is_night_hour",
        "is_root_attempt",
        "ip_attempt_count",
        "status_numeric",
        "port",
        "is_ssh_port",
        "fail_rate",
        "combo_score"
    ]