import sys
import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

# Add project root to path so we can import our own modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.utils.log_parser import load_and_prepare
from backend.utils.features import engineer_features, get_feature_names
from ml.threat_scorer import score_dataframe

# ── Where to save the trained model ───────────────────────────
MODEL_PATH  = "backend/models/isolation_forest.pkl"
SCALER_PATH = "backend/models/scaler.pkl"


def train(source="csv"):
    """
    Full training pipeline:
    1. Load and parse log data
    2. Engineer features
    3. Scale features
    4. Train Isolation Forest
    5. Score all entries
    6. Save model and scaler to disk
    7. Print evaluation summary
    """

    print("=" * 55)
    print("  🤖 AI Threat Detection — Model Training Pipeline")
    print("=" * 55)

    # ── Step 1: Load data ──────────────────────────────────────
    print("\n📂 Step 1: Loading log data …")
    df = load_and_prepare(source)
    print(f"   Loaded {len(df)} log entries")

    # ── Step 2: Engineer features ─────────────────────────────
    print("\n🔧 Step 2: Engineering features …")
    X = engineer_features(df)
    print(f"   Feature matrix shape: {X.shape}")

    # ── Step 3: Scale features ────────────────────────────────
    # Scaling makes all features have similar ranges
    # This helps the model treat all features fairly
    print("\n📏 Step 3: Scaling features …")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    print("   Features scaled using StandardScaler")

    # ── Step 4: Train the model ───────────────────────────────
    print("\n🌲 Step 4: Training Isolation Forest …")
    print("   contamination=0.25 means we expect ~25% anomalies")
    model = IsolationForest(
        n_estimators=200,      # Number of trees — more = more accurate
        contamination=0.25,    # Expected % of anomalies in the data
        random_state=42,       # Makes results reproducible
        n_jobs=-1              # Use all CPU cores for speed
    )
    model.fit(X_scaled)
    print("   ✅ Model trained successfully!")

    # ── Step 5: Generate predictions ──────────────────────────
    print("\n🔍 Step 5: Generating predictions …")
    predictions    = model.predict(X_scaled)
    anomaly_scores = model.decision_function(X_scaled)

    # Isolation Forest returns: -1 = anomaly, 1 = normal
    n_anomalies = (predictions == -1).sum()
    n_normal    = (predictions == 1).sum()
    print(f"   Normal entries  : {n_normal}")
    print(f"   Anomalies found : {n_anomalies}")
    print(f"   Anomaly rate    : {n_anomalies/len(predictions)*100:.1f}%")

    # ── Step 6: Score all entries ─────────────────────────────
    print("\n🎯 Step 6: Calculating threat scores …")
    scored_df = score_dataframe(X, anomaly_scores)

    print("\n   Threat level distribution:")
    level_counts = scored_df["threat_level"].value_counts()
    for level, count in level_counts.items():
        bar = "█" * (count // 10)
        print(f"   {level:<10}: {count:>4}  {bar}")

    print(f"\n   Average threat score : {scored_df['threat_score'].mean():.1f}")
    print(f"   Max threat score     : {scored_df['threat_score'].max()}")
    print(f"   Min threat score     : {scored_df['threat_score'].min()}")

    # ── Step 7: Save model and scaler ─────────────────────────
    print("\n💾 Step 7: Saving model to disk …")
    os.makedirs("backend/models", exist_ok=True)
    joblib.dump(model,  MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)
    print(f"   Model  saved → {MODEL_PATH}")
    print(f"   Scaler saved → {SCALER_PATH}")

    # ── Step 8: Save scored results for the dashboard ─────────
    print("\n📊 Step 8: Saving scored results …")
    # Add original log data back for display
    df_original = df.copy()
    df_original["threat_score"] = scored_df["threat_score"].values
    df_original["threat_level"] = scored_df["threat_level"].values
    df_original["threat_color"] = scored_df["threat_color"].values
    df_original["is_anomaly"]   = (predictions == -1).astype(int)

    results_path = "data/scored_logs.csv"
    df_original.to_csv(results_path, index=False)
    print(f"   Scored logs saved → {results_path}")

    print("\n" + "=" * 55)
    print("  ✅ Training complete! Model is ready to use.")
    print("=" * 55)

    return model, scaler, df_original


if __name__ == "__main__":
    model, scaler, results = train(source="csv")

    print("\n🔎 Sample of HIGH and CRITICAL threats detected:")
    high_threats = results[
        results["threat_level"].isin(["HIGH", "CRITICAL"])
    ][["timestamp", "ip_address", "username",
       "status", "failed_attempts", "threat_score",
       "threat_level"]].head(10)

    print(high_threats.to_string(index=False))