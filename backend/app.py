import json
import mimetypes
import os
import sys
import tempfile
from pathlib import Path

mimetypes.add_type("image/svg+xml", ".svg")

import boto3
from botocore.config import Config
from flask import Flask, jsonify, request, send_from_directory, Response
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.config import STYLES_FILE, TEMPLATES_FILE, ASSETS_DIR, FRONTEND_DIR
from prompt_generator import build_animal_edo_prompt, load_style, load_template
from runpod_client import run_job

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB


# ----------------------------
# Routes
# ----------------------------

@app.get("/styles")
def list_styles():
    """List all available style keys and their names."""
    styles = json.loads(STYLES_FILE.read_text(encoding="utf-8"))
    return jsonify({
        key: {"name": v["name"], "trigger_word": v["trigger_word"]}
        for key, v in styles.items()
    })


@app.get("/templates")
def list_templates():
    """List all available template keys and their names."""
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


@app.get("/assets/<path:path>")
def serve_assets(path):
    return send_from_directory(ASSETS_DIR, path)


@app.get("/r2-image")
def r2_image():
    """Proxy an R2 object by key so the browser can display it."""
    key = request.args.get("key")
    if not key:
        return "Missing key", 400

    account_id = os.getenv("R2_ACCOUNT_ID", "")
    access_key = os.getenv("R2_ACCESS_KEY_ID", "")
    secret_key = os.getenv("R2_SECRET_ACCESS_KEY", "")
    bucket     = os.getenv("R2_BUCKET_NAME", "")

    if not all([account_id, access_key, secret_key, bucket]):
        missing = [k for k, v in {"R2_ACCOUNT_ID": account_id, "R2_ACCESS_KEY_ID": access_key,
                                   "R2_SECRET_ACCESS_KEY": secret_key, "R2_BUCKET_NAME": bucket}.items() if not v]
        return jsonify({"error": f"Missing env vars: {missing}"}), 500

    try:
        r2 = boto3.client(
            "s3",
            endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=Config(signature_version="s3v4"),
            region_name="auto",
        )
        obj = r2.get_object(Bucket=bucket, Key=key)
        return Response(obj["Body"].read(), mimetype="image/png")
    except Exception as e:
        return jsonify({"error": str(e), "bucket": bucket, "key": key}), 500


@app.get("/")
def serve_index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.get("/<path:path>")
def serve_frontend(path):
    full = FRONTEND_DIR / path
    if full.exists():
        return send_from_directory(FRONTEND_DIR, path)
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.post("/generate")
def generate():
    """
    Full pipeline: pet photo -> Gemini animal description -> template + style -> RunPod image.

    Form fields:
      image         (file,   required)  PNG, JPG, or WEBP
      template_key  (str,    required)  key from templates.json
      style_key     (str,    default: inkwash)  key from styles.json

      --- RunPod overrides (all optional) ---
      width          (int,   default: 1024)
      height         (int,   default: 1024)
      steps          (int,   default: 15)
      cfg            (float, default: 1.0)
      seed           (int,   default: random)
      batch_size     (int,   default: 1)
      lora_strength  (float)
      lora2_strength (float)
      upscale_factor (float, default: 1.25)
      upscale_steps  (int,   default: 8)
      upscale_denoise(float, default: 0.7)
    """
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
        load_template(template_key)  # validate early
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        image.save(tmp)
        tmp_path = tmp.name

    try:
        result = build_animal_edo_prompt(
            image_path=tmp_path,
            style=style,
            style_key=style_key,
            template_key=template_key,
        )
    except Exception as e:
        return jsonify({"error": f"Prompt generation failed: {e}"}), 500
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    lora_cfg = style.get("lora", {})
    job_input = {
        "prompt": result["positive_prompt"],
        "negative_prompt": result["negative_prompt"],
        "lora_name": lora_cfg.get("lora_name", "wetInkZTurbo.safetensors"),
        "lora_strength": lora_cfg.get("lora_strength", 0.3),
        "lora2_name": lora_cfg.get("lora2_name", "ukiyoeZTurbo.safetensors"),
        "lora2_strength": lora_cfg.get("lora2_strength", 0.0),
    }

    for field, cast in [
        ("width", int), ("height", int), ("steps", int),
        ("cfg", float), ("seed", int), ("batch_size", int),
        ("lora_strength", float), ("lora2_strength", float),
        ("upscale_factor", float), ("upscale_steps", int),
        ("upscale_denoise", float),
    ]:
        val = request.form.get(field)
        if val is not None:
            try:
                job_input[field] = cast(val)
            except ValueError:
                return jsonify({"error": f"Invalid value for '{field}'."}), 400

    try:
        runpod_result = run_job(job_input)
    except Exception as e:
        return jsonify({"error": f"RunPod error: {e}"}), 502

    return jsonify({
        "style": style_key,
        "template": template_key,
        "positive_prompt": result["positive_prompt"],
        "negative_prompt": result["negative_prompt"],
        "animal_data": result["animal_data"],
        "scenario_data": result["scenario_data"],
        "images": runpod_result.get("images", []),
        "seed": runpod_result.get("seed"),
        "prompt_id": runpod_result.get("prompt_id"),
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
