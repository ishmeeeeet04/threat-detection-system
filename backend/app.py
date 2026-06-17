from flask import Flask, jsonify
from flask_cors import CORS
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def create_app():
    """Create and configure the Flask application."""

    app = Flask(__name__)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    from backend.routes.api import api
    app.register_blueprint(api, url_prefix="/api")

    @app.route("/")
    def home():
        return jsonify({
            "message"  : "🛡️ AI Threat Detection API is running",
            "version"  : "1.0.0",
            "endpoints": [
                "GET  /api/logs",
                "GET  /api/alerts",
                "GET  /api/stats",
                "GET  /api/threats/timeline",
                "GET  /api/threats/top-ips",
                "POST /api/analyse",
                "POST /api/reload"
            ]
        })

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"success": False, "error": "Endpoint not found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"success": False, "error": "Internal server error"}), 500

    return app


def setup():
    """Run setup — generate data, train model, init database."""
    print("🔄 Running setup …")

    # Generate sample logs if they don't exist
    if not os.path.exists("data/sample_logs.csv"):
        print("📊 Generating sample log data …")
        import subprocess
        subprocess.run([sys.executable, "data/generate_logs.py"], check=True)

    # Train model if it doesn't exist
    if not os.path.exists("backend/models/isolation_forest.pkl"):
        print("🤖 Training ML model …")
        import subprocess
        subprocess.run([sys.executable, "ml/train_model.py"], check=True)

    # Init database and load data
    print("📦 Setting up database …")
    from backend.utils.database import init_database, load_scored_logs_to_db
    init_database()
    load_scored_logs_to_db()

    print("✅ Setup complete!")


if __name__ == "__main__":
    print("🛡️  AI Threat Detection System — Starting up …\n")

    setup()

    print("\n🤖 Loading ML model …")
    from ml.detector import detector
    detector.load_model()

    print("\n🚀 Starting Flask server …")
    print("   URL: http://127.0.0.1:5000")
    print("   Press Ctrl+C to stop\n")

    app = create_app()
    app.run(
        host        = "0.0.0.0",
        port        = 5000,
        debug       = True,
        use_reloader= False
    )