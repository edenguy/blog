import sys
from pathlib import Path
from playwright.sync_api import sync_playwright


def main():
    html_path = Path(sys.argv[1]).resolve()
    pdf_path = Path(sys.argv[2]).resolve()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(html_path.as_uri())
        page.wait_for_load_state("networkidle")
        page.pdf(
            path=str(pdf_path),
            print_background=True,
            prefer_css_page_size=True,
        )
        browser.close()

    size_mb = pdf_path.stat().st_size / (1024 * 1024)
    print(f"PDF written: {pdf_path} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
