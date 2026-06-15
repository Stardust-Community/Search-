# ============================================================
#   ᴜᴛɪʟꜱ — helpers
# ============================================================

import base64
import re
import hashlib
import time
from pyrogram.types import MessageEntity


# ── Slug / base64 deep-link ──────────────────────────────────

def make_slug(name: str) -> str:
    """Deterministic short slug from post name."""
    h = hashlib.md5(name.lower().encode()).hexdigest()[:10]
    return h

def encode_slug(slug: str) -> str:
    """URL-safe base64 encode for deep link."""
    return base64.urlsafe_b64encode(slug.encode()).decode().rstrip("=")

def decode_slug(b64: str) -> str:
    """Decode deep-link payload back to slug."""
    padding = 4 - len(b64) % 4
    if padding != 4:
        b64 += "=" * padding
    return base64.urlsafe_b64decode(b64.encode()).decode()

def make_deep_link(bot_username: str, slug: str) -> str:
    return f"https://t.me/{bot_username}?start={encode_slug(slug)}"


# ── Time parser (e.g. "5m", "2h", "3d") ─────────────────────

TIME_RE = re.compile(r"^(\d+)\s*(s|sec|m|min|h|hr|d|day)s?$", re.I)

UNITS = {
    "s": 1, "sec": 1,
    "m": 60, "min": 60,
    "h": 3600, "hr": 3600,
    "d": 86400, "day": 86400,
}

def parse_time(text: str) -> int | None:
    """Return seconds or None if parse fails."""
    m = TIME_RE.match(text.strip())
    if not m:
        return None
    amount, unit = int(m.group(1)), m.group(2).lower()
    return amount * UNITS[unit]

def fmt_time(seconds: int) -> str:
    if seconds == 0:
        return "ᴅɪꜱᴀʙʟᴇᴅ"
    d, r = divmod(seconds, 86400)
    h, r = divmod(r, 3600)
    m, s = divmod(r, 60)
    parts = []
    if d: parts.append(f"{d}ᴅ")
    if h: parts.append(f"{h}ʜ")
    if m: parts.append(f"{m}ᴍ")
    if s: parts.append(f"{s}ꜱ")
    return " ".join(parts)


# ── Entity-aware caption copier ──────────────────────────────

def entities_to_html(text: str, entities: list) -> str:
    """
    Convert a Pyrogram message text + entities list into HTML
    so Telegram renders bold / italic / code / strikethrough /
    underline / spoiler / text-links exactly as the admin typed.
    """
    if not entities:
        return text

    # We'll build an HTML string by inserting open/close tags at
    # the correct UTF-16 offsets (Telegram uses UTF-16 code units).
    utf16 = text.encode("utf-16-le")

    # Collect (offset, length, entity) and sort by offset
    spans = []
    for e in entities:
        spans.append(e)

    # Build list of events: (char_index, is_open, tag_html)
    events = []  # (utf16_offset, open=True/False, html_str)

    for ent in spans:
        o = ent.offset * 2      # bytes
        l = ent.length * 2      # bytes
        t = ent.type

        if t == "bold":
            open_tag, close_tag = "<b>", "</b>"
        elif t == "italic":
            open_tag, close_tag = "<i>", "</i>"
        elif t == "underline":
            open_tag, close_tag = "<u>", "</u>"
        elif t == "strikethrough":
            open_tag, close_tag = "<s>", "</s>"
        elif t == "code":
            open_tag, close_tag = "<code>", "</code>"
        elif t == "pre":
            lang = getattr(ent, "language", "") or ""
            open_tag  = f'<pre language="{lang}">' if lang else "<pre>"
            close_tag = "</pre>"
        elif t == "spoiler":
            open_tag, close_tag = "<tg-spoiler>", "</tg-spoiler>"
        elif t == "text_link":
            url = getattr(ent, "url", "") or ""
            open_tag, close_tag = f'<a href="{url}">', "</a>"
        elif t == "blockquote":
            open_tag, close_tag = "<blockquote>", "</blockquote>"
        else:
            continue  # mention, hashtag, etc. — keep as plain text

        events.append((o,     True,  open_tag))
        events.append((o + l, False, close_tag))

    # Sort: opens before closes at same position
    events.sort(key=lambda x: (x[0], not x[1]))

    # Walk through UTF-16 bytes and inject tags
    result = []
    prev   = 0
    for byte_pos, is_open, tag in events:
        chunk = utf16[prev:byte_pos].decode("utf-16-le")
        result.append(_escape_html(chunk))
        result.append(tag)
        prev = byte_pos

    result.append(_escape_html(utf16[prev:].decode("utf-16-le")))
    return "".join(result)


def _escape_html(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ── Query cleaner — strip season / episode noise ─────────────
#
# Handles patterns like:
#   s1  s01  s1e1  s01e02  season1  season 1  season01
#   ep1  ep01  episode1  episode 12
#   part1  part 2  vol1  volume 2
#   1x01  720p  1080p  4k  hd  bluray  webrip  hdtv  x264  x265  hevc
#   (and any trailing punctuation / extra whitespace left behind)

_SEASON_EP_RE = re.compile(
    r"""
    \b(
        s\d{1,3}(e\d{1,3})?        # s1 / s01 / s1e1 / s01e02
      | season\s*\d{1,3}           # season1 / season 01 / season 2
      | ep(isode)?\s*\d{1,3}       # ep1 / ep01 / episode 12
      | e\d{1,3}                   # e01 (standalone episode tag)
      | part\s*\d{1,3}             # part1 / part 2
      | vol(ume)?\s*\d{1,3}        # vol1 / volume 2
      | \d{1,2}x\d{2,3}           # 1x01 style
      | \b(480|720|1080|2160)p\b   # resolution
      | \b4k\b | \bhd\b            # quality tags
      | \b(bluray|blu-ray|webrip|web-dl|hdtv|dvdrip)\b
      | \b(x264|x265|hevc|avc|xvid|h264|h265)\b
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)

def clean_query(text: str) -> str:
    """
    Strip season/episode/quality suffixes from a user query so that
    'Breaking Bad S01', 'breaking bad season 2', 'breaking bad 1080p'
    all reduce to 'Breaking Bad' for lookup.
    """
    cleaned = _SEASON_EP_RE.sub("", text)
    # Collapse extra spaces and strip trailing punctuation / dashes
    cleaned = re.sub(r"[\s\-_:,.()\[\]]+$", "", cleaned.strip())
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    return cleaned.strip()


# ── Paginate ─────────────────────────────────────────────────

PAGE_SIZE = 8   # posts per page in /search results

def paginate(total: int, page: int) -> dict:
    pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    return {
        "page":  max(0, min(page, pages - 1)),
        "pages": pages,
        "skip":  page * PAGE_SIZE,
        "limit": PAGE_SIZE,
    }
