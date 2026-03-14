"""Sample image upload and management routes."""
import uuid
from pathlib import Path

from flask import Blueprint, jsonify, request, g

from backend.auth_middleware import require_auth
from backend.storage.r2 import upload_object, generate_presigned_url
from backend.db import samples as samples_db

samples_bp = Blueprint("samples", __name__)

_ALLOWED_EXT = {".png", ".jpg", ".jpeg", ".webp"}


@samples_bp.post("/samples")
@require_auth
def upload_sample():
    if "image" not in request.files:
        return jsonify({"error": "No image provided"}), 400

    img = request.files["image"]
    suffix = Path(img.filename or "").suffix.lower()
    if suffix not in _ALLOWED_EXT:
        return jsonify({"error": "PNG, JPG or WEBP only"}), 400

    sample_id = str(uuid.uuid4())
    ext = "jpeg" if suffix in (".jpg", ".jpeg") else suffix.lstrip(".")
    r2_key = f"samples/{sample_id}.{ext}"

    upload_object(r2_key, img.read(), content_type=f"image/{ext}")
    samples_db.save(sample_id, r2_key, g.uid)

    return jsonify({"sample_id": sample_id, "r2_key": r2_key}), 201


@samples_bp.get("/samples")
@require_auth
def list_samples():
    result = []
    for doc in samples_db.list_all():
        d = doc.to_dict()
        try:
            url = generate_presigned_url(d["r2_key"], expires=3600)
        except Exception:
            url = None
        created = d.get("created_at")
        result.append({
            "sample_id": doc.id,
            "r2_key": d["r2_key"],
            "presigned_url": url,
            "created_at": created.isoformat() if created else None,
        })
    return jsonify(result)


@samples_bp.delete("/samples/<sample_id>")
@require_auth
def delete_sample(sample_id: str):
    samples_db.delete(sample_id)
    return jsonify({"ok": True})
