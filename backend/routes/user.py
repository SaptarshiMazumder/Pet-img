import os
import tempfile
import threading
import uuid

from flask import Blueprint, jsonify, g

from backend.auth_middleware import require_auth
from backend.db import portrait_generation as generations_db
from backend.firebase import get_db
from backend.job_store import job_store
from backend.services.generation import run_job_background
from backend.services.prompt_builder import load_style, load_template
from backend.storage import public_url
from backend.storage.r2 import delete_object, download_object

user_bp = Blueprint("user", __name__, url_prefix="/user")


@user_bp.get("/generations")
@require_auth
def get_generations():
    """Return the authenticated user's generation history with fresh presigned URLs."""
    docs = generations_db.get_by_uid(g.uid)

    results = []
    for doc in docs:
        data = doc.to_dict()
        r2_key = data.get("r2_key")
        compressed_r2_key = data.get("compressed_r2_key")
        ts = data.get("created_at")
        source_r2_key = data.get("source_r2_key")
        full_url = public_url(r2_key) if r2_key else None
        display_url = public_url(compressed_r2_key) if compressed_r2_key else full_url
        results.append({
            "job_id": doc.id,
            "template_key": data.get("template_key"),
            "style_key": data.get("style_key"),
            "positive_prompt": data.get("positive_prompt"),
            "seed": data.get("seed"),
            "r2_key": r2_key,
            "presigned_url": display_url,
            "source_url": public_url(source_r2_key) if source_r2_key else None,
            "orientation": data.get("orientation", "portrait"),
            "created_at": ts.isoformat() if ts else None,
        })

    results.sort(key=lambda x: x["created_at"] or "", reverse=True)
    return jsonify({"generations": results})


@user_bp.delete("/generations/<job_id>")
@require_auth
def delete_generation(job_id: str):
    """Delete a generation from Firestore and R2."""
    doc = get_db().collection("generations").document(job_id).get()
    if not doc.exists:
        return jsonify({"error": "Not found"}), 404
    if doc.to_dict().get("uid") != g.uid:
        return jsonify({"error": "Forbidden"}), 403

    data = doc.to_dict()
    keys_to_delete = []
    if data.get("r2_key"):
        keys_to_delete += [data["r2_key"], _fixed_key(data["r2_key"])]
    if data.get("source_r2_key"):
        keys_to_delete.append(data["source_r2_key"])
    if data.get("compressed_r2_key"):
        keys_to_delete.append(data["compressed_r2_key"])
    for key in keys_to_delete:
        try:
            delete_object(key)
        except Exception:
            pass

    generations_db.delete(job_id)
    return jsonify({"success": True})


@user_bp.post("/generations/<job_id>/regenerate")
@require_auth
def regenerate_generation(job_id: str):
    """Re-run a past generation using the stored source image and original parameters."""
    doc = get_db().collection("generations").document(job_id).get()
    if not doc.exists:
        return jsonify({"error": "Not found"}), 404

    data = doc.to_dict()
    if data.get("uid") != g.uid:
        return jsonify({"error": "Forbidden"}), 403

    source_r2_key = data.get("source_r2_key")
    if not source_r2_key:
        return jsonify({"error": "No source image stored for this generation. Please use the Create page to regenerate."}), 422

    template_key = data.get("template_key")
    style_key = data.get("style_key", "inkwash")

    try:
        style = load_style(style_key)
        load_template(template_key)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    # Download source image from R2 into a temp file
    try:
        image_bytes = download_object(source_r2_key)
    except Exception as e:
        return jsonify({"error": f"Could not retrieve source image: {e}"}), 500

    suffix = os.path.splitext(source_r2_key)[1] or ".jpg"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(image_bytes)
        tmp_path = tmp.name

    new_job_id = str(uuid.uuid4())
    job_store.create(new_job_id)

    # Upload source for the new job too
    new_source_r2_key = f"sources/{new_job_id}{suffix}"
    def _upload_source():
        try:
            from backend.storage.r2 import upload_object
            upload_object(new_source_r2_key, image_bytes, content_type=f"image/{suffix.lstrip('.')}")
        except Exception as exc:
            print(f"[R2] Source upload failed for {new_job_id}: {exc}")
    threading.Thread(target=_upload_source, daemon=True).start()

    threading.Thread(
        target=run_job_background,
        args=(new_job_id, tmp_path, style, style_key, template_key, {}),
        kwargs={"uid": g.uid, "source_r2_key": new_source_r2_key},
        daemon=True,
    ).start()

    # Delete old generation from R2 + Firestore after new job is queued
    keys_to_delete = []
    if data.get("r2_key"):
        keys_to_delete += [data["r2_key"], _fixed_key(data["r2_key"])]
    if data.get("compressed_r2_key"):
        keys_to_delete.append(data["compressed_r2_key"])
    for key in keys_to_delete:
        try:
            delete_object(key)
        except Exception:
            pass
    generations_db.delete(job_id)

    return jsonify({"job_id": new_job_id}), 202


def _fixed_key(key: str) -> str:
    base, ext = os.path.splitext(key)
    return f"{base}_fixed{ext}"
