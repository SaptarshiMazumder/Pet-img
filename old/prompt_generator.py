"""
ComfyUI Prompt Generator for Animal Images
-------------------------------------------
Analyzes an animal image using Gemini's vision API and generates a
ComfyUI-ready prompt based on a selected LoRA template from lora_templates.json.

Usage:
    python prompt_generator.py --image <path_or_url> --keywords "keyword1, keyword2" [--template <index>] [--list-templates]

Requirements:
    pip install google-generativeai requests python-dotenv
    Set GEMINI_API_KEY in .env file.
"""

import json
import os
import sys
from pathlib import Path

import google.generativeai as genai
import requests
from dotenv import load_dotenv

load_dotenv()

TEMPLATES_FILE = Path(__file__).parent / "lora_templates.json"

# ---------------------------------------------------------------------------
# Config — edit these before running
# ---------------------------------------------------------------------------
IMAGE_PATH = r"C:\Users\sapma\Downloads\BlackShiba.png"
TEMPLATE_INDEX = None  # set to an int to skip interactive selection, or None to pick interactively
ALL_TEMPLATES = False  # set to True to generate prompts for every template
# ---------------------------------------------------------------------------

MEDIA_TYPE_MAP = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_templates() -> list[dict]:
    if not TEMPLATES_FILE.exists():
        print(f"[ERROR] Templates file not found: {TEMPLATES_FILE}", file=sys.stderr)
        sys.exit(1)
    with open(TEMPLATES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def list_templates(templates: list[dict]) -> None:
    print("\nAvailable LoRA Templates:")
    print("=" * 60)
    for i, t in enumerate(templates):
        print(f"  [{i}] {t['loraName']}  |  Base: {t['baseModel']}  |  Trigger: {t['triggerWord']}")
    print()


def is_url(path: str) -> bool:
    return path.startswith("http://") or path.startswith("https://")


def load_image_part(image_path: str) -> dict:
    """Returns a Gemini-compatible inline_data image part."""
    if is_url(image_path):
        response = requests.get(image_path, timeout=15)
        response.raise_for_status()
        content_type = response.headers.get("Content-Type", "image/jpeg").split(";")[0].strip()
        return {"inline_data": {"mime_type": content_type, "data": response.content}}
    else:
        ext = Path(image_path).suffix.lower()
        mime_type = MEDIA_TYPE_MAP.get(ext, "image/jpeg")
        with open(image_path, "rb") as f:
            data = f.read()
        return {"inline_data": {"mime_type": mime_type, "data": data}}


# ---------------------------------------------------------------------------
# Core analysis + prompt generation
# ---------------------------------------------------------------------------

def analyze_image(model: genai.GenerativeModel, image_path: str) -> str:
    """
    Uses Gemini vision to produce a rich textual description of the animal image,
    covering: species/breed, physical appearance, coat/feathers/scales, colors,
    markings, expression, pose, environment/background, lighting, and mood.
    """
    analysis_request = (
        "You are an expert image analyst specializing in describing animals for AI art generation. "
        "Your descriptions are precise, vivid, and optimized for use as prompts in diffusion models.\n\n"
        "Carefully analyze this animal image and provide a comprehensive description covering ALL of the following:\n"
        "1. Species and breed (be specific)\n"
        "2. Physical appearance: body size/build, fur/feathers/scales texture and length\n"
        "3. Coloring and distinctive markings\n"
        "4. Facial features: eyes (color, shape, expression), ears, nose, mouth\n"
        "5. Current pose and body language\n"
        "6. Environment and background (surfaces, objects, setting)\n"
        "7. Lighting conditions (direction, quality, color temperature)\n"
        "8. Overall mood and atmosphere\n\n"
        "Write this as a single flowing paragraph optimized as an AI art prompt. "
        "Be specific and visual — avoid vague words. Do not include any preamble."
    )

    image_part = load_image_part(image_path)
    response = model.generate_content([image_part, analysis_request])
    return response.text.strip()


def generate_comfyui_prompt(
    model: genai.GenerativeModel,
    image_description: str,
    template: dict,
) -> str:
    """
    Takes the image description, invented scene, and a LoRA template,
    then generates a polished ComfyUI prompt.
    """
    trigger_word = template.get("triggerWord", "").strip()
    example_prompts = [p for p in template.get("examplePrompts", []) if p.strip()]
    example_prompt = example_prompts[0] if len(example_prompts) == 1 else None

    if len(example_prompts) > 1:
        print(f"\nMultiple example prompts available for [{template['loraName']}]:")
        for i, ep in enumerate(example_prompts):
            preview = ep[:80] + "..." if len(ep) > 80 else ep
            print(f"  [{i}] {preview}")
        while True:
            try:
                choice = int(input(f"Select example prompt [0–{len(example_prompts)-1}]: "))
                if 0 <= choice < len(example_prompts):
                    example_prompt = example_prompts[choice]
                    break
                print(f"  Enter a number between 0 and {len(example_prompts)-1}.")
            except ValueError:
                print("  Invalid input. Enter a number.")

    trigger_instruction = (
        f'1. Start the prompt with the trigger word: "{trigger_word}"'
        if trigger_word
        else "1. No trigger word — jump straight into the subject description"
    )
    trigger_line = f"- Trigger Word: {trigger_word}" if trigger_word else "- Trigger Word: (none)"

    if example_prompt:
        user_message = f"""You are an expert ComfyUI prompt engineer.

EXAMPLE PROMPT:
{example_prompt}

REPLACEMENT SUBJECT (from image):
{image_description}

TASK:
Rewrite the example prompt by intelligently substituting the main subject with the replacement subject described above. Follow these rules carefully:

1. IDENTIFY the main subject of the example prompt — this could be any entity: an animal, a person, a samurai, a creature, etc.

2. REPLACE the original subject's description with the replacement subject — include every visual detail: species/type, body build, coat/clothing/texture, coloring, markings, eye color, expression, and any distinctive features.

3. REMOVE any physical features, accessories, clothing, or props that were specific to the original subject and do not apply to the replacement (e.g. antlers on a deer, armor on a samurai, wings on a bird). Do not mention them at all. Also remove any leash, collar lead, or restraint — never include these in the output.

4. KEEP all scene elements, setting, background, lighting, atmosphere, mood, and writing style exactly as they are in the original.

5. UPDATE the tag list at the end (if present) — remove tags that described the original subject and add appropriate tags for the new subject. Keep all non-subject tags unchanged.

6. If the prompt has no identifiable main subject, insert the replacement subject naturally as the focal point without changing anything else.

{f'Keep the trigger word "{trigger_word}" at the start.' if trigger_word else ''}

Output ONLY the rewritten prompt. Nothing else."""
    else:
        user_message = f"""You are an expert ComfyUI prompt engineer generating a prompt for the "{template['loraName']}" LoRA on {template['baseModel']}.

LORA TEMPLATE:
- Base Model: {template['baseModel']}
- LoRA Name: {template['loraName']}
{trigger_line}

ANIMAL APPEARANCE (from image — preserve this likeness exactly):
{image_description}

INSTRUCTIONS:
{trigger_instruction}
2. Preserve the animal's exact appearance — breed, coat color, markings, eye color, build — do not generalize
3. Place the animal inside the scene above — setting, action, lighting, atmosphere
4. Choose an artistic style appropriate for the LoRA named "{template['loraName']}" on {template['baseModel']}
5. Do NOT include any leash, collar lead, or restraint
6. Write as a comma-separated tag list, no newlines, no explanations

Output ONLY the final prompt string. Nothing else."""

    response = model.generate_content(user_message)
    return response.text.strip()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    templates = load_templates()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("[ERROR] GEMINI_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")

    # --- Step 1: Analyze the image ---
    print(f"Analyzing image: {IMAGE_PATH}")
    image_description = analyze_image(model, IMAGE_PATH)
    print("\n--- Animal Description ---")
    print(image_description)
    print()

    # --- Step 2: Select template(s) ---
    if ALL_TEMPLATES:
        selected_templates = templates
    elif TEMPLATE_INDEX is not None:
        if TEMPLATE_INDEX < 0 or TEMPLATE_INDEX >= len(templates):
            print(f"[ERROR] TEMPLATE_INDEX {TEMPLATE_INDEX} is out of range (0–{len(templates)-1}).", file=sys.stderr)
            sys.exit(1)
        selected_templates = [templates[TEMPLATE_INDEX]]
    else:
        list_templates(templates)
        while True:
            try:
                choice = int(input(f"Select template [0–{len(templates)-1}]: "))
                if 0 <= choice < len(templates):
                    selected_templates = [templates[choice]]
                    break
                print(f"  Please enter a number between 0 and {len(templates)-1}.")
            except ValueError:
                print("  Invalid input. Enter a number.")

    # --- Step 4: Generate prompt(s) ---
    results = []
    for template in selected_templates:
        print(f"Generating prompt for [{template['loraName']}]...")
        prompt = generate_comfyui_prompt(model, image_description, template)
        results.append({"template": template, "prompt": prompt})

    # --- Output ---
    print("\n" + "=" * 60)
    print("GENERATED COMFYUI PROMPT(S)")
    print("=" * 60)
    for r in results:
        t = r["template"]
        trigger = t.get("triggerWord", "").strip() or "(none)"
        print(f"\nLoRA : {t['loraName']} ({t['baseModel']})")
        print(f"Trigger: {trigger}")
        print(f"\nPROMPT:\n{r['prompt']}")
        print("-" * 60)

    # Save to JSON when multiple prompts are generated
    if len(results) > 1 or ALL_TEMPLATES:
        out_path = Path("generated_prompts.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(
                [{"lora": r["template"]["loraName"], "baseModel": r["template"]["baseModel"], "prompt": r["prompt"]} for r in results],
                f,
                indent=2,
                ensure_ascii=False,
            )
        print(f"\nAll prompts saved to: {out_path.resolve()}")


if __name__ == "__main__":
    main()
