import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, jsonify
from flask_cors import CORS


def create_app():
    app = Flask(__name__)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    from backend.routes.api import api
    app.register_blueprint(api, url_prefix="/api")

    @app.route("/")
    def home():
        return jsonify({
            "message": "AI Threat Detection API is running",
            "status" : "online",
            "endpoints": [
                "GET  /api/logs",
                "GET  /api/alerts",
                "GET  /api/stats",
                "GET  /api/threats/timeline",
                "GET  /api/threats/top-ips",
                "POST /api/analyse"
            ]
        })

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"success": False, "error": "Endpoint not found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"success": False, "error": str(e)}), 500

    return app


if __name__ == "__main__":
    # Run setup
    os.makedirs("data", exist_ok=True)
    os.makedirs("backend/models", exist_ok=True)

    if not os.path.exists("data/sample_logs.csv"):
        os.system(f"{sys.executable} data/generate_logs.py")

    if not os.path.exists("backend/models/isolation_forest.pkl"):
        os.system(f"{sys.executable} ml/train_model.py")

    from backend.utils.database import init_database, load_scored_logs_to_db
    init_database()
    load_scored_logs_to_db()

    from ml.detector import detector
    detector.load_model()

    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)