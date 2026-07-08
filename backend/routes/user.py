import os
import tempfile
import threading
import uuid

from flask import Blueprint, jsonify, g

from backend.auth_middleware import require_auth
from backend.db import portrait_generation as generations_db
from backend.db import credits as credits_db
from backend.firebase import get_db
from backend.job_store import job_store
from backend.services.generation import run_job_background
from backend.services.prompt_builder import load_style, load_template
from backend.storage import public_url
from backend.storage.r2 import delete_object, download_object

user_bp = Blueprint("user", __name__, url_prefix="/user")


def _display_url(data: dict) -> str | None:
    """Public (watermarked) image URL for a generation, with legacy fallback.

    New generations expose only the watermarked ``preview_r2_key``. Legacy
    generations (pre-paywall) fall back to their old compressed/full public key.
    """
    if data.get("preview_r2_key"):
        return public_url(data["preview_r2_key"])
    if data.get("compressed_r2_key"):
        return public_url(data["compressed_r2_key"])
    if data.get("r2_key"):
        return public_url(data["r2_key"])
    return None


def _is_unlocked(data: dict) -> bool:
    """Legacy generations (no hd_r2_key) predate the paywall and are treated as unlocked."""
    if "hd_r2_key" not in data:
        return True
    return bool(data.get("unlocked"))


def _gen_r2_keys(data: dict) -> list[str]:
    """All R2 object keys owned by a generation doc (new schema + legacy)."""
    keys = []
    for field in ("hd_r2_key", "preview_r2_key", "source_r2_key", "compressed_r2_key"):
        if data.get(field):
            keys.append(data[field])
    if data.get("r2_key"):
        keys += [data["r2_key"], _fixed_key(data["r2_key"])]
    return keys


@user_bp.get("/generations")
@require_auth
def get_generations():
    """Return the authenticated user's generation history (watermarked previews only)."""
    docs = generations_db.get_by_uid(g.uid)

    results = []
    for doc in docs:
        data = doc.to_dict()
        ts = data.get("created_at")
        source_r2_key = data.get("source_r2_key")
        results.append({
            "job_id": doc.id,
            "template_key": data.get("template_key"),
            "style_key": data.get("style_key"),
            "positive_prompt": data.get("positive_prompt"),
            "seed": data.get("seed"),
            "presigned_url": _display_url(data),
            "unlocked": _is_unlocked(data),
            "source_url": public_url(source_r2_key) if source_r2_key else None,
            "orientation": data.get("orientation", "portrait"),
            "created_at": ts.isoformat() if ts else None,
        })

    results.sort(key=lambda x: x["created_at"] or "", reverse=True)
    return jsonify({"generations": results})


@user_bp.post("/generations/<job_id>/unlock")
@require_auth
def unlock_generation(job_id: str):
    """Spend 1 credit to unlock the HD download of a portrait. Idempotent."""
    try:
        result = credits_db.spend_credit_to_unlock(g.uid, job_id)
    except credits_db.NotFound:
        return jsonify({"error": "Not found"}), 404
    except credits_db.Forbidden:
        return jsonify({"error": "Forbidden"}), 403
    except credits_db.InsufficientCredits:
        return jsonify({"error": "Insufficient credits", "code": "insufficient_credits"}), 402

    doc = get_db().collection("generations").document(job_id).get()
    hd_key = doc.to_dict().get("hd_r2_key") if doc.exists else None
    return jsonify({
        "unlocked": True,
        "credits_remaining": result["credits_remaining"],
        "download_url": public_url(hd_key) if hd_key else None,
    })


@user_bp.get("/generations/<job_id>/download")
@require_auth
def download_generation(job_id: str):
    """Return the HD download URL — only if the caller owns and has unlocked it."""
    doc = get_db().collection("generations").document(job_id).get()
    if not doc.exists:
        return jsonify({"error": "Not found"}), 404
    data = doc.to_dict()
    if data.get("uid") != g.uid:
        return jsonify({"error": "Forbidden"}), 403
    if not _is_unlocked(data):
        return jsonify({"error": "Locked", "code": "locked"}), 402

    # Legacy generations may not have a private HD key; fall back to their old key.
    hd_key = data.get("hd_r2_key") or data.get("r2_key")
    if not hd_key:
        return jsonify({"error": "No HD file available"}), 404
    return jsonify({"download_url": public_url(hd_key)})


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
    for key in _gen_r2_keys(data):
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
    orientation = data.get("orientation", "portrait")
    width, height = (1040, 832) if orientation == "landscape" else (832, 1040)

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
        args=(new_job_id, tmp_path, style, style_key, template_key, {"width": width, "height": height}),
        kwargs={"uid": g.uid, "source_r2_key": new_source_r2_key, "orientation": orientation},
        daemon=True,
    ).start()

    # Delete old generation from R2 + Firestore after new job is queued
    # (keep the source image — the new job reuses it above).
    for key in _gen_r2_keys(data):
        if key == source_r2_key:
            continue
        try:
            delete_object(key)
        except Exception:
            pass
    generations_db.delete(job_id)

    return jsonify({"job_id": new_job_id}), 202


def _fixed_key(key: str) -> str:
    base, ext = os.path.splitext(key)
    return f"{base}_fixed{ext}"
