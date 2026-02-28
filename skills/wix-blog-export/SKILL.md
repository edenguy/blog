---
name: wix-blog-export
description: Export a Wix blog post to a local Markdown file with downloaded images. Use when the user provides a Wix blog URL and wants to persist it as Markdown, export from Wix, save a Wix post locally, or convert Wix to git-friendly format.
---

# Wix Blog Post Export

Export a published Wix blog post (URL) to a self-contained Markdown folder with locally downloaded images.

## Output Structure

```
<output-dir>/<post-slug>/
  index.md
  images/
    01.jpg
    02.png
    ...
```

## Workflow

### Step 1: Resolve Output Location

Ask the user where to save if not specified. Default: `d:\dev\Guy\blog\<post-slug>\`.
Derive `<post-slug>` from the URL path (the last segment, URL-decoded, transliterated to ASCII-safe if needed).

### Step 2: Fetch Page Content (Two Passes)

**Pass A -- Text content:** Use `WebFetch` on the URL. This returns readable text (the post body) but NO image URLs (Wix renders images via client-side JS).

**Pass B -- Raw HTML source:** Download the raw HTML for image and structure extraction:

```powershell
curl -s -L -o <temp>.html "<URL>"
```

### Step 3: Extract Post Metadata

Search the raw HTML for the JSON-LD block (`<script type="application/ld+json">`). Extract:

| Field | JSON-LD key |
|---|---|
| title | `headline` |
| author | `author.name` |
| published | `datePublished` |
| updated | `dateModified` |

Also check `<meta property="og:image">` for the cover image URL.

### Step 4: Extract Image Blocks from HTML

Wix blog posts use numbered content blocks: `data-hook="rcv-block<N>"`. Images appear inside blocks that contain `image-viewer` or `wix-image` elements.

**Critical:** Do NOT use a single regex that spans across block boundaries. Instead, iterate through each block individually and check if it contains an image:

```powershell
$html = [System.IO.File]::ReadAllText('<temp>.html', [System.Text.Encoding]::UTF8)
$maxBlock = ([regex]::Matches($html, 'data-hook="rcv-block(\d+)"') |
    ForEach-Object { [int]$_.Groups[1].Value } | Measure-Object -Maximum).Maximum
$imgNum = 1
for ($blk = 1; $blk -le $maxBlock; $blk++) {
    $pattern = "data-hook=`"rcv-block${blk}`"[^>]*>([\s\S]*?)(?=data-hook=`"rcv-block)"
    $m = [regex]::Match($html, $pattern)
    if (-not $m.Success) { continue }
    $content = $m.Groups[1].Value
    if ($content -match 'image-viewer|wix-image') {
        $imgMatch = [regex]::Match($content, '<siteId>_[a-f0-9]+~mv2\.\w+')
        if ($imgMatch.Success) { # Record: imgNum, blockNum, mediaId }
        $imgNum++
    }
}
```

This produces an ordered list of (blockNumber, imageId) pairs. Number them sequentially (01, 02, ...) -- this IS the image order for the markdown.

**Important:** The same image ID may appear in multiple blocks (e.g. duplicate images). Each occurrence gets its own sequential number.

### Step 5: Verify Image Placement

For each image block found in Step 4, find the nearest non-empty text block before and after:

```powershell
foreach ($imgBlock in $imageBlocks) {
    # Search backwards for nearest non-empty text block
    for ($t = $imgBlock - 1; $t -ge 1; $t--) {
        # Extract block content, strip HTML, check non-empty
        # Record as PREV anchor text
    }
    # Search forwards for nearest non-empty text block
    for ($t = $imgBlock + 1; $t -le $maxBlock; $t++) {
        # Extract block content, strip HTML, check non-empty
        # Record as NEXT anchor text
    }
}
```

Images in Wix are typically padded by `<div type="empty-line">` blocks on both sides. The nearest non-empty text before/after determines exact placement in the markdown.

Use this anchor text to locate the insertion point when assembling the markdown in Step 7.

### Step 6: Download Images

Fetch original-quality images by using the base media URL (no Wix resize parameters):

```
https://static.wixstatic.com/media/<mediaId>
```

Save with sequential numbered filenames matching the extension from the media ID:

```powershell
curl -s -L -o images/01.jpg "https://static.wixstatic.com/media/<mediaId>"
```

Batch downloads in groups of ~22 to avoid overly long commands.

### Step 7: Write the Markdown File

Create `index.md` with:

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

**Body:** Walk the block map from Step 5 in order. For each entry:
- **TXT blocks**: Convert to markdown paragraphs. Detect headings (`<div type="heading"`), blockquotes (`<div type="blockquote"`), and empty lines. Skip gallery CSS, video embeds, and `<div type="image"` wrapper blocks.
- **IMG blocks**: Insert `![](images/<num>.<ext>)`.

Formatting rules:
- Preserve all paragraph breaks
- Use `##` for headings, `>` for blockquotes
- Bold text: `**bold text**`
- Timestamps in bold: `**16:25. text...**`

### Step 8: Clean Up

Delete the temp HTML file.

### Step 9: Verify

List the final output directory and show file sizes. Confirm:
- Image reference count in markdown matches number of image files
- All `![](images/...)` references resolve to existing files

## Caveats

- **Client-side rendering**: Wix loads images via JS. The `WebFetch` text pass will never contain image URLs. Always do the raw HTML pass.
- **Block-based extraction is critical**: Do NOT extract image IDs globally and then classify. Instead, find `image-viewer`/`wix-image` blocks directly -- this avoids including unrelated thumbnails (Recent Posts, nav) and avoids missing gallery/consecutive images.
- **Galleries and consecutive images**: Some blocks contain pro-gallery CSS followed by multiple image blocks. The block-map approach captures all of these; a global-regex approach can miss them.
- **Image quality**: The base media URL without resize parameters returns the uploaded original.
- **Hebrew / RTL**: Set `lang: he` and `dir: rtl` in front-matter for Hebrew posts.
- **Encoding**: Use UTF-8 without BOM for all output files. On Windows PowerShell, use `[System.IO.File]::WriteAllText()` with `UTF8Encoding($false)` if writing via PowerShell. Read HTML with `[System.IO.File]::ReadAllText('<file>', [System.Text.Encoding]::UTF8)`.
- **Performance**: For posts with many images (50+), use PowerShell-native regex instead of ripgrep to avoid shell escaping issues. Batch image downloads in groups.
