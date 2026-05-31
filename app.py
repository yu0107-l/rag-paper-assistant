from flask import Flask
from flask_cors import CORS

from api.routes import bp as api_bp


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app)

    app.register_blueprint(api_bp, url_prefix="/api")

    @app.get("/")
    def index():
        return {
            "name": "RAG Paper Assistant",
            "status": "running",
            "docs": {
                "health": "/api/health",
                "upload": "POST /api/papers/upload",
                "ask": "POST /api/papers/ask",
            },
        }

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
