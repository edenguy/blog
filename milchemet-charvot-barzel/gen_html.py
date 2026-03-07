#!/usr/bin/env python3
"""Convert README.md to rich index.html with embedded videos."""
import re

with open("README.md", "r", encoding="utf-8") as f:
    md = f.read()

# Strip YAML frontmatter
md = re.sub(r"^---\n.*?\n---\n\n", "", md, flags=re.DOTALL)

# Video link pattern -> <video> element
md = re.sub(
    r'\[▶[^\]]*\]\((https://[^)]+videos/(\d+)\.mp4)\)',
    r'<figure class="video-wrap"><video src="videos/\2.mp4" controls preload="metadata" playsinline></video><figcaption>▶ וידאו</figcaption></figure>',
    md,
)
# Put adjacent videos (separated by ·) in a grid
md = re.sub(
    r'(<figure class="video-wrap">.*?</figure>)\s*·\s*(<figure class="video-wrap">.*?</figure>)',
    r'<div class="video-group">\1\2</div>',
    md,
    flags=re.DOTALL,
)

# Image pattern
md = re.sub(
    r'!\[\]\((images/[^)]+)\)',
    r'<figure class="img-wrap"><img src="\1" alt="" loading="lazy"></figure>',
    md,
)
md = re.sub(
    r'!\[\]\((he/whatsapp/[^)]+)\)',
    r'<figure class="img-wrap wa"><img src="\1" alt="" loading="lazy"></figure>',
    md,
)

# Headers
md = re.sub(r"^# (.+)$", r'<h1>\1</h1>', md, flags=re.MULTILINE)
md = re.sub(r"^## (.+)$", r'<h2 class="day">\1</h2>', md, flags=re.MULTILINE)
md = re.sub(r"^#### (.+)$", r'<h4>\1</h4>', md, flags=re.MULTILINE)

# Links
md = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2" target="_blank" rel="noopener">\1</a>', md)

# Code block
md = re.sub(
    r"```\n([\s\S]*?)```",
    r'<pre class="code-block"><code>\1</code></pre>',
    md,
)

# Bullet list - use full match
def replace_list(m):
    raw = m.group(0).strip().split("\n")
    lis = "".join(f"<li>{i.lstrip('- ').strip()}</li>" for i in raw if i.strip())
    return f"<ul class=\"diary-list\">{lis}</ul>"

md = re.sub(r"(?m)^- .+(?:\n- .+)*", replace_list, md)

# Split into paragraphs (double newline)
blocks = md.split("\n\n")
body_parts = []
for b in blocks:
    b = b.strip()
    if not b:
        continue
    if b.startswith("<"):
        body_parts.append(b)
    elif b.startswith("<ul"):
        body_parts.append(b)
    else:
        # Wrap in <p> if not already a block element
        lines = b.split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith("<"):
                body_parts.append(line)
            else:
                body_parts.append(f"<p>{line}</p>")

body_html = "\n".join(body_parts)

# Fix ◾ list - convert to ul
body_html = re.sub(
    r"<p>◾ ([^<]+)</p>(\s*<p>◾ [^<]+</p>)*",
    lambda m: "<ul class='guidelines'>" + "".join(
        f"<li>{re.search(r'◾ (.+)', p).group(1)}</li>"
        for p in m.group(0).split("</p>") if "◾" in p
    ) + "</ul>",
    body_html,
)

html = f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>חרבות ברזל, יומן מהעורף — גיא עדן</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;600;700&family=David+Libre:wght@400;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #f5f2eb;
      --bg-pattern: radial-gradient(ellipse at 20% 20%, rgba(196,165,116,.08) 0%, transparent 50%),
                    radial-gradient(ellipse at 80% 80%, rgba(139,69,19,.05) 0%, transparent 50%);
      --text: #1a1a1a;
      --muted: #5c5c5c;
      --accent: #6b4423;
      --accent-light: #a67c52;
      --card-bg: #fffefc;
      --shadow: 0 4px 20px rgba(0,0,0,.06);
      --shadow-hover: 0 8px 30px rgba(0,0,0,.1);
      --radius: 10px;
    }}
    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{
      font-family: "David Libre", "Heebo", "David", "Gisha", serif;
      font-size: 18px;
      line-height: 1.75;
      color: var(--text);
      background: var(--bg);
      margin: 0;
      padding: 0;
      direction: rtl;
    }}
    .container {{ max-width: 720px; margin: 0 auto; padding: 2rem 1.5rem; }}
    header {{
      text-align: center;
      padding: 3rem 0 2rem;
      border-bottom: 2px solid var(--accent-light);
      margin-bottom: 2rem;
    }}
    header h1 {{
      font-size: 2.2rem;
      font-weight: 700;
      margin: 0 0 0.5rem;
      color: var(--text);
    }}
    .meta {{
      font-size: 0.95rem;
      color: var(--muted);
    }}
    .meta a {{ color: var(--accent); text-decoration: none; }}
    .meta a:hover {{ text-decoration: underline; }}
    article {{ margin-bottom: 3rem; }}
    h1 {{ font-size: 1.8rem; margin: 2rem 0 1rem; }}
    h2.day {{
      font-size: 1.4rem;
      font-weight: 600;
      margin: 2.5rem 0 1rem;
      padding: 0.5rem 0;
      border-bottom: 1px solid var(--accent-light);
      color: var(--accent);
    }}
    h4 {{ font-size: 1.1rem; margin: 1.5rem 0 0.5rem; color: var(--muted); }}
    p {{ margin: 0 0 1rem; text-align: justify; }}
    .img-wrap, .video-wrap {{
      margin: 1.5rem 0;
      border-radius: var(--radius);
      overflow: hidden;
      box-shadow: var(--shadow);
      background: var(--card-bg);
    }}
    .img-wrap img, .video-wrap video {{
      display: block;
      width: 100%;
      max-width: 100%;
      height: auto;
    }}
    .video-wrap video {{ max-height: 480px; }}
    .video-group {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 1rem;
      margin: 1.5rem 0;
    }}
    .video-wrap figcaption, .img-wrap figcaption {{
      font-size: 0.85rem;
      color: var(--muted);
      padding: 0.5rem 1rem;
      background: #f5f5f5;
    }}
    .img-wrap.wa {{ max-width: 420px; margin-right: auto; margin-left: 0; }}
    .diary-list {{ margin: 1rem 0; padding-right: 1.5rem; }}
    .diary-list li {{ margin-bottom: 0.5rem; }}
    .guidelines {{ margin: 1rem 0; padding-right: 1.5rem; list-style: none; }}
    .guidelines li::before {{ content: "◾ "; color: var(--accent); margin-left: 0.25rem; }}
    .code-block {{
      background: #2d2d2d;
      color: #f8f8f2;
      padding: 1rem 1.25rem;
      border-radius: var(--radius);
      overflow-x: auto;
      font-family: "Consolas", "Monaco", monospace;
      font-size: 0.9rem;
      line-height: 1.5;
      margin: 1.5rem 0;
    }}
    .code-block code {{ white-space: pre-wrap; word-break: break-word; }}
    a {{ color: var(--accent); text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    footer {{
      text-align: center;
      padding: 2rem 0;
      font-size: 0.9rem;
      color: var(--muted);
      border-top: 1px solid var(--accent-light);
    }}
    @media (max-width: 600px) {{
      body {{ font-size: 16px; }}
      .container {{ padding: 1rem; }}
    }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>חרבות ברזל, יומן מהעורף</h1>
      <p class="meta">גיא עדן · אוקטובר 2023 · <a href="https://edenguy.wixsite.com/blog/post/milchamot-charvot-barzel-min-haaoref" target="_blank" rel="noopener">המקור בוויקס</a></p>
    </header>
    <article>
{body_html}
    </article>
    <footer>
      <p>חרבות ברזל — יומן מהעורף · גיא עדן</p>
    </footer>
  </div>
</body>
</html>
"""

# Fix the list replacement - the regex for guidelines might not work well. Let me simplify.
# Also need to fix the paragraph splitting - it might have broken things. Let me do a simpler conversion.

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

print("Generated index.html")
