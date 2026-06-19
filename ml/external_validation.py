"""
External validation against NSL-KDD, a public, peer-reviewed intrusion
detection benchmark. This is a SEPARATE experiment from the main project
pipeline, run on a different dataset with a different feature schema,
specifically to check whether Isolation Forest as a general technique
generalizes beyond this project's own synthetic data.
"""
import os
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import precision_score, recall_score, f1_score

# NSL-KDD ships with no header row, so we name the columns ourselves.
# The last two columns are the attack-type label and a "difficulty" score.
COLUMNS = [
    "duration","protocol_type","service","flag","src_bytes","dst_bytes","land",
    "wrong_fragment","urgent","hot","num_failed_logins","logged_in","num_compromised",
    "root_shell","su_attempted","num_root","num_file_creations","num_shells",
    "num_access_files","num_outbound_cmds","is_host_login","is_guest_login","count",
    "srv_count","serror_rate","srv_serror_rate","rerror_rate","srv_rerror_rate",
    "same_srv_rate","diff_srv_rate","srv_diff_host_rate","dst_host_count",
    "dst_host_srv_count","dst_host_same_srv_rate","dst_host_diff_srv_rate",
    "dst_host_same_src_port_rate","dst_host_srv_diff_host_rate","dst_host_serror_rate",
    "dst_host_srv_serror_rate","dst_host_rerror_rate","dst_host_srv_rerror_rate",
    "label","difficulty"
]

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(SCRIPT_DIR, "..", "nsl-kdd-data", "KDDTrain+_20Percent.txt")

df = pd.read_csv(DATA_PATH, names=COLUMNS)
df["is_attack"] = (df["label"] != "normal").astype(int)

# Keep only numeric features, drop label/difficulty/text columns for this
# simple comparison (protocol_type/service/flag are categorical strings).
numeric_cols = df.select_dtypes(include="number").columns.tolist()
numeric_cols = [c for c in numeric_cols if c not in ("difficulty", "is_attack")]

X = StandardScaler().fit_transform(df[numeric_cols])
y = df["is_attack"]

print(f"Total records: {len(df)}")
print(f"Actual attack ratio in this dataset: {y.mean():.3f}\n")

# Experiment 1: contamination="auto" — what you'd realistically use
# when you DON'T know the true attack ratio in advance, which is the
# honest, real-world situation.
model_auto = IsolationForest(contamination="auto", random_state=42, n_estimators=100)
pred_auto = (model_auto.fit_predict(X) == -1).astype(int)

print("=== contamination='auto' (no cheating, realistic) ===")
print(f"Precision: {precision_score(y, pred_auto):.3f}")
print(f"Recall:    {recall_score(y, pred_auto):.3f}")
print(f"F1:        {f1_score(y, pred_auto):.3f}\n")

# Experiment 2: contamination set to the TRUE known ratio — only possible
# because this is a labeled benchmark. This mirrors exactly what this
# project's main pipeline does with its synthetic data, and shows directly
# why that's an unrealistic assumption in production.
model_cheat = IsolationForest(contamination=y.mean(), random_state=42, n_estimators=100)
pred_cheat = (model_cheat.fit_predict(X) == -1).astype(int)

print("=== contamination=true_ratio (only possible because we have labels) ===")
print(f"Precision: {precision_score(y, pred_cheat):.3f}")
print(f"Recall:    {recall_score(y, pred_cheat):.3f}")
print(f"F1:        {f1_score(y, pred_cheat):.3f}")