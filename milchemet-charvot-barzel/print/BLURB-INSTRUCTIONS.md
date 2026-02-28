# Printing with Blurb -- חרבות ברזל, יומן מהעורף

## Book Specs

| Spec | Value |
|---|---|
| Format | Photo Book, Standard Portrait |
| Size | 8 x 10 inches (20 x 25 cm) |
| Cover | Hardcover ImageWrap |
| Paper | Mohawk proPhoto Pearl (190 GSM, semi-gloss) |
| Pages | 124 (even, within 20-240 range) |
| Images | 111 embedded |
| Fonts | David, Gisha (embedded in PDF) |
| Interior PDF | `book.pdf` (32.9 MB) |
| Estimated cost | ~$122 book + ~$15-20 shipping to Israel = **~$140 USD** |

## Rebuild the Interior PDF

If you edit `README.md` or `print.css`, rebuild with:

```powershell
powershell -ExecutionPolicy Bypass -File "d:\dev\blog\milchemet-charvot-barzel\print\build.ps1"
```

Pipeline: `README.md` → Pandoc → `book.html` → Playwright/Chromium → `book.pdf`

Prerequisites: Pandoc, Python, Playwright (`pip install playwright && python -m playwright install chromium`).

## Upload to Blurb

1. Go to [blurb.com/pdf-to-book](https://www.blurb.com/pdf-to-book)
2. Select **Photo Book** > **Standard Portrait 8x10**
3. Select **Hardcover ImageWrap**
4. Select **Mohawk proPhoto Pearl** paper
5. Upload `book.pdf` as the interior

## Create the Cover

Blurb provides the exact cover template (with spine width calculated from your page count and paper choice) **after** you upload the interior PDF. You do not need to calculate dimensions yourself.

Options:

- **Blurb's built-in cover tool** -- place text and an image directly in their web editor. Simplest.
- **Canva** -- download Blurb's cover template dimensions after upload, create in Canva, export as PDF with bleed marks.
- **Manual** -- use one of the blog's photos as background, overlay the title in Hebrew. Tools: GIMP, Photoshop, or Canva.

Cover content:

| Panel | Content |
|---|---|
| Front | Title, author, optional photo |
| Spine | Title + author (Blurb calculates spine width) |
| Back | Synopsis, optional author photo |

## Preview and Order

1. Blurb shows a digital proof before payment -- review it carefully
2. Check: first/last page, image placement, margins, Hebrew text rendering
3. **Order 1 proof copy first** before ordering multiples
4. When the physical copy arrives, review print quality, color accuracy, binding

## CSS Tuning Reference

Key values in `print.css` you may want to adjust after reviewing the proof:

| Property | Current | Effect |
|---|---|---|
| `@page { size }` | `8in 10in` | Page dimensions (must match Blurb format) |
| `@page { margin }` | `13mm outer, 19mm gutter` | Margins; gutter = binding side |
| `body { font-size }` | `12pt` | Body text size |
| `img { max-height }` | `190mm` | Maximum image height per page |
| `h2 { page-break-before }` | `always` | Each diary day starts on a new page |
| `.cover-page h1 { font-size }` | `34pt` | Title on interior cover page |

## Why These Tools

| Tool | Role | Why |
|---|---|---|
| **Pandoc** | Markdown → HTML | Handles YAML front-matter, headings, image refs, CSS linking |
| **Playwright** | HTML → PDF | Headless Chromium; handles RTL, Hebrew fonts, `@page` CSS natively on Windows |
| ~~WeasyPrint~~ | *(abandoned)* | Requires GTK3 native libs on Windows -- installation fails |
| ~~LaTeX~~ | *(abandoned)* | Pandoc bug: images break in RTL PDF via XeLaTeX |

## File Inventory

```
milchemet-charvot-barzel/
  README.md              # Source Markdown (Hebrew, RTL)
  images/                # 111 downloaded images (001.jpg - 111.jpg)
  print/
    print.css            # Print stylesheet (8x10, RTL, David font)
    build.ps1            # Build script (Pandoc + Playwright)
    html_to_pdf.py       # Playwright PDF converter
    book.html            # Intermediate HTML (generated)
    book.pdf             # Final print-ready PDF (generated)
    BLURB-INSTRUCTIONS.md  # This file
```
