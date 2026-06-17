import os
import sys

print("Starting setup...")

# Create data folder if missing
os.makedirs("data", exist_ok=True)
os.makedirs("backend/models", exist_ok=True)

# Step 1: Generate logs
print("Generating sample logs...")
os.system(f"{sys.executable} data/generate_logs.py")

# Step 2: Train model
print("Training ML model...")
os.system(f"{sys.executable} ml/train_model.py")

# Step 3: Init database
print("Setting up database...")
from backend.utils.database import init_database, load_scored_logs_to_db
init_database()
load_scored_logs_to_db()

print("Setup complete!")