---
name: wix-blog-export
description: Export a Wix blog post to a local Markdown file with downloaded images, translate to multiple languages with localized WhatsApp screenshot rendering, and generate print-ready PDFs. Use when the user provides a Wix blog URL and wants to persist it as Markdown, export from Wix, save a Wix post locally, convert Wix to git-friendly format, translate WhatsApp screenshots, or generate multilingual book PDFs.
---

# Wix Blog Post Export

Export a published Wix blog post (URL) to a self-contained Markdown folder with locally downloaded images.

## Output Structure

```
<output-dir>/<post-slug>/
  he/
    readme.md
  images/
    001.jpg
    002.png
    ...
```

## Execution Model

**Use subagents for all heavy work.** The parent conversation should only:
1. Resolve parameters (URL, output location)
2. Launch subagents
3. Report results to the user

This prevents Cursor crashes from context bloat during long exports.

### Subagent Breakdown

| Subagent | Type | Task |
|---|---|---|
| **Fetch & Analyze** | `shell` | Download raw HTML, extract metadata, build ordered image list, build block map. Write results to temp files. |
| **Download Images** | `shell` | Read image list from temp file, download all images in batches. |
| **Build Markdown** | `generalPurpose` | Read WebFetch text + block map + image list, assemble final `he/readme.md`. |
| **Verify** | `generalPurpose` | Count image refs vs files, check all refs resolve, show summary. |

For posts with few images (<10), a single `generalPurpose` subagent can handle the entire export. For posts with many images (10+), split into the subagents above.

When exporting **multiple posts**, launch them in parallel (up to 4 concurrent subagents).

---

## Workflow

### Step 1: Resolve Output Location (parent)

Ask the user where to save if not specified. Default: `d:\dev\blog\<post-slug>\`.
Derive `<post-slug>` from the URL path (the last segment, URL-decoded, transliterated to ASCII-safe if needed).

### Step 2: Fetch & Analyze (subagent: `shell`)

Launch a shell subagent with these instructions:

**Pass A -- Text content:** Use `WebFetch` on the URL. This returns readable text (the post body) but NO image URLs (Wix renders images via client-side JS). Save to `<temp>_text.txt`.

**Pass B -- Raw HTML source:** Download the raw HTML:

```powershell
curl.exe -s -L -o <temp>.html "<URL>"
```

**Extract metadata** from the JSON-LD block (`<script type="application/ld+json">`):

| Field | JSON-LD key |
|---|---|
| title | `headline` |
| author | `author.name` |
| published | `datePublished` |
| updated | `dateModified` |

Also check `<meta property="og:image">` for the cover image URL. Write metadata to `<temp>_meta.txt`.

**Extract ALL image blocks** from the HTML. Wix blog posts use numbered content blocks: `data-hook="rcv-block<N>"`. Images appear in **two distinct container types** -- both must be captured:

**Type A: Standard images** (`image-viewer` / `wix-image`) -- single images in `rcv-block` elements.

**Type B: Pro Gallery images** (`gallery-item-image`) -- multiple images inside a Wix Pro Gallery widget. These use `data-hook="gallery-item-image-img-preload"` and do NOT contain `image-viewer` or `wix-image`. A single `rcv-block` can contain an entire gallery with many images.

Iterate through each block individually:

```powershell
$html = [System.IO.File]::ReadAllText('<temp>.html', [System.Text.Encoding]::UTF8)
$siteId = ([regex]::Match($html, '(\d{4,8})_[a-f0-9]+~mv2\.\w+')).Groups[1].Value
$maxBlock = ([regex]::Matches($html, 'data-hook="rcv-block(\d+)"') |
    ForEach-Object { [int]$_.Groups[1].Value } | Measure-Object -Maximum).Maximum
$imgNum = 1
for ($blk = 1; $blk -le $maxBlock; $blk++) {
    $pattern = "data-hook=`"rcv-block${blk}`"[^>]*>([\s\S]*?)(?=data-hook=`"rcv-block)"
    $m = [regex]::Match($html, $pattern)
    if (-not $m.Success) { continue }
    $content = $m.Groups[1].Value

    # Type A: standard image-viewer / wix-image
    if ($content -match 'image-viewer|wix-image') {
        $imgMatch = [regex]::Match($content, "${siteId}_[a-f0-9]+~mv2\.\w+")
        if ($imgMatch.Success) { # Record: imgNum, blockNum, Type=A, mediaId }
        $imgNum++
    }

    # Type B: pro-gallery images
    if ($content -match 'gallery-item-image') {
        $galleryImgs = [regex]::Matches($content, "${siteId}_[a-f0-9]+~mv2\.\w+")
        $seen = @{}
        foreach ($gi in $galleryImgs) {
            if (-not $seen.ContainsKey($gi.Value)) {
                $seen[$gi.Value] = $true
                # Record: imgNum, blockNum, Type=B, mediaId
                $imgNum++
            }
        }
    }
}
```

Write the ordered image list to `<temp>_images.txt` (one line per image: `NNN|blockNum|type|mediaId|ext`).

**Build block map:** Walk all blocks in order and classify each as TEXT, HEADING, QUOTE, IMG, or EMPTY. Write to `<temp>_blockmap.txt`.

**For each image block**, find the nearest non-empty text block before and after for placement anchoring.

The subagent should return: total image count, metadata summary, and paths to all temp files.

### Step 3: Download Images (subagent: `shell`)

Launch a shell subagent that reads `<temp>_images.txt` and downloads all images:

```powershell
curl.exe -s -L -o images/001.jpg "https://static.wixstatic.com/media/<mediaId>"
```

Use 3-digit zero-padded filenames. Batch downloads in groups of ~20. Verify all files have non-zero size.

### Step 4: Build Markdown (subagent: `generalPurpose`)

Launch a generalPurpose subagent that:

1. Reads metadata from `<temp>_meta.txt`
2. Reads the WebFetch text content
3. Reads the block map from `<temp>_blockmap.txt`
4. Reads the image list from `<temp>_images.txt`

Creates `he/readme.md` with:

**YAML front-matter:**

```yaml
---
title: "<title>"
author: "<author>"
date: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
lang: he       # adjust per post language
dir: rtl       # adjust per post language
original_url: "<full Wix URL>"
---
```

**Body:** Walk the block map in order. For each entry:
- **TXT blocks**: Convert to markdown paragraphs. Detect headings (`<div type="heading"`), blockquotes (`<div type="blockquote"`), and empty lines.
- **IMG blocks**: Insert `![](../images/<NNN>.<ext>)`. For gallery blocks with multiple images, insert consecutive image references.

Formatting rules:
- Preserve all paragraph breaks
- Use `##` for headings, `>` for blockquotes
- Bold text: `**bold text**`
- Timestamps in bold: `**16:25. text...**`

### Step 5: Clean Up & Verify (subagent: `generalPurpose`)

Launch a generalPurpose subagent that:
1. Deletes all temp files (`<temp>.html`, `<temp>_*.txt`)
2. Counts `![](../images/...)` references in the markdown
3. Verifies each reference resolves to an existing file
4. Lists the output directory with file sizes
5. Returns a summary

---

---

## Multi-Language Translation

Translate the exported Hebrew post into additional languages (EN, DE, RU, etc.).

### Rules

1. **Each language gets its own top-level folder**: `<lang>/` (e.g., `he/`, `en/`, `de/`, `ru/`) -- all languages are symmetrical peers
2. **Markdown is always `readme.md`**: every language folder contains `readme.md` -- not `book-en.md`, not `book.md`, always `readme.md`
3. **Translated WhatsApp images live in the language folder**: rendered JPGs sit alongside their `readme.md` (e.g., `en/006_en.jpg`)
4. **Shared images stay in `images/`**: photos, infographics, and any image that doesn't contain translatable text remains in the common `images/` folder and is referenced via `../images/NNN.ext` from any language folder (preserving original extension)
5. **WhatsApp JSON definitions live in `print/`**: one JSON per WA image per language (e.g., `print/006_en.json`, `print/006_de.json`)
6. **Never modify the original `images/` folder**: it holds the Hebrew originals; translated versions go in language folders

### Directory Structure

```
<post-slug>/
  images/                # Shared images (photos, infographics) -- NEVER modified
    001.jpg              # Photo -- shared by all languages
    006.jpg              # Hebrew WhatsApp screenshot (original, .jpg)
    058.png              # Hebrew WhatsApp screenshot (original, .png)
    ...
  print/                 # Build tools + WhatsApp JSON definitions only
    wa_renderer.py       # WhatsApp chat image renderer (Playwright-based)
    render_all_en.py     # Batch render script: outputs to <root>/<lang>/
    postprocess_html.py  # HTML image grid post-processor
    html_to_pdf.py       # Playwright HTML-to-PDF converter
    build-lang.ps1       # PDF build script for translated languages
    print-ltr.css        # LTR print stylesheet
    build.ps1            # PDF build script for Hebrew original
    print.css            # RTL print stylesheet (Hebrew)
    006_en.json          006_de.json          006_ru.json
    012_en.json          012_de.json          012_ru.json
    ...
  he/
    readme.md            # Hebrew original source
  en/
    readme.md            # English book text
    006_en.jpg           # Rendered English WhatsApp images
    012_en.jpg
    ...
    book-en.pdf          # Generated PDF (build output)
  de/
    readme.md            # German book text
    006_de.jpg
    ...
  ru/
    readme.md            # Russian book text
    006_ru.jpg
    ...
```

### How to Translate a Post

**Step 1 -- Translate the markdown:**
Copy the Hebrew `he/readme.md`, translate all text to the target language, and save as `<lang>/readme.md`. Update the YAML front-matter:

```yaml
---
title: "Translated Title"
author: "Author Name"
date: 2023-10-07
lang: en        # en / de / ru
dir: ltr        # always ltr for EN/DE/RU
subtitle: "Translated Subtitle"
original_url: "<original Wix URL>"
---
```

**Step 2 -- Classify ALL images (both JPG and PNG):**
Read every image from `images/` regardless of extension and classify. Chat screenshots can be either `.jpg` or `.png` -- do not skip PNGs.

| Category | Action | Example |
|---|---|---|
| **PHOTO** | Keep as-is, reference shared `../images/NNN.ext` | Selfies, landscapes, documents |
| **WA** (WhatsApp chat) | Translate and render per language | Dark-mode chat screenshots with Hebrew text |
| **MESSENGER** (FB/Telegram) | Translate and render as WA style | Other chat apps with Hebrew text |
| **INFOGRAPHIC** | Keep or translate separately | Charts, data visualizations |
| **SCREENSHOT** (already English) | Keep as-is | English app screenshots, English-only chats |

**Step 3 -- Transcribe and translate chat images:**
For each WA or MESSENGER image:
1. Read the original Hebrew image visually
2. Identify every message: sender, side (left=received, right=sent), text, time, features (quotes, forwarded, edited, reactions)
3. Create a JSON file per language in `print/` (e.g., `print/012_en.json`, `print/012_de.json`, `print/012_ru.json`)

**Step 4 -- Render translated WhatsApp images:**

```powershell
cd <post-slug>/print
python render_all_en.py            # all languages
python render_all_en.py en         # just English
python render_all_en.py de ru      # just German and Russian
```

Images are rendered directly into each language folder (e.g., `en/012_en.jpg`).

**Step 5 -- Update image references in `readme.md`:**
For each translated chat image, change the reference from the shared original to the local rendered version. The original may be `.jpg` or `.png`; the rendered version is always `.jpg`:

```markdown
# Before (shared Hebrew original -- can be .jpg or .png):
![](../images/006.jpg)
![](../images/058.png)

# After (local rendered version -- always .jpg):
![](006_en.jpg)
![](058_en.jpg)
```

Non-chat images keep their shared path regardless of extension: `![](../images/001.jpg)`, `![](../images/046.png)`

### WhatsApp Translation Conventions

| Element | EN | DE | RU |
|---|---|---|---|
| Sender names | Transliterate Hebrew (Sapir Eden _) | Same as EN | Cyrillic (Сапир Эден _) |
| Group names | Translate meaning (Brothers of the Farm) | Translate (Brüder des Bauernhofs) | Translate (Братья фермы) |
| Status "online" | online | online | в сети |
| Quote sender "You" | You | Du | Ты |
| "Forwarded" label | ↪ Forwarded (built-in) | ↪ Forwarded (built-in) | ↪ Forwarded (built-in) |
| Timestamps | Keep original | Keep original | Keep original |
| Phone numbers | Keep original | Keep original | Keep original |
| `direction` field | `"ltr"` | `"ltr"` | `"ltr"` |
| Poll hint | Select one | Eine auswählen | Выберите один |
| System messages | Translate | Translate | Translate |

### WhatsApp JSON Format

Each JSON file defines one WhatsApp chat screenshot:

```json
{
  "chat_name": "Contact Name _",
  "chat_status": "online",
  "direction": "ltr",
  "avatar_icon": "&#128101;",
  "footer": false,
  "messages": [
    {"side": "right", "text": "Sent message", "time": "18:31", "check": "\u2713\u2713"},
    {"side": "left", "sender": "Name _", "text": "Received message", "time": "18:39"},
    {"side": "left", "quote": {"sender": "You", "text": "Quoted text"}, "text": "Reply to quote", "time": "18:45"},
    {"side": "left", "forwarded": true, "text": "Forwarded content", "time": "22:24"},
    {"side": "right", "text": "Edited message", "time": "09:58", "check": "\u2713\u2713", "edited": true},
    {"side": "left", "sender": "~ name", "sender_phone": "+972 52-865-2788", "text": "Group msg", "time": "23:56"},
    {"side": "left", "text": "Message with reaction", "time": "22:35", "reaction": "\u2764\ufe0f"},
    {"type": "spacer"},
    {"type": "system", "text": "Someone joined using this group's invite link"},
    {"type": "date", "text": "Today"},
    {"type": "unread", "text": "1 Unread Message"},
    {"type": "poll", "sender": "~ Anat Nee...", "sender_phone": "+972 50-565-0129",
     "question": "Poll question?", "hint": "Select one",
     "options": [{"label": "Yes", "votes": 0}, {"label": "No", "votes": 30, "selected": true}],
     "time": "20:27"}
  ]
}
```

**Message fields:** `side` (left/right), `check` (✓✓ read receipts), `quote` (reply block), `forwarded`, `edited`, `sender_phone`, `reaction`. **Special types:** `spacer`, `system`, `date`, `unread`, `poll`.

### Rendering Commands

```powershell
# Single image (from print/ directory)
python wa_renderer.py 006_en.json ../en/006_en.jpg [width=420]

# Batch render all languages (outputs to <root>/<lang>/)
python render_all_en.py             # en, de, ru
python render_all_en.py de ru       # specific languages only
```

---

## Print-Ready PDF Generation

Generate print-ready PDFs for book printing services (BookPod, Blurb, etc.). Directory structure is defined in the Multi-Language Translation section above.

### Prerequisites

- **Pandoc** (already installed for export): converts Markdown to HTML
- **Python + Playwright**: `pip install playwright` then `python -m playwright install chromium`
- Hebrew system fonts: David, Gisha, or similar

### How it works

The `build.ps1` script is fully generic and works from any post's `print/` directory:

1. Extracts title, author, date from `he/readme.md` YAML front-matter
2. Generates a cover page HTML fragment
3. Runs Pandoc to convert `he/readme.md` -> `book.html` with `print.css` linked
4. Fixes image/CSS paths to absolute (Playwright needs this)
5. Runs Playwright headless Chromium to convert `book.html` -> `book.pdf`

### Build commands

```powershell
# Hebrew original (RTL) -- reads he/readme.md
powershell -ExecutionPolicy Bypass -File "<post-slug>\print\build.ps1"

# Translated language (LTR) -- reads readme.md from top-level language folder
powershell -ExecutionPolicy Bypass -File "<post-slug>\print\build-lang.ps1" -Lang en -SourceMd "<post-slug>\en\readme.md"
powershell -ExecutionPolicy Bypass -File "<post-slug>\print\build-lang.ps1" -Lang de -SourceMd "<post-slug>\de\readme.md"
powershell -ExecutionPolicy Bypass -File "<post-slug>\print\build-lang.ps1" -Lang ru -SourceMd "<post-slug>\ru\readme.md"
```

### Key CSS design decisions

- **Page size**: A5 (148x210mm) -- standard for BookPod; change to 8x10in for Blurb
- **Margins**: 15mm inner (binding gutter), 12mm outer/top/bottom
- **Images**: `max-width: 100%`, `max-height: 130mm`, centered, `page-break-inside: avoid`
- **Section headings** (`h2`): `page-break-before: always` so each diary day starts on a new page
- **Font**: David at 11pt, RTL direction
- **Cover page**: Title + author + date, full-page, `page-break-after: always`
- **First h1 suppressed**: Already shown on cover page

### Why Playwright instead of WeasyPrint

WeasyPrint requires GTK3 native libraries on Windows (complex setup). Playwright uses headless Chromium which handles RTL, images, and `@page` CSS natively with zero extra dependencies beyond `pip install playwright`.

### Why not LaTeX

Pandoc has a [documented bug](https://github.com/jgm/pandoc/issues/10611) where images break in RTL PDF output via XeLaTeX.

### Generating for multiple posts

The `print.css`, `build.ps1`, and `html_to_pdf.py` files are identical across all posts -- copy them to each post's `print/` directory and run `build.ps1`. Use subagents to build multiple PDFs in parallel.

### Full translation + PDF workflow

1. Translate Hebrew `he/readme.md` -> `<lang>/readme.md` for each target language
2. Classify ALL images (both .jpg and .png): WA/MESSENGER (translate) vs PHOTO (keep shared) vs other
3. Transcribe each WA image, create JSON files in `print/` (`NNN_<lang>.json`)
4. Run `python render_all_en.py` -- outputs images to `<lang>/NNN_<lang>.jpg`
5. In each `readme.md`, chat refs use local `NNN_<lang>.jpg` (always .jpg), non-chat refs keep shared `../images/NNN.ext` (original extension)
6. Run `build-lang.ps1 -Lang <lang> -SourceMd <lang>/readme.md` per language

---

## Caveats

- **Client-side rendering**: Wix loads images via JS. The `WebFetch` text pass will never contain image URLs. Always do the raw HTML pass.
- **Two image container types**: Wix uses BOTH `image-viewer`/`wix-image` (single images) AND `gallery-item-image` (Pro Gallery widgets with multiple images). You MUST detect both types or you will miss images. The gallery type does NOT contain `image-viewer` or `wix-image` in its markup.
- **Block-based extraction is critical**: Do NOT extract image IDs globally and then classify. Instead, find image containers within each `rcv-block` -- this avoids including unrelated thumbnails (Recent Posts, nav) and correctly captures gallery images in order.
- **Gallery deduplication**: Within a single gallery block, the same image ID appears multiple times (for srcset/responsive variants). Deduplicate by ID within each block, but keep the order.
- **Image quality**: The base media URL without resize parameters returns the uploaded original.
- **Hebrew / RTL**: Set `lang: he` and `dir: rtl` in front-matter for Hebrew posts.
- **Encoding**: Use UTF-8 without BOM for all output files. On Windows PowerShell, use `[System.IO.File]::WriteAllText()` with `UTF8Encoding($false)`. Read HTML with `[System.IO.File]::ReadAllText('<file>', [System.Text.Encoding]::UTF8)`.
- **Performance**: For posts with many images (50+), use PowerShell-native regex instead of ripgrep to avoid shell escaping issues. Batch image downloads in groups.
- **Windows PowerShell**: Use `curl.exe` (not `curl` which aliases to `Invoke-WebRequest`). Use `;` not `&&` to chain commands.
- **Context management**: All heavy I/O (HTML parsing, image downloading, markdown assembly) MUST run inside subagents to prevent parent conversation context from growing too large and causing Cursor crashes.
