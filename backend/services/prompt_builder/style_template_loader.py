"""
Load style and template data from config files.
"""
import json

from backend.config import STYLES_FILE, TEMPLATES_FILE


def load_style(style_key: str) -> dict:
    styles = json.loads(STYLES_FILE.read_text(encoding="utf-8"))
    if style_key not in styles:
        raise ValueError(f"Unknown style '{style_key}'. Available: {', '.join(styles)}")
    return styles[style_key]


def load_template(template_key: str) -> dict:
    templates = json.loads(TEMPLATES_FILE.read_text(encoding="utf-8"))
    if template_key not in templates:
        raise ValueError(f"Unknown template '{template_key}'. Available: {', '.join(templates)}")
    return templates[template_key]
