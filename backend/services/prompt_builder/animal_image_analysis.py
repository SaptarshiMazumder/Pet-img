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
Example subject_phrase (tabby cat): "A stoic orange tabby cat with rich ginger fur marked by darker orange stripes along the back and sides, a pale cream muzzle sharply contrasting the striped cheeks, cream fur on the chest and inner legs, long white whiskers, alert triangular ears, and steady amber eyes"
Example subject_phrase (colorpoint cat): "A stoic Ragdoll cat with a plush cream-white body, a dark seal-brown mask covering the eye area, nose bridge, and cheeks contrasting with the pale cream forehead and chin, matching dark brown ear tips and paw points, long silky fur, a full plumed tail, and vivid blue eyes"

Example face_sentence (dog): "The Shiba Inu has a rounded face with a cream muzzle surrounded by orange fur, a black nose, and dark almond-shaped eyes."
Example face_sentence (tabby cat): "The tabby cat has a graceful face with striped cheeks, a pale cream muzzle, and steady amber eyes."
Example face_sentence (colorpoint cat): "The Ragdoll has a soft round face with a dark seal mask across the eyes and nose bridge sharply contrasting the pale cream forehead, a pinkish-grey nose leather, and large vivid blue eyes."

CRITICAL for fur pattern accuracy — be highly specific:
- For colorpoint cats/dogs: name the exact color of the points (e.g. "seal brown", "blue-grey", "flame orange"), describe precisely which areas are pointed (eye mask, nose bridge, cheeks, ear tips, paws, tail tip) vs which areas are pale/white, and describe whether the color transition is sharp or gradual.
- For tabby cats/dogs: specify stripe width (thin, bold), placement (back, sides, legs, face), and the exact contrast between stripe color and base coat.
- For bicolor or patched animals: describe the exact size, placement, and edge sharpness of each color patch.
- Always contrast the darkest and lightest areas explicitly so the pattern can be reconstructed from words alone.

Your job:
1. Identify the species/breed (e.g. "Shiba Inu", "orange tabby cat", "Ragdoll cat").
2. Detect life stage from physical cues (proportions, body size, coat development):
   - "puppy" if clearly a young puppy (large paws relative to body, round face, soft fluffy coat, small stature)
   - "kitten" if clearly a young kitten
   - "adult" otherwise (default when age is ambiguous)
   - "senior" only if clearly elderly (greyed muzzle, cloudy eyes)
   If the life stage is "puppy" or "kitten", append it to the species name: e.g. "German Shepherd puppy", "tabby kitten".
3. Write subject_phrase: Start with "A stoic" then the species/breed name (including life stage if puppy/kitten), then "with" and a rich description of: fur color and pattern, specific markings with exact body locations, tail, ears, and eyes. Follow the fur pattern accuracy rules above. Physical traits only — no expression, no role.
4. Write face_sentence: A single sentence starting with "The [species or breed]" describing face shape, the specific marking pattern on the face (which areas are dark vs pale), nose color/shape, and eye color/shape. Use a period at the end. No expression or mood.
5. Set pronoun: "dog" if canine, "cat" if feline, otherwise "animal".

Return JSON in exactly this shape (no extra fields):
{
  "species": "German Shepherd puppy",
  "subject_phrase": "A stoic German Shepherd puppy with ...",
  "face_sentence": "The German Shepherd puppy has ...",
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
