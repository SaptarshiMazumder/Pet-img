import json

from flask import Blueprint, jsonify, send_from_directory

from backend.config import STYLES_FILE, TEMPLATES_FILE, ASSETS_DIR

catalog_bp = Blueprint("catalog", __name__)


@catalog_bp.get("/styles")
def list_styles():
    styles = json.loads(STYLES_FILE.read_text(encoding="utf-8"))
    return jsonify({
        key: {"name": v["name"], "trigger_word": v["trigger_word"]}
        for key, v in styles.items()
    })


@catalog_bp.get("/templates")
def list_templates():
    templates = json.loads(TEMPLATES_FILE.read_text(encoding="utf-8"))
    return jsonify({
        key: {
            "name": v["name"],
            "preview_url": v.get("preview_url", ""),
            "mood": v.get("mood", ""),
            "environment": v["environment"][:80],
        }
        for key, v in templates.items()
    })


@catalog_bp.get("/assets/<path:path>")
def serve_assets(path):
    return send_from_directory(ASSETS_DIR, path)
