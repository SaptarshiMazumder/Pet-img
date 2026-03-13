"""CLI entrypoint: python -m backend.services.prompt_builder /path/to/image.png [template_key] [style_key]"""
import json
import sys

from backend.services.prompt_builder import build_animal_edo_prompt, load_style


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m backend.services.prompt_builder /path/to/image.png [template_key] [style_key]")
        raise SystemExit(1)

    image_path = sys.argv[1]
    template_key = sys.argv[2] if len(sys.argv) > 2 else "scholar_lord"
    style_key = sys.argv[3] if len(sys.argv) > 3 else "inkwash"

    style = load_style(style_key)
    result = build_animal_edo_prompt(image_path, style=style, style_key=style_key, template_key=template_key)

    print("\n=== ANIMAL DATA ===")
    print(json.dumps(result["animal_data"], indent=2, ensure_ascii=False))
    print("\n=== TEMPLATE ===")
    print(json.dumps(result["scenario_data"], indent=2, ensure_ascii=False))
    print("\n=== POSITIVE PROMPT ===")
    print(result["positive_prompt"])
    print("\n=== NEGATIVE PROMPT ===")
    print(result["negative_prompt"])


if __name__ == "__main__":
    main()
