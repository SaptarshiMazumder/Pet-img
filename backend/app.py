import mimetypes
import sys
from pathlib import Path

# Ensure the project root is on sys.path so `backend` is importable as a package
sys.path.insert(0, str(Path(__file__).parent.parent))

mimetypes.add_type("image/svg+xml", ".svg")

from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from backend.routes.catalog import catalog_bp
from backend.routes.generation import generation_bp
from backend.routes.print_orders import print_orders_bp
from backend.routes.user import user_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB
    CORS(app)
    app.register_blueprint(catalog_bp)
    app.register_blueprint(generation_bp)
    app.register_blueprint(print_orders_bp)
    app.register_blueprint(user_bp)
    return app


app = create_app()


def _startup_recovery():
    try:
        from backend.worker import recover_active_jobs
        recover_active_jobs()
    except Exception as exc:
        print(f"[startup] recovery failed: {exc}")


import threading as _threading
_threading.Thread(target=_startup_recovery, daemon=True).start()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
