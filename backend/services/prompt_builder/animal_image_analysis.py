"""
Animal image analysis via Gemini vision.
Extracts physical traits (fur, eyes, markings) from a pet reference image.
"""
import json
import os
import re
from pathlib import Path

from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

_client = None
MODEL = "gemini-3.1-flash-lite-preview"


def _get_client():
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY must be set for animal analysis")
        _client = genai.Client(api_key=api_key)
    return _client


ANALYSIS_PROMPT = """
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


def extract_animal_appearance(image_path: str) -> dict:
    """
    Analyze the animal in the image: fur patterns, colors, eyes, ears, marks.
    Returns subject_phrase, face_sentence, species, pronoun (dog/cat/animal).
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

    response = _get_client().models.generate_content(
        model=MODEL,
        contents=[
            types.Part.from_text(text=ANALYSIS_PROMPT),
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
