import json
import sys
import asyncio
from pathlib import Path

HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  background: #0b141a;
  font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
  font-size: 15px;
  color: #e9edef;
  width: WIDTH_PXpx;
  direction: DIRECTION;
}

.header {
  background: #202c33;
  padding: 10px 16px;
  display: flex;
  align-items: center;
  gap: 10px;
  border-bottom: 1px solid #374045;
}

.header .back { color: #00a884; font-size: 22px; }

.header .avatar {
  width: 40px; height: 40px;
  background: #2a3942;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  color: #8696a0; font-size: 20px;
}

.header .info { flex: 1; }
.header .name { font-size: 16px; font-weight: 500; color: #e9edef; }
.header .status { font-size: 12px; color: #8696a0; }

.header .icons { display: flex; gap: 20px; color: #aebac1; font-size: 20px; }

.chat {
  padding: 8px 12px;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.msg {
  max-width: 75%;
  padding: 6px 8px 2px 8px;
  border-radius: 8px;
  position: relative;
  line-height: 1.35;
  word-wrap: break-word;
}

.msg.left {
  align-self: flex-start;
  background: #202c33;
}

.msg.right {
  align-self: flex-end;
  background: #005c4b;
}

.msg .sender {
  font-size: 12.5px;
  font-weight: 500;
  color: #f7941d;
  margin-bottom: 2px;
}

.msg .sender .phone {
  color: #8696a0;
  font-weight: 400;
  margin-left: 8px;
}

.msg .text {
  font-size: 14.5px;
  color: #e9edef;
  line-height: 1.3;
}

.msg .meta {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 4px;
  margin-top: 1px;
  padding-bottom: 2px;
}

.msg .time {
  font-size: 11px;
  color: #8696a099;
}

.msg .edited {
  font-size: 11px;
  color: #8696a099;
}

.msg .check {
  font-size: 12px;
  color: #53bdeb;
  letter-spacing: -3px;
}

.reaction {
  position: absolute;
  bottom: -10px;
  left: 4px;
  font-size: 16px;
  background: #202c33;
  border-radius: 10px;
  padding: 1px 4px;
  border: 1px solid #0b141a;
}

.msg.right .reaction {
  left: auto;
  right: 4px;
}

.time-spacer { height: 16px; }

.quote-block {
  background: rgba(0, 0, 0, 0.25);
  border-radius: 4px;
  padding: 4px 8px;
  margin-bottom: 4px;
  border-left: 3px solid #06cf9c;
}
.quote-block .quote-sender {
  color: #06cf9c;
  font-size: 12px;
  font-weight: 500;
}
.quote-block .quote-text {
  color: #8696a0;
  font-size: 13px;
  line-height: 1.3;
}

.forwarded-label {
  font-size: 12px;
  color: #8696a0;
  font-style: italic;
  margin-bottom: 2px;
}

.system-msg {
  text-align: center;
  padding: 4px 12px;
  color: rgba(134, 150, 160, 0.6);
  font-size: 12.5px;
  background: #1b2831;
  border-radius: 6px;
  align-self: center;
  max-width: 85%;
}

.date-divider {
  text-align: center;
  padding: 4px 12px;
  color: #e9edef;
  font-size: 12.5px;
  background: #182229;
  border-radius: 8px;
  align-self: center;
  margin: 4px 0;
}

.unread-banner {
  text-align: center;
  padding: 6px 0;
  color: #e9edef;
  font-size: 13px;
  background: #182229;
  width: 100%;
  margin: 4px 0;
}

.chat-footer {
  text-align: center;
  padding: 10px 12px;
  color: #8696a0;
  font-size: 13px;
}
.chat-footer .admin-label { color: #00a884; }

.poll-question {
  font-size: 14.5px;
  font-weight: 500;
  margin: 4px 0 8px 0;
  color: #e9edef;
}
.poll-hint {
  font-size: 12px;
  color: #8696a0;
  margin-bottom: 8px;
}
.poll-option {
  display: flex;
  align-items: center;
  padding: 8px;
  border: 1px solid #374045;
  border-radius: 8px;
  margin-bottom: 4px;
  gap: 8px;
  position: relative;
  overflow: hidden;
}
.poll-option .poll-radio {
  font-size: 18px;
  color: #8696a0;
  z-index: 1;
}
.poll-option.selected .poll-radio {
  color: #00a884;
}
.poll-option .poll-label {
  flex: 1;
  font-size: 14px;
  z-index: 1;
}
.poll-option .poll-count {
  font-size: 14px;
  color: #8696a0;
  z-index: 1;
}
.poll-bar {
  position: absolute;
  left: 0; top: 0; bottom: 0;
  background: rgba(0, 168, 132, 0.2);
  border-radius: 8px;
}
.view-votes {
  text-align: center;
  color: #00a884;
  font-size: 14px;
  padding: 8px;
  border-top: 1px solid #374045;
  margin-top: 4px;
}
</style>
</head>
<body>

<div class="header">
  <span class="back">&#8592;</span>
  <div class="avatar">AVATAR_ICON</div>
  <div class="info">
    <div class="name">CHAT_NAME</div>
    <div class="status">CHAT_STATUS</div>
  </div>
  <div class="icons">
    <span>&#127909;</span>
    <span>&#128222;</span>
    <span>&#8942;</span>
  </div>
</div>

<div class="chat">
MESSAGES_HTML
</div>

FOOTER_HTML

</body>
</html>"""


# AI-Generated: Claude
def build_message_html(msg):
    side = msg.get("side", "left")
    sender = msg.get("sender", "")
    sender_phone = msg.get("sender_phone", "")
    text = msg.get("text", "")
    time_val = msg.get("time", "")
    check = msg.get("check", "")
    reaction = msg.get("reaction", "")
    quote = msg.get("quote")
    forwarded = msg.get("forwarded", False)
    edited = msg.get("edited", False)

    parts = []
    parts.append(f'  <div class="msg {side}">')

    if forwarded:
        parts.append('    <div class="forwarded-label">&#8618; Forwarded</div>')

    if sender:
        phone_html = f' <span class="phone">{sender_phone}</span>' if sender_phone else ""
        parts.append(f'    <div class="sender">{sender}{phone_html}</div>')

    if quote:
        q_sender = quote.get("sender", "")
        q_text = quote.get("text", "")
        parts.append('    <div class="quote-block">')
        parts.append(f'      <div class="quote-sender">{q_sender}</div>')
        parts.append(f'      <div class="quote-text">{q_text}</div>')
        parts.append('    </div>')

    parts.append(f'    <div class="text">{text}</div>')

    meta_parts = ""
    if edited:
        meta_parts += '<span class="edited">Edited </span>'
    meta_parts += f'<span class="time">{time_val}</span>'
    if check:
        meta_parts += f' <span class="check">{check}</span>'
    parts.append(f'    <div class="meta">{meta_parts}</div>')

    if reaction:
        parts.append(f'    <div class="reaction">{reaction}</div>')

    parts.append("  </div>")
    return "\n".join(parts)


def build_system_html(msg):
    text = msg.get("text", "")
    return f'  <div class="system-msg">{text}</div>'


def build_date_html(msg):
    text = msg.get("text", "")
    return f'  <div class="date-divider">{text}</div>'


def build_unread_html(msg):
    text = msg.get("text", "1 Unread Message")
    return f'  <div class="unread-banner">{text}</div>'


# AI-Generated: Claude
def build_poll_html(msg):
    sender = msg.get("sender", "")
    sender_phone = msg.get("sender_phone", "")
    question = msg.get("question", "")
    options = msg.get("options", [])
    time_val = msg.get("time", "")
    hint = msg.get("hint", "Select one")

    parts = []
    parts.append('  <div class="msg left" style="max-width: 85%;">')

    if sender:
        phone_html = f' <span class="phone">{sender_phone}</span>' if sender_phone else ""
        parts.append(f'    <div class="sender">{sender}{phone_html}</div>')

    parts.append(f'    <div class="poll-question">{question}</div>')
    parts.append(f'    <div class="poll-hint">\u2705 {hint}</div>')

    max_votes = max((o.get("votes", 0) for o in options), default=1) or 1
    for opt in options:
        selected = "selected" if opt.get("selected") else ""
        radio = "\u2705" if opt.get("selected") else "\u25cb"
        label = opt.get("label", "")
        votes = opt.get("votes", 0)
        bar_pct = int((votes / max_votes) * 100) if votes > 0 else 0
        bar_html = f'<div class="poll-bar" style="width: {bar_pct}%;"></div>' if bar_pct > 0 else ""
        parts.append(f'    <div class="poll-option {selected}">')
        parts.append(f'      <span class="poll-radio">{radio}</span>')
        parts.append(f'      <span class="poll-label">{label}</span>')
        parts.append(f'      <span class="poll-count">{votes}</span>')
        parts.append(f'      {bar_html}')
        parts.append('    </div>')

    parts.append(f'    <div class="meta"><span class="time">{time_val}</span></div>')
    parts.append('    <div class="view-votes">View votes</div>')
    parts.append("  </div>")
    return "\n".join(parts)


def render_chat_image(chat_data, output_path, width=420):
    direction = chat_data.get("direction", "rtl")
    chat_name = chat_data.get("chat_name", "")
    chat_status = chat_data.get("chat_status", "")
    avatar_icon = chat_data.get("avatar_icon", "&#128101;")
    footer = chat_data.get("footer", "")
    messages = chat_data.get("messages", [])

    msgs_html = []
    for msg in messages:
        msg_type = msg.get("type", "message")
        if msg_type == "spacer":
            msgs_html.append('  <div class="time-spacer"></div>')
        elif msg_type == "system":
            msgs_html.append(build_system_html(msg))
        elif msg_type == "date":
            msgs_html.append(build_date_html(msg))
        elif msg_type == "unread":
            msgs_html.append(build_unread_html(msg))
        elif msg_type == "poll":
            msgs_html.append(build_poll_html(msg))
        else:
            msgs_html.append(build_message_html(msg))

    footer_html = ""
    if footer:
        footer_html = f'<div class="chat-footer">Only <span class="admin-label">admins</span> can send messages</div>'

    html = HTML_TEMPLATE
    html = html.replace("WIDTH_PX", str(width))
    html = html.replace("DIRECTION", direction)
    html = html.replace("CHAT_NAME", chat_name)
    html = html.replace("CHAT_STATUS", chat_status)
    html = html.replace("AVATAR_ICON", avatar_icon)
    html = html.replace("MESSAGES_HTML", "\n".join(msgs_html))
    html = html.replace("FOOTER_HTML", footer_html)

    html_path = str(output_path).replace(".jpg", ".html").replace(".png", ".html")
    Path(html_path).write_text(html, encoding="utf-8")

    asyncio.run(_screenshot(html_path, str(output_path), width))
    Path(html_path).unlink(missing_ok=True)
    print(f"Generated: {output_path}")


async def _screenshot(html_path, output_path, width):
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": width, "height": 800})
        await page.goto(f"file:///{Path(html_path).resolve().as_posix()}")
        await page.wait_for_timeout(300)

        body = await page.query_selector("body")
        bbox = await body.bounding_box()
        height = int(bbox["height"]) + 2

        await page.set_viewport_size({"width": width, "height": height})
        await page.screenshot(path=output_path, full_page=True, type="jpeg", quality=92)
        await browser.close()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python wa_renderer.py <chat.json> <output.jpg>")
        sys.exit(1)

    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    out = sys.argv[2]
    width = int(sys.argv[3]) if len(sys.argv) > 3 else 420
    render_chat_image(data, out, width)
