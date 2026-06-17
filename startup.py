"""
This file runs before gunicorn starts on Render.
It generates data, trains the model, and sets up the database.
"""
import os
import sys

print("🚀 Running startup script …")

# Step 1: Generate logs if missing
if not os.path.exists("data/sample_logs.csv"):
    print("📊 Generating sample data …")
    exec(open("data/generate_logs.py").read())

# Step 2: Train model if missing
if not os.path.exists("backend/models/isolation_forest.pkl"):
    print("🤖 Training model …")
    os.system(f"{sys.executable} ml/train_model.py")

# Step 3: Setup database
print("📦 Setting up database …")
from backend.utils.database import init_database, load_scored_logs_to_db
init_database()
load_scored_logs_to_db()

print("✅ Startup complete!")