from pathlib import Path

BACKEND_DIR = Path(__file__).parent.parent  # backend/ root

TEMPLATES_FILE = BACKEND_DIR / "templates.json"
STYLES_FILE    = BACKEND_DIR / "styles.json"
ASSETS_DIR     = BACKEND_DIR / "assets"
