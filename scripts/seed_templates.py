"""
One-time script to seed Firestore with templates from the local JSON files.
Run from the project root:
  python -m scripts.seed_templates
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / "backend" / ".env")

from backend.firebase import get_db

BACKEND_DIR = Path(__file__).parent.parent / "backend"


def seed(collection: str, json_file: Path):
    db = get_db()
    data = json.loads(json_file.read_text(encoding="utf-8"))
    batch = db.batch()
    for key, value in data.items():
        ref = db.collection(collection).document(key)
        batch.set(ref, value)
    batch.commit()
    print(f"Seeded {len(data)} documents into '{collection}'")


if __name__ == "__main__":
    seed("templates",     BACKEND_DIR / "templates.json")
    seed("templates_uso", BACKEND_DIR / "templates_uso.json")
    print("Done.")
