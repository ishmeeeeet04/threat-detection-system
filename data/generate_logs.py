import random
import pandas as pd
from faker import Faker
from datetime import datetime, timedelta

fake = Faker()

# ─────────────────────────────────────────
# Settings
# ─────────────────────────────────────────
TOTAL_ENTRIES = 1000
OUTPUT_CSV    = "data/sample_logs.csv"
OUTPUT_LOG    = "data/auth.log"

# Normal office hours: 8am–6pm
NORMAL_HOURS  = list(range(8, 19))
# Suspicious hours: midnight–5am
SUSPICIOUS_HOURS = list(range(0, 5))

# A small pool of "trusted" IPs (normal users)
TRUSTED_IPS = [fake.ipv4_private() for _ in range(10)]

# A small pool of "attacker" IPs
ATTACKER_IPS = [fake.ipv4_public() for _ in range(5)]

# Normal usernames
NORMAL_USERS = ["alice", "bob", "charlie", "diana", "eve",
                "frank", "grace", "henry", "iris", "jack"]

# Attacker favourite targets
TARGET_USERS = ["root", "admin", "administrator", "test", "guest"]

def random_timestamp(suspicious=False):
    """Generate a random timestamp — suspicious ones happen at night."""
    base = datetime.now() - timedelta(days=random.randint(0, 30))
    if suspicious:
        hour = random.choice(SUSPICIOUS_HOURS)
    else:
        hour = random.choice(NORMAL_HOURS)
    return base.replace(
        hour=hour,
        minute=random.randint(0, 59),
        second=random.randint(0, 59),
        microsecond=0
    )

def generate_normal_entry():
    """A regular employee logging in successfully."""
    ts       = random_timestamp(suspicious=False)
    ip       = random.choice(TRUSTED_IPS)
    user     = random.choice(NORMAL_USERS)
    status   = "Accepted" if random.random() > 0.1 else "Failed"
    attempts = 1 if status == "Accepted" else random.randint(1, 3)
    port     = random.randint(1024, 65535)
    return {
        "timestamp"     : ts.strftime("%Y-%m-%d %H:%M:%S"),
        "ip_address"    : ip,
        "username"      : user,
        "status"        : status,
        "failed_attempts": attempts,
        "port"          : port,
        "hour"          : ts.hour,
        "is_suspicious" : 0        # label for reference (not used in training)
    }

def generate_suspicious_entry(attack_type="brute_force"):
    """A suspicious/attack entry."""
    ts   = random_timestamp(suspicious=True)
    ip   = random.choice(ATTACKER_IPS)
    user = random.choice(TARGET_USERS)
    port = 22  # attackers almost always target SSH port 22

    if attack_type == "brute_force":
        # Many failed attempts from same IP
        status   = "Failed"
        attempts = random.randint(10, 50)

    elif attack_type == "unusual_ip":
        # Successful login but from a foreign/unknown IP
        status   = "Accepted"
        attempts = 1
        ip       = fake.ipv4_public()   # completely random public IP

    elif attack_type == "suspicious_time":
        # Login at 3am — could be normal but worth flagging
        status   = random.choice(["Accepted", "Failed"])
        attempts = random.randint(1, 5)

    else:
        status   = "Failed"
        attempts = random.randint(5, 20)

    return {
        "timestamp"      : ts.strftime("%Y-%m-%d %H:%M:%S"),
        "ip_address"     : ip,
        "username"       : user,
        "status"         : status,
        "failed_attempts": attempts,
        "port"           : port,
        "hour"           : ts.hour,
        "is_suspicious"  : 1
    }

def generate_dataset():
    entries = []

    # 75% normal traffic
    for _ in range(750):
        entries.append(generate_normal_entry())

    # 25% suspicious — mix of attack types
    attack_types = ["brute_force", "unusual_ip", "suspicious_time", "other"]
    for _ in range(250):
        entries.append(generate_suspicious_entry(
            random.choice(attack_types)
        ))

    # Shuffle so attacks are not all at the end
    random.shuffle(entries)
    return entries

def save_csv(entries):
    df = pd.DataFrame(entries)
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"✅ CSV saved  → {OUTPUT_CSV}  ({len(df)} rows)")
    return df

def save_auth_log(entries):
    """Write entries in classic Linux auth.log format."""
    lines = []
    for e in entries:
        ts   = e["timestamp"]
        ip   = e["ip_address"]
        user = e["username"]
        port = e["port"]

        if e["status"] == "Failed":
            line = (f"{ts} server sshd[{random.randint(1000,9999)}]: "
                    f"Failed password for {user} from {ip} port {port} ssh2")
        else:
            line = (f"{ts} server sshd[{random.randint(1000,9999)}]: "
                    f"Accepted password for {user} from {ip} port {port} ssh2")
        lines.append(line)

    with open(OUTPUT_LOG, "w") as f:
        f.write("\n".join(lines))
    print(f"✅ Auth log saved → {OUTPUT_LOG}  ({len(lines)} lines)")

if __name__ == "__main__":
    print("🔄 Generating log data …")
    entries = generate_dataset()
    df      = save_csv(entries)
    save_auth_log(entries)

    print("\n📊 Quick summary:")
    print(f"   Total entries : {len(df)}")
    print(f"   Normal        : {(df['is_suspicious']==0).sum()}")
    print(f"   Suspicious    : {(df['is_suspicious']==1).sum()}")
    print(f"   Failed logins : {(df['status']=='Failed').sum()}")
    print(f"   Accepted      : {(df['status']=='Accepted').sum()}")
    print("\n✅ Done! Check the data/ folder.")