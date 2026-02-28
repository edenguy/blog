"""Batch-render all English WhatsApp JSON definitions to JPG images."""
import json
from pathlib import Path
from wa_renderer import render_chat_image

PRINT_DIR = Path(__file__).parent
IMAGES_DIR = PRINT_DIR.parent / "images"

JOBS = [
    ("006_en.json", "006_en.jpg"),
    ("012_en.json", "012_en.jpg"),
    ("013_en.json", "013_en.jpg"),
    ("014_en.json", "014_en.jpg"),
    ("018_en.json", "018_en.jpg"),
    ("026_en.json", "026_en.jpg"),
    ("045_en.json", "045_en.jpg"),
    ("057_en.json", "057_en.jpg"),
    ("069_en.json", "069_en.jpg"),
    ("070_en.json", "070_en.jpg"),
]


def main():
    IMAGES_DIR.mkdir(exist_ok=True)
    for json_name, img_name in JOBS:
        json_path = PRINT_DIR / json_name
        img_path = IMAGES_DIR / img_name
        if not json_path.exists():
            print(f"SKIP (missing): {json_name}")
            continue
        data = json.loads(json_path.read_text(encoding="utf-8"))
        print(f"Rendering {json_name} -> {img_path}")
        render_chat_image(data, str(img_path), width=420)


if __name__ == "__main__":
    main()
