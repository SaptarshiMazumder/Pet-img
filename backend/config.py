from pathlib import Path

BACKEND_DIR   = Path(__file__).parent
ROOT_DIR      = BACKEND_DIR.parent

TEMPLATES_FILE        = BACKEND_DIR / "templates.json"
ASSETS_DIR            = BACKEND_DIR / "assets"
STYLES_FILE           = ROOT_DIR    / "styles.json"
NEGATIVE_PROMPTS_FILE = ROOT_DIR    / "negative_prompts.json"
