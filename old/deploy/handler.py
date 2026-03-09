"""
RunPod Serverless Handler — ComfyUI Prompt Generator
-----------------------------------------------------
Wraps prompt_generator.py for RunPod serverless deployment.

Expected job input:
{
    "image_url": "https://...",          // public image URL  (use this OR image_base64)
    "image_base64": "<base64 string>",   // base64-encoded image (use this OR image_url)
    "image_mime_type": "image/jpeg",     // required when using image_base64, e.g. "image/jpeg", "image/png"
    "template_index": 0,                 // optional — index into lora_templates.json; omit to run all
    "all_templates": false               // optional — set true to generate for every template
}

Returns:
{
    "results": [
        {
            "lora": "Japanese Ink-Wash",
            "baseModel": "FLUX1",
            "workflow": "Workflows/flux_redux_workflow.json.json",
            "triggerWord": "",
            "prompt": "A golden retriever with..."
        },
        ...
    ],
    "animal_description": "A golden retriever with..."
}
"""

import base64
import json
import os
import tempfile
from pathlib import Path

import google.generativeai as genai
import requests
import runpod

from prompt_generator import (
    analyze_image,
    generate_comfyui_prompt,
    load_templates,
)

# ---- Init Gemini once at cold-start ----------------------------------------

_model = None

def get_model():
    global _model
    if _model is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY environment variable is not set.")
        genai.configure(api_key=api_key)
        _model = genai.GenerativeModel("gemini-2.0-flash")
    return _model


# ---- Helper: resolve image to a local tmp path or URL ----------------------

def resolve_image(job_input: dict) -> str:
    """Returns a file path or URL that load_image_part() can consume."""
    if "image_url" in job_input:
        return job_input["image_url"]

    if "image_base64" in job_input:
        mime_type = job_input.get("image_mime_type", "image/jpeg")
        ext_map = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/gif": ".gif",
            "image/webp": ".webp",
        }
        ext = ext_map.get(mime_type, ".jpg")
        data = base64.b64decode(job_input["image_base64"])
        tmp = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
        tmp.write(data)
        tmp.flush()
        tmp.close()
        return tmp.name

    raise ValueError("Job input must contain either 'image_url' or 'image_base64'.")


# ---- Handler ----------------------------------------------------------------

def handler(job):
    job_input = job.get("input", {})

    try:
        image_path = resolve_image(job_input)
    except ValueError as e:
        return {"error": str(e)}

    model = get_model()
    templates = load_templates()

    # Analyze image
    try:
        animal_description = analyze_image(model, image_path)
    except Exception as e:
        return {"error": f"Image analysis failed: {e}"}

    # Determine which templates to use
    all_templates_flag = job_input.get("all_templates", False)
    template_index = job_input.get("template_index", None)

    if all_templates_flag:
        selected_templates = templates
    elif template_index is not None:
        if not (0 <= template_index < len(templates)):
            return {"error": f"template_index {template_index} out of range (0–{len(templates)-1})"}
        selected_templates = [templates[template_index]]
    else:
        selected_templates = templates  # default: generate for all

    # Generate prompts
    results = []
    for template in selected_templates:
        example_prompts = [p for p in template.get("examplePrompts", []) if p.strip()]

        # If multiple example prompts, use the first one (no interactive input in serverless)
        if len(example_prompts) > 1:
            # Use provided example_prompt_index if supplied, else default to 0
            ep_index = job_input.get("example_prompt_index", 0)
            ep_index = max(0, min(ep_index, len(example_prompts) - 1))
            template = {**template, "examplePrompts": [example_prompts[ep_index]]}

        try:
            prompt = generate_comfyui_prompt(model, animal_description, template)
            results.append({
                "lora": template["loraName"],
                "baseModel": template["baseModel"],
                "workflow": template.get("workflow", ""),
                "triggerWord": template.get("triggerWord", ""),
                "prompt": prompt,
            })
        except Exception as e:
            results.append({
                "lora": template["loraName"],
                "error": str(e),
            })

    # Clean up temp file if created
    if "image_base64" in job_input and Path(image_path).exists():
        Path(image_path).unlink(missing_ok=True)

    return {
        "animal_description": animal_description,
        "results": results,
    }


if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})
