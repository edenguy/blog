import re
import sys
from pathlib import Path


IMG_P_RE = re.compile(
    r'(<p>)\s*(<img\s+[^>]*src="([^"]+)"[^>]*/?>)\s*(</p>)'
)
WHITESPACE_ONLY_RE = re.compile(r'^\s*$')


def is_consecutive(html, match1_end, match2_start):
    between = html[match1_end:match2_start]
    return WHITESPACE_ONLY_RE.match(between) is not None


# AI-Generated: Claude
def postprocess(html_path):
    html = Path(html_path).read_text(encoding="utf-8")

    matches = list(IMG_P_RE.finditer(html))
    if not matches:
        return

    groups = []
    current_group = [matches[0]]
    for j in range(1, len(matches)):
        if is_consecutive(html, matches[j - 1].end(), matches[j].start()):
            current_group.append(matches[j])
        else:
            groups.append(current_group)
            current_group = [matches[j]]
    groups.append(current_group)

    replacements = []
    quads = 0
    pairs = 0
    solos = 0
    removed = 0

    for group in groups:
        i = 0
        while i < len(group):
            remaining = len(group) - i

            if remaining >= 4:
                imgs = [group[i + k].group(2) for k in range(4)]
                grid_html = (
                    '<div class="image-grid">\n'
                    + "".join(f"  {img}\n" for img in imgs)
                    + "</div>"
                )
                replacements.append((group[i].start(), group[i].end(), grid_html))
                for k in range(1, 4):
                    replacements.append((group[i + k].start(), group[i + k].end(), ""))
                    removed += 1
                quads += 1
                i += 4

            elif remaining >= 2:
                m1 = group[i]
                m2 = group[i + 1]
                pair_html = (
                    '<div class="image-pair">\n'
                    f"  {m1.group(2)}\n"
                    f"  {m2.group(2)}\n"
                    "</div>"
                )
                replacements.append((m1.start(), m1.end(), pair_html))
                replacements.append((m2.start(), m2.end(), ""))
                pairs += 1
                removed += 1
                i += 2

            else:
                m = group[i]
                solo_html = (
                    f'<div class="image-solo">\n  {m.group(2)}\n</div>'
                )
                replacements.append((m.start(), m.end(), solo_html))
                solos += 1
                i += 1

    for start, end, replacement in reversed(replacements):
        html = html[:start] + replacement + html[end:]

    Path(html_path).write_text(html, encoding="utf-8")
    print(f"Post-processed: {quads} quads, {pairs} pairs, {solos} solo, {removed} merged")


if __name__ == "__main__":
    postprocess(sys.argv[1])
