---
name: wix-blog-export
description: Export a Wix blog post to a local Markdown file with downloaded images. Use when the user provides a Wix blog URL and wants to persist it as Markdown, export from Wix, save a Wix post locally, or convert Wix to git-friendly format.
---

# Wix Blog Post Export

Export a published Wix blog post (URL) to a self-contained Markdown folder with locally downloaded images.

## Output Structure

```
<output-dir>/<post-slug>/
  README.md
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
| **Build Markdown** | `generalPurpose` | Read WebFetch text + block map + image list, assemble final `README.md`. |
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

Creates `README.md` with:

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
- **IMG blocks**: Insert `![](images/<NNN>.<ext>)`. For gallery blocks with multiple images, insert consecutive image references.

Formatting rules:
- Preserve all paragraph breaks
- Use `##` for headings, `>` for blockquotes
- Bold text: `**bold text**`
- Timestamps in bold: `**16:25. text...**`

### Step 5: Clean Up & Verify (subagent: `generalPurpose`)

Launch a generalPurpose subagent that:
1. Deletes all temp files (`<temp>.html`, `<temp>_*.txt`)
2. Counts `![](images/...)` references in the markdown
3. Verifies each reference resolves to an existing file
4. Lists the output directory with file sizes
5. Returns a summary

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
