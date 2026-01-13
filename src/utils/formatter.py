import re
import html
from typing import Generator

SENTENCE_END_RE = re.compile(r'([.!?])(\s+)')


def clean_text(text: str) -> str:
    if text is None:
        return ''
    # Normalize whitespace and remove excessive blank lines
    txt = text.replace('\r\n', '\n').replace('\r', '\n')
    txt = re.sub(r"\n{3,}", "\n\n", txt)
    txt = re.sub(r"[ \t]+", " ", txt)
    txt = txt.strip()
    return txt


def ensure_reviewer_headings(text: str) -> str:
    """Ensure reviewer output uses the canonical headings. If missing, try to split heuristically and insert headings."""
    text = clean_text(text)
    headings = ["Title Assessment", "Abstract Evaluation", "Strengths", "Weaknesses", "Detailed Comments", "Overall Recommendation"]

    # If any expected heading is present, assume good structure
    for h in headings:
        if re.search(rf"^#*\s*{re.escape(h)}", text, flags=re.IGNORECASE | re.MULTILINE):
            return text

    # Heuristic split: look for keyword anchors
    parts = {}
    # try to find Strengths / Weaknesses
    m_strengths = re.search(r"(Strengths?[:\-])", text, flags=re.IGNORECASE)
    m_weakness = re.search(r"(Weaknesses?[:\-])", text, flags=re.IGNORECASE)

    if m_strengths and m_weakness:
        before = text[:m_strengths.start()].strip()
        strengths = text[m_strengths.start():m_weakness.start()].strip()
        weaknesses = text[m_weakness.start():].strip()
        parts[headings[0]] = before or "(no title provided)"
        parts[headings[2]] = strengths
        parts[headings[3]] = weaknesses
    else:
        # fallback: place all under Detailed Comments
        parts[headings[4]] = text

    # Build markdown output
    out = []
    for h in headings:
        if h in parts:
            out.append(f"## {h}\n{clean_text(parts[h])}\n")
    return "\n".join(out) if out else text


def safe_markdown_to_html(md_text: str) -> str:
    """Convert markdown to HTML and remove <script> tags as simple sanitization."""
    try:
        import markdown
        html_text = markdown.markdown(md_text)
        # remove script tags
        html_text = re.sub(r"<script.*?>.*?</script>", "", html_text, flags=re.DOTALL | re.IGNORECASE)
        return html_text
    except Exception:
        return html.escape(md_text)


def chunk_text_for_stream(text: str, max_chars: int = 240) -> Generator[str, None, None]:
    """Yield chunks at sentence boundaries where possible."""
    text = clean_text(text)
    if not text:
        yield ''
        return

    sentences = re.split(r'(?<=[.!?])\s+', text)
    buf = ''
    for s in sentences:
        if len(buf) + len(s) + 1 <= max_chars:
            buf = (buf + ' ' + s).strip()
        else:
            if buf:
                yield buf
            buf = s
    if buf:
        yield buf


def format_for_bot(bot_id: str, text: str) -> str:
    text = clean_text(text)
    if bot_id == 'reviewer':
        return ensure_reviewer_headings(text)
    if bot_id == 'analyst':
        # For analyst, prefer an explicit markdown structure if present
        return text
    if bot_id == 'writer':
        # Writer should return a clean paragraph only
        return '\n\n'.join([p.strip() for p in text.splitlines() if p.strip()])
    if bot_id == 'conference':
        # Ensure concise first-line summary and bullets
        lines = text.splitlines()
        if len(lines) > 0 and len(lines[0]) > 0:
            first = lines[0].strip()
            rest = '\n'.join(lines[1:]).strip()
            if rest:
                return f"### Summary\n{first}\n\n{rest}"
            return f"### Summary\n{first}"
    return text