"""
Load style and template data.
Styles: local JSON (styles.json) — rarely change, no UI to edit them.
Templates: Firestore — single source of truth, editable without redeploy.
"""
import json

from backend.config import STYLES_FILE


def load_style(style_key: str) -> dict:
    styles = json.loads(STYLES_FILE.read_text(encoding="utf-8"))
    if style_key not in styles:
        raise ValueError(f"Unknown style '{style_key}'. Available: {', '.join(styles)}")
    return styles[style_key]


def load_template(template_key: str) -> dict:
    from backend.db.templates import get
    data = get(template_key)
    if data is None:
        raise ValueError(f"Unknown template '{template_key}'.")
    return data


def load_uso_template(template_key: str) -> dict:
    from backend.db.templates import get_uso
    data = get_uso(template_key)
    if data is None:
        raise ValueError(f"Unknown USO template '{template_key}'.")
    return data
