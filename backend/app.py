import json
import sys
import tempfile
from pathlib import Path

from flask import Flask, jsonify, request
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

# Allow importing from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from prompt_generator import build_animal_edo_prompt, load_style, STYLES_FILE
from runpod_client import run_job

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB max upload


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


@app.post("/generate")
def generate_prompt():
    """
    Full pipeline: pet photo → Gemini prompts → RunPod image generation.

    Form fields:
      image          (file,  required)  PNG, JPG, or WEBP
      style_key      (str,   default: inkwash)
      allow_glasses  (bool,  default: true)
      allow_hats     (bool,  default: true)
      allow_armor    (bool,  default: true)
      allow_kimono   (bool,  default: true)
      allow_indoors  (bool,  default: true)
      allow_outdoors (bool,  default: true)

      --- RunPod overrides (all optional) ---
      width          (int,   default: 1024)
      height         (int,   default: 1024)
      steps          (int,   default: 15)
      cfg            (float, default: 1.0)
      seed           (int,   default: random)
      batch_size     (int,   default: 1)
      lora_strength  (float) override LoRA 1 strength
      lora2_strength (float) override LoRA 2 strength
      upscale_factor (float, default: 1.25)
      upscale_steps  (int,   default: 8)
      upscale_denoise(float, default: 0.7)

    Returns JSON:
      positive_prompt, negative_prompt, animal_data, scenario_data,
      style, images (list of {url, key, index} from RunPod/R2)
    """
    if "image" not in request.files:
        return jsonify({"error": "No image file provided."}), 400

    image = request.files["image"]
    suffix = Path(image.filename).suffix.lower()
    if suffix not in {".png", ".jpg", ".jpeg", ".webp"}:
        return jsonify({"error": "Image must be PNG, JPG, or WEBP."}), 400

    style_key = request.form.get("style_key", "inkwash")

    def get_bool(field, default=True):
        val = request.form.get(field)
        if val is None:
            return default
        return val.lower() not in {"false", "0", "no"}

    allow_indoors = get_bool("allow_indoors")
    allow_outdoors = get_bool("allow_outdoors")

    if not allow_indoors and not allow_outdoors:
        return jsonify({"error": "At least one of allow_indoors or allow_outdoors must be true."}), 400

    try:
        style = load_style(style_key)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    # Save upload to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        image.save(tmp)
        tmp_path = tmp.name

    try:
        result = build_animal_edo_prompt(
            image_path=tmp_path,
            style=style,
            style_key=style_key,
            allow_glasses=get_bool("allow_glasses"),
            allow_hats=get_bool("allow_hats"),
            allow_armor=get_bool("allow_armor"),
            allow_kimono=get_bool("allow_kimono"),
            allow_indoors=allow_indoors,
            allow_outdoors=allow_outdoors,
        )
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    # Build RunPod job input from style LoRA config + user overrides
    lora_cfg = style.get("lora", {})
    job_input = {
        "prompt": result["positive_prompt"],
        "negative_prompt": result["negative_prompt"],
        "lora_name": lora_cfg.get("lora_name", "wetInkZTurbo.safetensors"),
        "lora_strength": lora_cfg.get("lora_strength", 0.3),
        "lora2_name": lora_cfg.get("lora2_name", "ukiyoeZTurbo.safetensors"),
        "lora2_strength": lora_cfg.get("lora2_strength", 0.0),
    }

    # Optional RunPod overrides from request
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

    # Call RunPod
    try:
        runpod_result = run_job(job_input)
    except Exception as e:
        return jsonify({"error": f"RunPod error: {e}"}), 502

    return jsonify({
        "style": style_key,
        "positive_prompt": result["positive_prompt"],
        "negative_prompt": result["negative_prompt"],
        "animal_data": result["animal_data"],
        "scenario_data": result["scenario_data"],
        "images": runpod_result.get("images", []),
        "seed": runpod_result.get("seed"),
        "prompt_id": runpod_result.get("prompt_id"),
    })


# ----------------------------
# Run
# ----------------------------

if __name__ == "__main__":
    app.run(debug=True, port=5000)
