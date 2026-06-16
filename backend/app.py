from flask import Flask, jsonify
from flask_cors import CORS
import sys
import os

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.routes.api import api
from backend.utils.database import init_database, load_scored_logs_to_db


def create_app():
    """Create and configure the Flask application."""

    app = Flask(__name__)

    # CORS allows our frontend HTML file to call this API
    # Without this, the browser would block the requests
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Register our API routes under the /api prefix
    app.register_blueprint(api, url_prefix="/api")

    # ── Health check endpoint ──────────────────────────────────
    @app.route("/")
    def home():
        return jsonify({
            "message": "🛡️ AI Threat Detection API is running",
            "version": "1.0.0",
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


if __name__ == "__main__":
    print("🛡️  AI Threat Detection System — Starting up …\n")

    # Step 1: Initialise database tables
    print("📦 Initialising database …")
    init_database()

    # Step 2: Load scored logs into database
    print("📂 Loading scored logs …")
    count = load_scored_logs_to_db()

    if count == 0:
        print("\n⚠️  No data loaded. Make sure you have run:")
        print("   python ml/train_model.py")
    else:
        print(f"   ✅ {count} log entries loaded")

    # Step 3: Load ML model
    print("\n🤖 Loading ML model …")
    from ml.detector import detector
    detector.load_model()

    # Step 4: Start the server
    print("\n🚀 Starting Flask server …")
    print("   URL: http://127.0.0.1:5000")
    print("   Press Ctrl+C to stop\n")

    app = create_app()
    app.run(
        host="0.0.0.0",
        port=5001,
        debug=True,     # Auto-restarts when you change code
        use_reloader=False  # Prevents double model loading in debug mode
    )