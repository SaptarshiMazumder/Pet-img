import json
import os
import re
from pathlib import Path

from google import genai
from google.genai import types
from dotenv import load_dotenv

from backend.config import STYLES_FILE, TEMPLATES_FILE, NEGATIVE_PROMPTS_FILE

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODEL = "gemini-2.0-flash"


# ----------------------------
# Loaders
# ----------------------------

def load_style(style_key: str) -> dict:
    styles = json.loads(STYLES_FILE.read_text(encoding="utf-8"))
    if style_key not in styles:
        raise ValueError(f"Unknown style '{style_key}'. Available: {', '.join(styles)}")
    return styles[style_key]


def load_template(template_key: str) -> dict:
    templates = json.loads(TEMPLATES_FILE.read_text(encoding="utf-8"))
    if template_key not in templates:
        raise ValueError(f"Unknown template '{template_key}'. Available: {', '.join(templates)}")
    return templates[template_key]


def build_negative_prompt(style_key: str) -> str:
    """Read negative prompt terms from JSON (array of strings) and join for ComfyUI."""
    default = "blurry, watermark, deformed paws, human like fingers"
    try:
        data = json.loads(NEGATIVE_PROMPTS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, FileNotFoundError):
        return default
    if isinstance(data, list):
        terms = [str(t).strip() for t in data if t]
        return ", ".join(terms) if terms else default
    return default


# ----------------------------
# Step 1: Analyze animal in image (Gemini)
# ----------------------------

def extract_animal_appearance(image_path: str) -> dict:
    """
    Analyze the animal in the image: fur patterns, colors, eyes, ears, marks.
    Returns subject_phrase (for "A stoic X with ..."), face_sentence, species, pronoun (dog/cat/animal).
    """
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    ext = path.suffix.lower().replace(".", "")
    if ext == "jpg":
        ext = "jpeg"
    if ext not in {"png", "jpeg", "webp"}:
        raise ValueError("Use a PNG, JPG/JPEG, or WEBP image.")

    image_bytes = path.read_bytes()
    mime_type = f"image/{ext}"

    prompt = """
You are analyzing an animal reference image for physical appearance only. Your output will be used to build a single art prompt. Return JSON only.

CRITICAL — DO NOT include any expression, mood, or gesture from the reference image:
- Do NOT describe or infer: tongue, panting, smiling, open mouth, happy, sad, alert, calm, dignified, fierce, sleepy, or any other expression or emotion.
- Do NOT copy any facial expression from the photo. Describe only neutral, physical traits: face shape, nose, eye shape and color, fur, markings, ears, etc.
- If the animal has its tongue out, is panting, or has any distinctive expression in the photo, ignore it completely. Describe the face and body as neutral physical features only.

Describe the animal in the same style as these examples (physical traits only, no expression):

Example subject_phrase (dog): "A stoic Shiba Inu with warm golden-orange fur, soft cream-white markings on the muzzle, chest, and inner legs, a plush curled tail, small upright triangular ears, and dark almond-shaped eyes"
Example subject_phrase (cat): "A stoic orange tabby cat with rich ginger fur marked by darker orange stripes, a pale muzzle, soft cream fur along the chest and inner body, long white whiskers, alert triangular ears, and steady amber eyes"

Example face_sentence (dog): "The Shiba Inu has a rounded face, a black nose, and dark almond-shaped eyes."
Example face_sentence (cat): "The cat has a graceful face structure, a pale muzzle, and amber eyes; its striped coat gives it an elegant presence."

Your job:
1. Identify the species/breed (e.g. "Shiba Inu", "orange tabby cat", "golden retriever").
2. Write subject_phrase: Start with "A stoic" then the species/breed name, then "with" and a rich description of: fur color and pattern, markings (muzzle, chest, legs, etc.), tail, ears, and eyes. Physical traits only. Do NOT add "portrayed as" or any role. Do NOT include any expression (no panting, tongue, smile, etc.).
3. Write face_sentence: A single sentence starting with "The [species or breed]" describing only physical face features: face shape, nose, eye shape and color. Optionally one line about coat. Use a period at the end. Do NOT mention any expression, mood, or emotion.
4. Set pronoun: "dog" if canine, "cat" if feline, otherwise "animal".

Return JSON in exactly this shape (no extra fields):
{
  "species": "Shiba Inu",
  "subject_phrase": "A stoic Shiba Inu with ...",
  "face_sentence": "The Shiba Inu has ...",
  "pronoun": "dog"
}
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=[
            types.Part.from_text(text=prompt),
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
        ],
    )

    text = response.text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```\s*json?\s*", "", text).strip().rstrip("`")
    data = json.loads(text)

    species = (data.get("species") or "animal").strip()
    subject_phrase = (data.get("subject_phrase") or "A stoic animal").strip()
    face_sentence = (data.get("face_sentence") or f"The {species} has a neutral face with typical features.").strip()
    pronoun = (data.get("pronoun") or "animal").strip().lower()
    if pronoun not in ("dog", "cat", "animal"):
        pronoun = "animal"

    return {
        "species": species,
        "subject_phrase": subject_phrase,
        "face_sentence": face_sentence,
        "pronoun": pronoun,
    }


# ----------------------------
# Step 2: Compose prompt from template + animal + style
# ----------------------------

def _fill_placeholders(s: str, *, pronoun: str, species: str) -> str:
    return s.replace("{pronoun}", pronoun).replace("{species}", species)


def compose_final_prompt(animal_data: dict, template: dict, style: dict) -> str:
    """
    Assemble: [trigger] [subject_phrase], portrayed as [role_title]. [face] It wears/dressed [wardrobe]. [pose]. [props] Setting. Lighting. Mood. [style_suffix]
    Template fields can contain {pronoun} and {species}; we replace them.
    """
    trigger = (style.get("trigger_word") or "").strip()
    style_suffix = (style.get("suffix") or "").strip()

    subject_phrase = animal_data.get("subject_phrase", "A stoic animal").strip()
    face_sentence = animal_data.get("face_sentence", "").strip()
    species = animal_data.get("species", "animal").strip()
    pronoun = animal_data.get("pronoun", "animal").strip().lower()

    role_title = template.get("role_title", "").strip()
    wardrobe = template.get("wardrobe", "").strip()
    attire_verb = template.get("attire_verb", "wears").strip()
    pose_sentence = template.get("pose_sentence", "").strip()
    props_sentence = (template.get("props_sentence") or "").strip()
    environment = template.get("environment", "").strip()
    lighting = template.get("lighting", "").strip()
    mood = template.get("mood", "").strip()

    pose_sentence = _fill_placeholders(pose_sentence, pronoun=pronoun, species=species)
    lighting = _fill_placeholders(lighting, pronoun=pronoun, species=species)
    wardrobe = _fill_placeholders(wardrobe, pronoun=pronoun, species=species)

    subject_line = f"{trigger} {subject_phrase}".strip() if trigger else subject_phrase
    parts = [
        f"{subject_line}, portrayed as {role_title}.",
        face_sentence,
        f"It {attire_verb} {wardrobe}.",
        pose_sentence,
    ]
    if props_sentence:
        parts.append(props_sentence)
    parts.append(f"The setting is {environment}.")
    parts.append(lighting)
    parts.append(f"The mood feels {mood}.")
    parts.append(style_suffix)

    return " ".join(p.strip() for p in parts if p.strip())


# ----------------------------
# Main pipeline
# ----------------------------

def build_animal_edo_prompt(
    image_path: str,
    style: dict,
    style_key: str,
    template_key: str,
) -> dict:
    animal_data = extract_animal_appearance(image_path)
    template = load_template(template_key)
    final_prompt = compose_final_prompt(animal_data, template, style)
    negative_prompt = build_negative_prompt(style_key)

    return {
        "animal_data": animal_data,
        "scenario_data": template,
        "positive_prompt": final_prompt,
        "negative_prompt": negative_prompt,
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python prompt_generator.py /path/to/image.png [template_key] [style_key]")
        raise SystemExit(1)

    image_path = sys.argv[1]
    template_key = sys.argv[2] if len(sys.argv) > 2 else "scholar_lord"
    style_key = sys.argv[3] if len(sys.argv) > 3 else "inkwash"

    style = load_style(style_key)
    result = build_animal_edo_prompt(image_path, style=style, style_key=style_key, template_key=template_key)

    print("\n=== ANIMAL DATA ===")
    print(json.dumps(result["animal_data"], indent=2, ensure_ascii=False))
    print("\n=== TEMPLATE ===")
    print(json.dumps(result["scenario_data"], indent=2, ensure_ascii=False))
    print("\n=== POSITIVE PROMPT ===")
    print(result["positive_prompt"])
    print("\n=== NEGATIVE PROMPT ===")
    print(result["negative_prompt"])
