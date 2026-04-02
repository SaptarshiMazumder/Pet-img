"""
Image review for USO style-transfer outputs.
Checks for coherence and subject-scene integration issues.
The artistic style is reference-driven and must never be changed.
"""
import json
import os
import re

from google import genai
from google.genai import types

_client = None
MODEL = "gemini-3.1-flash-lite-preview"

REVIEW_PROMPT_USO = """
You are reviewing an AI-generated style-transfer image of an animal. The image was produced by applying
an artistic style (from a reference painting or artwork) to a subject (a pet photo). The style is intentional
and must not be changed under any circumstances.

Review the image for the following issues:

1. **Subject-scene incoherence** — the animal appears pasted-in or disconnected from the scene, with no
   visual integration (mismatched lighting direction, missing shadows, obvious edge artifacts).
2. **Anatomical errors** — mangled paws, extra or missing limbs, distorted proportions, extra tails.
3. **Obvious artifacts** — hard seams, smeared areas, duplicated body parts, corrupted regions that break
   the visual coherence of the image.
4. **Composition errors** — subject is severely cropped in a way that makes no sense, or key parts of the
   subject are missing when they should be present.

Do NOT flag:
- The artistic style itself (painterly, abstract, sketchy, etc.) — this is intentional.
- Simplified or stylized rendering of the animal — this is expected.
- Unusual color palettes or textures that are part of the style.
- Anything that appears to be a deliberate artistic choice.

If the image looks coherent and acceptable, respond with exactly: {"ok": true}

If you find one or more real issues, respond with JSON only in this exact shape:
{
  "ok": false,
  "fix_prompt": "A clear, precise, SHORT instruction targeting only the broken area. Must: (1) describe exactly what to fix and where, (2) explicitly state 'Preserve the artistic style and overall composition completely. Do not touch anything else.' The fix must be surgical — only the broken area changes."
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


def review_image_uso(image_bytes: bytes, mime_type: str = "image/png") -> str | None:
    """
    Analyze a USO style-transfer output for coherence issues.
    Returns a fix prompt if issues found, else None.
    """
    client = _get_client()
    response = client.models.generate_content(
        model=MODEL,
        contents=[
            types.Part.from_text(text=REVIEW_PROMPT_USO),
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
        ],
    )

    text = (response.text or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```\s*json?\s*", "", text).strip().rstrip("`")

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None

    if data.get("ok") is True:
        return None

    fix_prompt = (data.get("fix_prompt") or "").strip()
    if not fix_prompt:
        return None

    if "preserve the artistic style" not in fix_prompt.lower():
        fix_prompt = f"{fix_prompt.rstrip('.')} Preserve the artistic style and overall composition completely. Do not touch anything else."

    return fix_prompt
