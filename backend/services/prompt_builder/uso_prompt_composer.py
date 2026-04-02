"""
Prompt composer for the USO (Flux1-Dev style-transfer) workflow.
Same composition as ZTurbo — subject described in the scene with full pose/environment/mood —
but without style trigger word, wardrobe, or style suffix.
"""
from backend.services.prompt_builder.animal_image_analysis import extract_animal_appearance
from backend.services.prompt_builder.prompt_composer import compose_final_prompt


def compose_uso_prompt(template: dict, subject_image_path: str) -> str:
    animal_data = extract_animal_appearance(subject_image_path)
    # Empty style: no trigger word, no wardrobe, no style suffix
    return compose_final_prompt(animal_data, template, style={})
