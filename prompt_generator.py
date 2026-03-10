import json
import os
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
    data = json.loads(NEGATIVE_PROMPTS_FILE.read_text(encoding="utf-8"))
    terms = []
    for category in data["base"].values():
        terms.extend(category)
    terms.extend(data["per_style"].get(style_key, []))
    return ", ".join(terms)


# ----------------------------
# Step 1: Extract animal appearance (Gemini)
# ----------------------------

def extract_animal_appearance(image_path: str) -> dict:
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
You are analyzing an animal reference image for prompt engineering.

Return JSON only.

Your job is to describe ONLY the animal's likeness-defining physical appearance.
Focus on:
- species
- fur or coat color
- fur patterns and markings
- muzzle details
- face shape
- eye shape and eye color
- nose color/shape
- ears shape/size/orientation
- whiskers if visible
- distinctive identifiers that help preserve likeness
- overall facial vibe

Do NOT mention:
- posture, pose, or body position
- background, clothing, or accessories
- what the animal is doing
- camera or viewpoint

Be concrete and visual. Prioritize face details and markings.

Return JSON in exactly this shape:
{
  "species": "...",
  "appearance_summary": "...",
  "face_details": ["...", "..."],
  "distinctive_traits": ["...", "..."],
  "prompt_subject_phrase": "..."
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
        text = text.strip("`").replace("json\n", "", 1).strip()
    return json.loads(text)


# ----------------------------
# Step 2: Compose final prompt
# ----------------------------

def compose_final_prompt(animal_data: dict, template: dict, style: dict) -> str:
    prefix = style["trigger_word"]
    style_suffix = style["suffix"]
    subject = animal_data["prompt_subject_phrase"].strip()

    role_title = template["role_title"].strip()
    wardrobe = template["wardrobe"].strip()
    pose_action = template["pose_action"].strip()
    environment = template["environment"].strip()
    lighting = template["lighting"].strip()
    mood = template["mood"].strip()
    props = template.get("props", [])

    if props:
        if len(props) == 1:
            props_sentence = f" Beside it rests {props[0]}."
        elif len(props) == 2:
            props_sentence = f" Beside it rest {props[0]} and {props[1]}."
        else:
            props_sentence = f" Beside it rest {', '.join(props[:-1])}, and {props[-1]}."
    else:
        props_sentence = ""

    full_prompt = (
        f"{prefix} {subject}, portrayed as {role_title}. "
        f"{animal_data['appearance_summary']} "
        f"Depicted in a dignified humanoid composition — upper body and face prominently framed, "
        f"dressed in {wardrobe}, lower body naturally obscured by clothing, environment, or framing. "
        f"It is {pose_action}.{props_sentence} "
        f"The scene takes place {environment}. "
        f"{lighting} "
        f"The mood feels {mood}. "
        f"{style_suffix}"
    )

    return " ".join(full_prompt.split())


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
    template_key = sys.argv[2] if len(sys.argv) > 2 else "moonlit_cliffside"
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
