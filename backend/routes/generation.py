import tempfile
import threading
import uuid
from pathlib import Path

from flask import Blueprint, jsonify, request

from backend.services.prompt_builder import load_style, load_template
from backend.job_store import job_store
from backend.services.generation import run_job_background, run_uso_job_background
from backend.auth_middleware import get_optional_uid
from backend.autoscaler_client import autoscaler
from backend.storage.r2 import upload_object

generation_bp = Blueprint("generation", __name__)

_OVERRIDE_FIELDS: list[tuple[str, type]] = [
    ("width", int), ("height", int), ("steps", int),
    ("cfg", float), ("seed", int), ("batch_size", int),
    ("lora_strength", float), ("lora2_strength", float),
    ("upscale_factor", float), ("upscale_steps", int),
    ("upscale_denoise", float),
]


@generation_bp.post("/warm")
def warm():
    """Called when a user visits the site — spins up a worker preemptively."""
    threading.Thread(target=autoscaler.warm, daemon=True).start()
    return jsonify({"ok": True}), 200


@generation_bp.post("/generate")
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

    try:
        style = load_style(style_key)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    try:
        load_template(template_key)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    dry_run = request.form.get("dry_run", "false").lower() == "true"
    orientation = request.form.get("orientation", "portrait")
    uid = get_optional_uid()

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

    # Upload source image to R2 asynchronously — used for regeneration later
    source_r2_key = f"sources/{job_id}{suffix}"
    def _upload_source():
        try:
            with open(tmp_path, "rb") as f:
                upload_object(source_r2_key, f.read(), content_type=f"image/{suffix.lstrip('.')}")
        except Exception as exc:
            print(f"[R2] Source upload failed for {job_id}: {exc}")
    threading.Thread(target=_upload_source, daemon=True).start()

    thread = threading.Thread(
        target=run_job_background,
        args=(job_id, tmp_path, style, style_key, template_key, overrides),
        kwargs={"dry_run": dry_run, "uid": uid, "source_r2_key": source_r2_key, "orientation": orientation},
        daemon=True,
    )
    thread.start()

    return jsonify({"job_id": job_id}), 202


_USO_OVERRIDE_FIELDS: list[tuple[str, type]] = [
    ("width", int), ("height", int), ("steps", int),
    ("cfg", float), ("seed", int), ("batch_size", int),
    ("guidance", float), ("lora_strength", float),
]


@generation_bp.post("/generate/uso")
def generate_uso():
    if "subject_image" not in request.files:
        return jsonify({"error": "subject_image is required."}), 400
    if "style_image" not in request.files:
        return jsonify({"error": "style_image is required."}), 400

    prompt = request.form.get("prompt", "").strip()
    if not prompt:
        return jsonify({"error": "prompt is required."}), 400

    subject = request.files["subject_image"]
    style = request.files["style_image"]

    for f in (subject, style):
        if Path(f.filename).suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
            return jsonify({"error": f"{f.filename}: must be PNG, JPG, or WEBP."}), 400

    overrides = {}
    for field, cast in _USO_OVERRIDE_FIELDS:
        val = request.form.get(field)
        if val is not None:
            try:
                overrides[field] = cast(val)
            except ValueError:
                return jsonify({"error": f"Invalid value for '{field}'."}), 400

    uid = get_optional_uid()
    job_id = str(uuid.uuid4())

    subject_suffix = Path(subject.filename).suffix.lower()
    style_suffix = Path(style.filename).suffix.lower()
    subject_r2_key = f"uso-inputs/{job_id}/subject{subject_suffix}"
    style_r2_key = f"uso-inputs/{job_id}/style{style_suffix}"

    subject_bytes = subject.read()
    style_bytes = style.read()

    try:
        upload_object(subject_r2_key, subject_bytes, content_type=f"image/{subject_suffix.lstrip('.')}")
        upload_object(style_r2_key, style_bytes, content_type=f"image/{style_suffix.lstrip('.')}")
    except Exception as exc:
        return jsonify({"error": f"Failed to upload images: {exc}"}), 500

    job_store.create(job_id)

    threading.Thread(
        target=run_uso_job_background,
        args=(job_id, subject_r2_key, style_r2_key, prompt),
        kwargs={"uid": uid, "overrides": overrides},
        daemon=True,
    ).start()

    return jsonify({"job_id": job_id}), 202


@generation_bp.get("/job/<job_id>")
def get_job(job_id: str):
    job = job_store.get(job_id)
    if job is None:
        return jsonify({"error": "Job not found."}), 404
    return jsonify(job)
