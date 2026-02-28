"""Batch-render WhatsApp JSON definitions to JPG images for all languages."""
import json
import sys
from pathlib import Path
from wa_renderer import render_chat_image

PRINT_DIR = Path(__file__).parent

IMAGE_IDS = ["006", "012", "013", "014", "018", "026", "045", "057", "069", "070"]
LANGUAGES = ["en", "de", "ru"]


def main():
    langs = sys.argv[1:] if len(sys.argv) > 1 else LANGUAGES
    for lang in langs:
        lang_dir = PRINT_DIR / lang
        lang_dir.mkdir(exist_ok=True)
        print(f"\n=== Rendering {lang.upper()} -> {lang_dir} ===")
        for img_id in IMAGE_IDS:
            json_name = f"{img_id}_{lang}.json"
            img_name = f"{img_id}_{lang}.jpg"
            json_path = PRINT_DIR / json_name
            img_path = lang_dir / img_name
            if not json_path.exists():
                print(f"  SKIP (missing): {json_name}")
                continue
            data = json.loads(json_path.read_text(encoding="utf-8"))
            print(f"  {json_name} -> {lang}/{img_name}")
            render_chat_image(data, str(img_path), width=420)
    print("\nDone.")


if __name__ == "__main__":
    main()
