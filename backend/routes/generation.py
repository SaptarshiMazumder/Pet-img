import tempfile
import threading
import uuid
from pathlib import Path

from flask import Blueprint, jsonify, request

from prompt_generator import load_style, load_template
from backend.job_store import job_store
from backend.worker import run_job_background

generation_bp = Blueprint("generation", __name__)

_OVERRIDE_FIELDS: list[tuple[str, type]] = [
    ("width", int), ("height", int), ("steps", int),
    ("cfg", float), ("seed", int), ("batch_size", int),
    ("lora_strength", float), ("lora2_strength", float),
    ("upscale_factor", float), ("upscale_steps", int),
    ("upscale_denoise", float),
]


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

    thread = threading.Thread(
        target=run_job_background,
        args=(job_id, tmp_path, style, style_key, template_key, overrides),
        daemon=True,
    )
    thread.start()

    return jsonify({"job_id": job_id}), 202


@generation_bp.get("/job/<job_id>")
def get_job(job_id: str):
    job = job_store.get(job_id)
    if job is None:
        return jsonify({"error": "Job not found."}), 404
    return jsonify(job)
