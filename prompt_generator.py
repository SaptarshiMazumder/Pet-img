import json
import os
import random
from pathlib import Path

from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


# ----------------------------
# Config
# ----------------------------

MODEL = "gemini-2.0-flash"

STYLES_FILE = Path(__file__).parent / "styles.json"
NEGATIVE_PROMPTS_FILE = Path(__file__).parent / "negative_prompts.json"


def build_negative_prompt(style_key: str) -> str:
    with open(NEGATIVE_PROMPTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    terms = []
    for category in data["base"].values():
        terms.extend(category)
    terms.extend(data["per_style"].get(style_key, []))
    return ", ".join(terms)


def load_style(style_key: str) -> dict:
    with open(STYLES_FILE, "r", encoding="utf-8") as f:
        styles = json.load(f)
    if style_key not in styles:
        raise ValueError(f"Unknown style '{style_key}'. Available: {', '.join(styles)}")
    return styles[style_key]


def pick_style_interactive() -> dict:
    with open(STYLES_FILE, "r", encoding="utf-8") as f:
        styles = json.load(f)
    keys = list(styles.keys())
    print("\nAvailable styles:")
    for i, key in enumerate(keys, 1):
        print(f"  {i}. {styles[key]['name']} [{key}]")
    while True:
        choice = input("\nPick a style (number or key): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(keys):
            return styles[keys[int(choice) - 1]]
        if choice in styles:
            return styles[choice]
        print(f"Invalid choice. Enter a number 1-{len(keys)} or a key.")

SCENARIO_THEMES = [
    "shogun court",
    "samurai nobility",
    "edo-era scholar",
    "moonlit sakura garden",
    "traditional tea room",
    "castle chamber",
    "riverside pavilion",
    "tatami interior",
    "warrior at rest",
    "noble contemplation",
    "cliffside overlook",
    "misty mountain pass",
    "waterfall shrine",
    "cherry blossom storm",
    "foggy river crossing",
    "lone warrior vigil",
    "storm before battle",
    "night fishing by lantern light",
]

PROPS = [
    "sake cup",
    "traditional sake bottle",
    "low lacquered tray",
    "unfurled scroll",
    "rolled scroll",
    "kiseru tobacco pipe",
    "ink stone and calligraphy brush",
    "folding screen",
    "ornamental ceramics",
    "stone lantern",
    "folded war fan",
    "open iron war fan held elegantly",
    "katana blade being slowly drawn",
    "whetstone and blade resting on cloth",
    "lacquered sake set on a low table",
    "silk pillow",
    "decorative armor chest piece displayed beside",
    "bundle of incense sticks",
    "wooden go board with scattered stones",
    "hanging paper lantern",
]

INDOOR_LOCATIONS = [
    "inside a refined tatami chamber with sliding shoji screens",
    "within a dimly lit castle interior, candlelit and ornate",
    "in a noble tea room with a low lacquered table",
    "inside a private study lined with scrolls and ink",
    "in a grand audience hall with wooden pillars and silk banners",
    "inside a warrior's quarters, armor displayed on a stand nearby",
    "in a torchlit inner sanctum of a mountain fortress",
]

INDOOR_POSES = [
    "reclining sideways on a silk pillow, one arm propped, gazing into the distance",
    "lying across cushions, lazily holding a sake cup aloft",
    "seated cross-legged, slowly whetting a blade on a stone cloth in lap",
    "leaning against a wooden pillar, unrolling a long scroll with focus",
    "kneeling upright at a low table, brush in hand mid-stroke",
    "half-reclined on a floor cushion, exhaling a long slow breath from a kiseru pipe",
    "seated with one knee raised, holding a folded fan open across the knee",
    "sprawled with elegant composure across cushions, holding a sake cup above the face",
    "sitting with back against a shoji screen, one hand resting on a sheathed blade",
    "poised at a go board, fingers hovering over a stone in deep thought",
]

OUTDOOR_LOCATIONS = [
    "on a rugged cliffside overlooking a vast misty valley below",
    "beneath a massive storm-weathered sakura tree dropping petals into the wind",
    "standing at the edge of a mountain waterfall, mist rising around the figure",
    "on a narrow stone bridge over a rushing river at dusk",
    "at the peak of a mossy staircase leading to a mountain shrine",
    "on a rocky coastal cliff, waves crashing far below in stormy light",
    "beside a still mountain lake reflecting the full moon",
    "in an open bamboo grove, shafts of moonlight cutting through the stalks",
    "on a foggy river bank, a small lantern-lit boat tied nearby",
    "at the crest of a hill, overlooking a sea of cherry blossoms at night",
]

OUTDOOR_POSES = [
    "standing at the cliff edge, robes billowing in the wind, gazing into the mist",
    "crouching low on a mossy rock, one hand braced on the ground, surveying the land",
    "seated on a large stone at the waterfall's edge, one foot dangling",
    "standing with arms folded inside wide sleeves, watching petals fall",
    "kneeling at the riverbank, one hand trailing in the water",
    "posed with one foot on a boulder, arms crossed, wind pulling at the robes",
    "leaning against a gnarled tree trunk at the cliff edge, eyes closed",
    "standing in a clearing, sword drawn vertically and held before the face in salute",
    "seated on a flat rock beside the water, a sake cup raised toward the moon",
    "walking slowly through falling petals, head tilted slightly upward",
]

MOODS = [
    "intimate, noble, relaxed, and atmospheric",
    "calm, dignified, scholarly, and atmospheric",
    "serene, royal, contemplative, and elegant",
    "disciplined, noble, quiet, and cinematic",
    "melancholic, solitary, and beautifully foreboding",
    "tense, still, and charged with quiet power",
    "wistful, windswept, and poetic",
    "proud, commanding, and timeless",
]

# Optional toggles
ALLOW_GLASSES = True
ALLOW_HATS = True
ALLOW_ARMOR = True
ALLOW_KIMONO = True
ALLOW_INDOORS = True
ALLOW_OUTDOORS = True


# ----------------------------
# Helpers
# ----------------------------

def load_image_bytes(image_path: str) -> tuple[bytes, str]:
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    ext = path.suffix.lower().replace(".", "")
    if ext == "jpg":
        ext = "jpeg"
    if ext not in {"png", "jpeg", "webp"}:
        raise ValueError("Use a PNG, JPG/JPEG, or WEBP image.")

    return path.read_bytes(), f"image/{ext}"


def safe_json_loads(text: str) -> dict:
    """
    Tries to parse JSON even if the model wraps it in markdown fences.
    """
    cleaned = text.strip()

    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.replace("json\n", "", 1).strip()

    return json.loads(cleaned)


# ----------------------------
# Step 1: Extract animal appearance
# ----------------------------

def extract_animal_appearance(image_path: str) -> dict:
    image_bytes, mime_type = load_image_bytes(image_path)

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
- posture
- pose
- body position
- how many legs/paws
- background
- clothing
- accessories
- what the animal is doing
- camera/viewpoint

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

    return safe_json_loads(response.text)


# ----------------------------
# Step 2: Generate scenario
# ----------------------------

def generate_edo_scenario(
    animal_data: dict,
    allow_glasses: bool = ALLOW_GLASSES,
    allow_hats: bool = ALLOW_HATS,
    allow_armor: bool = ALLOW_ARMOR,
    allow_kimono: bool = ALLOW_KIMONO,
    allow_indoors: bool = ALLOW_INDOORS,
    allow_outdoors: bool = ALLOW_OUTDOORS,
) -> dict:
    chosen_theme = random.choice(SCENARIO_THEMES)
    chosen_mood = random.choice(MOODS)

    allowed_wardrobe = ["royal historical attire"]
    if allow_armor:
        allowed_wardrobe.append("samurai armor")
    if allow_kimono:
        allowed_wardrobe.append("layered kimono")
    if allow_hats:
        allowed_wardrobe.append("shogun hat or scholar hat")
    if allow_glasses:
        allowed_wardrobe.append("reading glasses occasionally")

    # Pick indoor or outdoor based on toggles
    modes = []
    if allow_indoors:
        modes.append("indoor")
    if allow_outdoors:
        modes.append("outdoor")
    chosen_mode = random.choice(modes)

    if chosen_mode == "indoor":
        chosen_location = random.choice(INDOOR_LOCATIONS)
        pose_suggestions = random.sample(INDOOR_POSES, k=3)
        setting_guidance = "The setting is indoors — a noble, intimate Japanese interior."
    else:
        chosen_location = random.choice(OUTDOOR_LOCATIONS)
        pose_suggestions = random.sample(OUTDOOR_POSES, k=3)
        setting_guidance = "The setting is outdoors — dramatic natural landscape in Edo-era Japan."

    prompt = f"""
You are generating a vivid scene for an animal portrait prompt.

The animal likeness is:
{json.dumps(animal_data, ensure_ascii=False, indent=2)}

Constraints:
- The setting must feel strongly Edo-era Japanese.
- Keep themes around: shogun, samurai, sakura, sake, cliffs, waterfalls, rivers, moonlight, mist, water, tatami, castle interiors, garden pavilions, noble chambers.
- The animal must always be richly clothed and represent royalty, nobility, warrior class, or scholar-aristocracy.
- Make the scene elegant, vivid, and image-generation friendly.
- Do not make it modern.
- Do not make it goofy.
- Do not add extra animals.
- Do not make the wardrobe generic fantasy; keep it traditional Japanese-inspired.
- The pose_action must be physically specific, visually interesting, and cinematic — not just "standing" or "sitting".

Allowed wardrobe directions:
{", ".join(allowed_wardrobe)}

Setting mode: {chosen_mode}
{setting_guidance}

Suggested location:
{chosen_location}

Pose inspiration (pick or adapt one of these, or invent something equally vivid):
{chr(10).join(f"- {p}" for p in pose_suggestions)}

Preferred theme for this run:
{chosen_theme}

Target mood:
{chosen_mood}

Return JSON only in exactly this shape:
{{
  "role_title": "...",
  "wardrobe": "...",
  "pose_action": "...",
  "props": ["...", "..."],
  "environment": "...",
  "lighting": "...",
  "mood": "...",
  "scenario_summary": "..."
}}
"""

    response = client.models.generate_content(model=MODEL, contents=prompt)

    data = safe_json_loads(response.text)

    filtered_props = [p for p in data.get("props", []) if isinstance(p, str)]
    if not filtered_props:
        filtered_props = random.sample(PROPS, k=3)

    data["props"] = filtered_props
    return data


# ----------------------------
# Step 3: Compose final prompt
# ----------------------------

def compose_final_prompt(animal_data: dict, scenario_data: dict, style: dict) -> str:
    prefix = style["trigger_word"]
    style_suffix = style["suffix"]
    subject = animal_data["prompt_subject_phrase"].strip()
    role_title = scenario_data["role_title"].strip()
    wardrobe = scenario_data["wardrobe"].strip()
    pose_action = scenario_data["pose_action"].strip()
    environment = scenario_data["environment"].strip()
    lighting = scenario_data["lighting"].strip()
    mood = scenario_data["mood"].strip()
    props = scenario_data.get("props", [])

    props_sentence = ""
    if props:
        if len(props) == 1:
            props_sentence = f" Beside it rests {props[0]}."
        elif len(props) == 2:
            props_sentence = f" Beside it rest {props[0]} and {props[1]}."
        else:
            props_sentence = (
                f" Beside it rest {', '.join(props[:-1])}, and {props[-1]}."
            )

    full_prompt = (
        f"{prefix} {subject}, portrayed as {role_title}. "
        f"{animal_data['appearance_summary']} "
        f"It is dressed in {wardrobe}. "
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
    style_key: str = "inkwash",
    allow_glasses: bool = ALLOW_GLASSES,
    allow_hats: bool = ALLOW_HATS,
    allow_armor: bool = ALLOW_ARMOR,
    allow_kimono: bool = ALLOW_KIMONO,
    allow_indoors: bool = ALLOW_INDOORS,
    allow_outdoors: bool = ALLOW_OUTDOORS,
) -> dict:
    animal_data = extract_animal_appearance(image_path)
    scenario_data = generate_edo_scenario(
        animal_data,
        allow_glasses=allow_glasses,
        allow_hats=allow_hats,
        allow_armor=allow_armor,
        allow_kimono=allow_kimono,
        allow_indoors=allow_indoors,
        allow_outdoors=allow_outdoors,
    )
    final_prompt = compose_final_prompt(animal_data, scenario_data, style=style)
    negative_prompt = build_negative_prompt(style_key)

    return {
        "animal_data": animal_data,
        "scenario_data": scenario_data,
        "positive_prompt": final_prompt,
        "negative_prompt": negative_prompt,
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python prompt_generator.py /path/to/animal_image.png")
        raise SystemExit(1)

    image_path = sys.argv[1]
    style = pick_style_interactive()
    style_key = next(
        k for k, v in json.loads(STYLES_FILE.read_text(encoding="utf-8")).items()
        if v["trigger_word"] == style["trigger_word"]
    )
    result = build_animal_edo_prompt(image_path, style=style, style_key=style_key)

    print("\n=== ANIMAL DATA ===")
    print(json.dumps(result["animal_data"], indent=2, ensure_ascii=False))

    print("\n=== SCENARIO DATA ===")
    print(json.dumps(result["scenario_data"], indent=2, ensure_ascii=False))

    print("\n=== POSITIVE PROMPT ===")
    print(result["positive_prompt"])

    print("\n=== NEGATIVE PROMPT ===")
    print(result["negative_prompt"])
