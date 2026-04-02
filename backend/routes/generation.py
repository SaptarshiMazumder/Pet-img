import os
import tempfile
import threading
import uuid
from pathlib import Path

from flask import Blueprint, g, jsonify, request

from backend.services.prompt_builder import load_style, load_uso_template
from backend.services.workflows import get_workflow
from backend.job_store import job_store
from backend.services.generation import run_workflow_background
from backend.auth_middleware import require_auth
from backend.autoscaler_client import autoscaler
from backend.storage.r2 import upload_object
from backend.db import user_credits

generation_bp = Blueprint("generation", __name__)

_OVERRIDE_FIELDS: list[tuple[str, type]] = [
    ("width", int), ("height", int), ("steps", int),
    ("cfg", float), ("seed", int), ("batch_size", int),
    ("lora_strength", float), ("lora2_strength", float),
    ("upscale_factor", float), ("upscale_steps", int),
    ("upscale_denoise", float),
]

_USO_OVERRIDE_FIELDS: list[tuple[str, type]] = [
    ("width", int), ("height", int), ("steps", int),
    ("cfg", float), ("seed", int), ("batch_size", int),
    ("guidance", float), ("lora_strength", float),
]


@generation_bp.post("/warm")
def warm():
    """Called when a user visits the site — spins up a worker preemptively."""
    threading.Thread(target=autoscaler.warm, daemon=True).start()
    return jsonify({"ok": True}), 200


@generation_bp.post("/generate")
@require_auth
def generate():
    if "image" not in request.files:
        return jsonify({"error": "No image file provided."}), 400

    image = request.files["image"]
    suffix = Path(image.filename).suffix.lower()
    if suffix not in {".png", ".jpg", ".jpeg", ".webp"}:
        return jsonify({"error": "Image must be PNG, JPG, or WEBP."}), 400

    template_key = request.form.get("template_key")
    if not template_key:
        return jsonify({"error": "template_key is required."}), 400

    style_key = request.form.get("style_key", "inkwash")

    workflow = get_workflow("zturbo")
    try:
        workflow.load_template(template_key)
        load_style(style_key)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    dry_run = request.form.get("dry_run", "false").lower() == "true"
    orientation = request.form.get("orientation", "portrait")
    uid = g.uid

    try:
        credits_remaining = user_credits.deduct_one_credit(uid)
    except ValueError:
        return jsonify({"error": "No credits remaining. Please recharge to continue.", "code": "insufficient_credits"}), 402

    overrides = {}
    for field, cast in _OVERRIDE_FIELDS:
        val = request.form.get(field)
        if val is not None:
            try:
                overrides[field] = cast(val)
            except ValueError:
                return jsonify({"error": f"Invalid value for '{field}'."}), 400

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        image.save(tmp)
        tmp_path = tmp.name

    job_id = str(uuid.uuid4())
    job_store.create(job_id)

    source_r2_key = f"sources/{job_id}{suffix}"

    def _upload_source():
        try:
            with open(tmp_path, "rb") as f:
                upload_object(source_r2_key, f.read(), content_type=f"image/{suffix.lstrip('.')}")
        except Exception as exc:
            print(f"[R2] Source upload failed for {job_id}: {exc}")
    threading.Thread(target=_upload_source, daemon=True).start()

    threading.Thread(
        target=run_workflow_background,
        args=(job_id, workflow, template_key),
        kwargs={
            "uid": uid,
            "source_r2_key": source_r2_key,
            "orientation": orientation,
            "dry_run": dry_run,
            "cleanup": lambda: Path(tmp_path).unlink(missing_ok=True),
            "image_path": tmp_path,
            "style_key": style_key,
            "overrides": overrides,
        },
        daemon=True,
    ).start()

    return jsonify({"job_id": job_id, "credits_remaining": credits_remaining}), 202


@generation_bp.post("/generate/uso")
@require_auth
def generate_uso():
    if "subject_image" not in request.files:
        return jsonify({"error": "subject_image is required."}), 400

    template_key = request.form.get("template_key")
    if not template_key:
        return jsonify({"error": "template_key is required."}), 400

    try:
        load_uso_template(template_key)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    subject = request.files["subject_image"]
    if Path(subject.filename).suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
        return jsonify({"error": f"{subject.filename}: must be PNG, JPG, or WEBP."}), 400

    overrides = {}
    for field, cast in _USO_OVERRIDE_FIELDS:
        val = request.form.get(field)
        if val is not None:
            try:
                overrides[field] = cast(val)
            except ValueError:
                return jsonify({"error": f"Invalid value for '{field}'."}), 400

    uid = g.uid

    try:
        credits_remaining = user_credits.deduct_one_credit(uid)
    except ValueError:
        return jsonify({"error": "No credits remaining. Please recharge to continue.", "code": "insufficient_credits"}), 402

    job_id = str(uuid.uuid4())

    subject_suffix = Path(subject.filename).suffix.lower()
    subject_r2_key = f"uso-inputs/{job_id}/subject{subject_suffix}"
    style_r2_key = "uso_styles/oilPainting.jpg"

    subject_bytes = subject.read()

    try:
        upload_object(subject_r2_key, subject_bytes, content_type=f"image/{subject_suffix.lstrip('.')}")
    except Exception as exc:
        return jsonify({"error": f"Failed to upload image: {exc}"}), 500

    # Write subject to temp file — Gemini needs a file path for animal analysis
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix=subject_suffix) as tmp:
        tmp.write(subject_bytes)
        subject_tmp_path = tmp.name

    r2_public_base = os.environ.get("R2_PUBLIC_BASE_URL", "").rstrip("/")
    subject_url = f"{r2_public_base}/{subject_r2_key}"
    style_url = f"{r2_public_base}/{style_r2_key}"

    workflow = get_workflow("uso")
    job_store.create(job_id)

    orientation = request.form.get("orientation", "portrait")

    threading.Thread(
        target=run_workflow_background,
        args=(job_id, workflow, template_key),
        kwargs={
            "uid": uid,
            "source_r2_key": subject_r2_key,
            "uso_style_r2_key": style_r2_key,
            "orientation": orientation,
            "cleanup": lambda: Path(subject_tmp_path).unlink(missing_ok=True),
            "subject_url": subject_url,
            "subject_image_path": subject_tmp_path,
            "style_url": style_url,
            "overrides": overrides,
        },
        daemon=True,
    ).start()

    return jsonify({"job_id": job_id, "credits_remaining": credits_remaining}), 202


@generation_bp.get("/job/<job_id>")
def get_job(job_id: str):
    job = job_store.get(job_id)
    if job is None:
        return jsonify({"error": "Job not found."}), 404
    return jsonify(job)
