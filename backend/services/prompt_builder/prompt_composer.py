"""
Prompt composer — assemble the final portrait prompt from animal data, template, and style.
"""


def _fill_placeholders(s: str, *, pronoun: str, species: str) -> str:
    return s.replace("{pronoun}", pronoun).replace("{species}", species)


def compose_final_prompt(animal_data: dict, template: dict, style: dict) -> str:
    """
    Assemble: [trigger] [subject_phrase], portrayed as [role_title]. [face] It wears [wardrobe]. [pose]. [props] Setting. Lighting. Mood. [style_suffix]
    Template fields can contain {pronoun} and {species}; we replace them.
    """
    trigger = (style.get("trigger_word") or "").strip()
    style_suffix = (style.get("suffix") or "").strip()

    subject_phrase = animal_data.get("subject_phrase", "A stoic animal").strip()
    face_sentence = animal_data.get("face_sentence", "").strip()
    species = animal_data.get("species", "animal").strip()
    pronoun = animal_data.get("pronoun", "animal").strip().lower()

    role_title = template.get("role_title", "").strip()
    wardrobe = template.get("wardrobe", "").strip()
    attire_verb = template.get("attire_verb", "wears").strip()
    pose_sentence = template.get("pose_sentence", "").strip()
    props_sentence = (template.get("props_sentence") or "").strip()
    environment = template.get("environment", "").strip()
    lighting = template.get("lighting", "").strip()
    mood = template.get("mood", "").strip()

    pose_sentence = _fill_placeholders(pose_sentence, pronoun=pronoun, species=species)
    lighting = _fill_placeholders(lighting, pronoun=pronoun, species=species)
    wardrobe = _fill_placeholders(wardrobe, pronoun=pronoun, species=species)

    subject_line = f"{trigger} {subject_phrase}".strip() if trigger else subject_phrase
    parts = [
        f"{subject_line}, portrayed as {role_title}.",
        face_sentence,
        f"It {attire_verb} {wardrobe}.",
        pose_sentence,
    ]
    if props_sentence:
        parts.append(props_sentence)
    parts.append(f"The setting is {environment}.")
    parts.append(lighting)
    parts.append(f"The mood feels {mood}.")
    parts.append(style_suffix)

    return " ".join(p.strip() for p in parts if p.strip())
