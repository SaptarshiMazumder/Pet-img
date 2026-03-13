"""
Image review — analyze generated animal portraits for defects via Gemini vision.
Returns a fix prompt if issues found, else None.
"""
import json
import os
import re

from google import genai
from google.genai import types

_client = None
MODEL = "gemini-3.1-flash-lite-preview"

REVIEW_PROMPT = """
You are reviewing an AI-generated image of an animal in a humanoid pose (e.g., standing on two legs, dressed as a character).
The image should show a single animal with a humanoid body — correct number of limbs, proper paws/feet, one tail, etc.

Check for these DEFECTS:
1. **Mangled or wrong paws/feet** — feet that look like human fingers, deformed paws, extra toes, fused digits
2. **Extra hands or arms** — more than two arms/hands
3. **Extra legs** — more than two legs (hind legs visible when they shouldn't be, extra feet)
4. **Extra tail** — multiple tails, or tail in wrong place
5. **Wrong body parts** — animal hind legs/body visible on top of or alongside the humanoid body
6. **Other anatomical errors** — duplicated limbs, missing limbs, distorted proportions

If the image looks correct (no defects), respond with exactly: {"ok": true}

If you find one or more defects, respond with JSON only in this exact shape:
{
  "ok": false,
  "fix_prompt": "A clear, precise, SHORT instruction for fixing the image. Examples: 'Fix the paws and feet to look like proper animal paws. Do not touch anything else.' or 'Remove the extra hands. Do not touch anything else.' or 'Remove the extra tail. Do not touch anything else.' The fix_prompt must: (1) state exactly what to fix, (2) end with 'Do not touch anything else.' — nothing else."
}

Return ONLY valid JSON. No markdown, no explanation, no extra text.
"""


def _get_client():
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY must be set for image review")
        _client = genai.Client(api_key=api_key)
    return _client


def review_image(image_bytes: bytes, mime_type: str = "image/png") -> str | None:
    """
    Analyze the image for defects. Returns a fix prompt if issues found, else None.
    """
    client = _get_client()
    response = client.models.generate_content(
        model=MODEL,
        contents=[
            types.Part.from_text(text=REVIEW_PROMPT),
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
        ],
    )

    text = (response.text or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```\s*json?\s*", "", text).strip().rstrip("`")

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None  # If we can't parse, assume ok and skip fix

    if data.get("ok") is True:
        return None

    fix_prompt = (data.get("fix_prompt") or "").strip()
    if not fix_prompt:
        return None

    # Ensure it ends with the safety instruction
    if "do not touch anything else" not in fix_prompt.lower():
        fix_prompt = f"{fix_prompt.rstrip('.')} Do not touch anything else."

    return fix_prompt
