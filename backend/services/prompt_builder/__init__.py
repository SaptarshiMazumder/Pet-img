"""
Prompt builder — animal analysis (Gemini) + template composition.
Builds the portrait prompt from pet image, style, and template.
"""
from backend.services.prompt_builder.style_template_loader import load_style, load_template
from backend.services.prompt_builder.animal_image_analysis import extract_animal_appearance
from backend.services.prompt_builder.prompt_composer import compose_final_prompt


def build_animal_edo_prompt(
    image_path: str,
    style: dict,
    style_key: str,
    template_key: str,
) -> dict:
    """Build full portrait prompt from pet image, style, and template."""
    animal_data = extract_animal_appearance(image_path)
    template = load_template(template_key)
    final_prompt = compose_final_prompt(animal_data, template, style)

    return {
        "animal_data": animal_data,
        "scenario_data": template,
        "positive_prompt": final_prompt,
        "negative_prompt": "",  # Z-turbo works better without negative prompts
    }


__all__ = [
    "build_animal_edo_prompt",
    "load_style",
    "load_template",
    "extract_animal_appearance",
    "compose_final_prompt",
]
