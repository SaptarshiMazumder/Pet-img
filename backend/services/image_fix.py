"""
Image fix service — uses Gemini (or Vertex AI) to edit images based on a fix prompt.
Applies the instruction from the review step (e.g., "fix the paws... Do not touch anything else.")
"""
import os

from google import genai
from google.genai import types

_client = None

# Model for image editing (supports image-to-image with text instruction)
IMAGE_EDIT_MODEL = "gemini-3.1-flash-image-preview"


def _get_client():
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY must be set for image fixing")
        _client = genai.Client(api_key=api_key)
    return _client


def fix_image(image_bytes: bytes, fix_prompt: str, mime_type: str = "image/png") -> bytes | None:
    """
    Edit the image according to the fix prompt. Returns the edited image bytes, or None on failure.
    """
    client = _get_client()

    # Build the edit instruction — be explicit about preserving the rest
    full_prompt = f"{fix_prompt}\n\nApply only this change. Preserve the rest of the image exactly."

    response = client.models.generate_content(
        model=IMAGE_EDIT_MODEL,
        contents=[
            types.Part.from_text(text=full_prompt),
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
        ],
        config=types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"]),
    )

    if not response.candidates:
        return None

    for part in response.candidates[0].content.parts:
        if part.inline_data is not None and part.inline_data.data:
            return bytes(part.inline_data.data)

    return None
