"""
Tests for compose_final_prompt — the function that assembles the text prompt
sent to the image model. Bugs here silently produce malformed prompts and
bad generations, so this is high-value logic to lock down.
"""
from backend.services.prompt_builder.prompt_composer import compose_final_prompt


def _template():
    return {
        "role_title": "a samurai warrior",
        "wardrobe": "ornate {species} armor",
        "attire_verb": "wears",
        "pose_sentence": "{pronoun} stands ready for battle",
        "props_sentence": "A katana rests at its side.",
        "environment": "a misty castle courtyard",
        "lighting": "Golden light falls across {pronoun}.",
        "mood": "proud and fearless",
    }


def _style():
    return {"trigger_word": "TRG", "suffix": "oil painting, masterpiece"}


def test_placeholders_are_replaced():
    """{pronoun} and {species} must be substituted with real values, never left literal."""
    animal = {"subject_phrase": "A noble dog", "species": "dog", "pronoun": "He"}
    prompt = compose_final_prompt(animal, _template(), _style())

    assert "{pronoun}" not in prompt, "left an unreplaced {pronoun} placeholder"
    assert "{species}" not in prompt, "left an unreplaced {species} placeholder"
    assert "dog armor" in prompt          # {species} -> dog
    assert "he stands ready" in prompt    # {pronoun} -> he (lowercased by the composer)


def test_trigger_word_is_prepended():
    """When a style has a trigger word, the prompt must start with it."""
    animal = {"subject_phrase": "A noble dog", "species": "dog", "pronoun": "he"}
    prompt = compose_final_prompt(animal, _template(), _style())
    assert prompt.startswith("TRG A noble dog")


def test_missing_trigger_word_has_no_leading_space():
    """No trigger word -> prompt starts cleanly with the subject, no stray space."""
    animal = {"subject_phrase": "A noble dog", "species": "dog", "pronoun": "he"}
    prompt = compose_final_prompt(animal, _template(), {"trigger_word": "", "suffix": ""})
    assert prompt.startswith("A noble dog")


def test_optional_clauses_are_dropped_when_empty():
    """Empty wardrobe/props must not leave dangling 'It wears .' fragments."""
    template = _template()
    template["wardrobe"] = ""
    template["props_sentence"] = ""
    animal = {"subject_phrase": "A noble dog", "species": "dog", "pronoun": "he"}
    prompt = compose_final_prompt(animal, template, _style())
    assert "It wears" not in prompt
    assert "katana" not in prompt


def test_defaults_used_when_animal_data_is_empty():
    """Given no animal data, the composer should fall back to safe defaults, not crash."""
    prompt = compose_final_prompt({}, _template(), _style())
    assert "A stoic animal" in prompt   # subject_phrase default
    assert "portrayed as a samurai warrior" in prompt
