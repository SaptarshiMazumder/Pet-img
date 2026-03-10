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

Return JSON only. Be extremely precise and visual — you are feeding a portrait artist.

Your job is to describe the animal's likeness-defining physical appearance in fine detail.
Cover ALL of the following:

COAT & COLOR:
- Exact base coat color(s) — be specific (e.g. "warm fawn", "blue-grey", "cream with apricot tint")
- Secondary colors and exactly where they appear (muzzle, chest, eyebrows, paws, tail tip, etc.)
- Coat pattern type (solid, bicolor, tricolor, tabby, brindle, merle, tuxedo, etc.)
- Coat texture and length (short and smooth, dense double coat, wiry, silky, wavy, etc.)
- Any white patches, dark masks, saddle markings, ticking, or gradients

FACE & HEAD:
- Face shape (broad, narrow, flat/brachycephalic, elongated, round, wedge-shaped, etc.)
- Forehead markings or wrinkles
- Under-eye area — any tear stains, lighter fur rings, darker fur patches, prominent folds
- Eye shape (almond, round, deep-set, wide-set, hooded) and exact eye color
- Nose color, shape, and size
- Muzzle length, shape, and color
- Jowls, lip color, cheek structure
- Ear shape, size, position, and inner ear color if visible
- Whisker color and thickness if visible
- Any distinctive facial markings that make this individual unique

DISTINCTIVE IDENTIFIERS:
- Anything highly specific to this individual that sets it apart

Do NOT mention posture, background, clothing, accessories, what the animal is doing, or camera angle.

Return JSON in exactly this shape:
{
  "species": "...",
  "breed": "...",
  "coat_summary": "...",
  "face_details": ["...", "..."],
  "distinctive_traits": ["...", "..."],
  "appearance_summary": "...",
  "prompt_subject_phrase": "..."
}

For prompt_subject_phrase: write a dense, comma-separated phrase capturing the most visually unique coat and face details — this will be injected directly into an art prompt.
For appearance_summary: write 2-3 natural sentences describing the animal's full appearance for an artist.
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

    species = animal_data.get("species", "animal").lower()
    breed = animal_data.get("breed", "").strip()
    coat_summary = animal_data.get("coat_summary", "").strip()
    distinctive = animal_data.get("distinctive_traits", [])

    role_title = template["role_title"].strip()
    wardrobe = template["wardrobe"].strip()
    pose_action = template["pose_action"].strip()
    environment = template["environment"].strip()
    lighting = template["lighting"].strip()
    mood = template["mood"].strip()
    props = template.get("props", [])

    # Species-specific paw language
    paw_term = "paws"
    if "cat" in species or "feline" in species or "kitten" in species:
        paw_term = "cat paws with retractable claws"
    elif "dog" in species or "canine" in species or "puppy" in species:
        paw_term = "dog paws with visible paw pads"
    elif "rabbit" in species or "bunny" in species:
        paw_term = "rabbit paws"
    elif "bear" in species:
        paw_term = "bear paws with claws"
    elif "fox" in species:
        paw_term = "fox paws"

    if props:
        if len(props) == 1:
            props_sentence = f" Beside it rests {props[0]}."
        elif len(props) == 2:
            props_sentence = f" Beside it rest {props[0]} and {props[1]}."
        else:
            props_sentence = f" Beside it rest {', '.join(props[:-1])}, and {props[-1]}."
    else:
        props_sentence = ""

    # Build appearance detail line
    appearance_line = animal_data["appearance_summary"].strip()
    if coat_summary:
        appearance_line += f" Coat: {coat_summary}."
    if distinctive:
        appearance_line += f" Distinctive features: {'; '.join(distinctive)}."

    species_label = f"{breed} {species}".strip() if breed else species

    full_prompt = (
        f"{prefix} {subject}, a {species_label} portrayed as {role_title}. "
        f"{appearance_line} "
        f"Depicted in a dignified humanoid composition — upper body and face prominently framed, "
        f"dressed in {wardrobe}, retaining natural {paw_term} (not human hands or fingers), "
        f"lower body naturally obscured by clothing, environment, or framing. "
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
