"""Extract LaTeX math fragments from a .tex/.md file.

Recognizes (longest-first to avoid `$$` being eaten by `$`):
  \\[ ... \\]
  $$ ... $$
  \\( ... \\)
  $ ... $
  \\begin{equation|equation*|align|align*|gather|gather*} ... \\end{...}
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_PATTERNS = [
    re.compile(r"\\\[(.+?)\\\]", re.DOTALL),
    re.compile(r"\$\$(.+?)\$\$", re.DOTALL),
    re.compile(r"\\\((.+?)\\\)", re.DOTALL),
    re.compile(
        r"\\begin\{(equation\*?|align\*?|gather\*?)\}(.+?)\\end\{\1\}",
        re.DOTALL,
    ),
    re.compile(r"(?<!\$)\$(?!\$)([^$]+?)(?<!\$)\$(?!\$)", re.DOTALL),
]

_PARAGRAPH_BREAK = re.compile(r"\n[ \t]*\n+")
_INTRA_PARA_WS = re.compile(r"\s+")


@dataclass(frozen=True)
class Text:
    content: str


@dataclass(frozen=True)
class Equation:
    latex: str


Segment = Text | Equation


def extract(text: str) -> list[str]:
    """Return all math fragments in the given text, in document order."""
    return [latex for _, _, latex in _equation_spans(text)]


def extract_segments(text: str) -> list[list[Segment]]:
    """Split text into paragraphs of Text/Equation segments.

    Paragraphs are separated by blank lines (`\\n\\s*\\n+`). Within a
    paragraph, runs of whitespace (including single newlines) collapse to a
    single space. Leading/trailing whitespace at paragraph boundaries is
    stripped. Equations preserve their LaTeX exactly.
    """
    spans = _equation_spans(text)

    # Build a flat list of ('text'|'eq', payload) interleaved.
    flat: list[tuple[str, str]] = []
    cursor = 0
    for start, end, latex in spans:
        if start > cursor:
            flat.append(("text", text[cursor:start]))
        flat.append(("eq", latex))
        cursor = end
    if cursor < len(text):
        flat.append(("text", text[cursor:]))

    paragraphs: list[list[Segment]] = []
    current: list[Segment] = []

    def close_paragraph() -> None:
        nonlocal current
        stripped = _strip_outer_text_whitespace(current)
        if stripped:
            paragraphs.append(stripped)
        current = []

    for kind, content in flat:
        if kind == "eq":
            current.append(Equation(latex=content))
            continue
        # Split text on blank-line boundaries; each odd-indexed part is a separator.
        parts = _PARAGRAPH_BREAK.split(content)
        for i, part in enumerate(parts):
            cleaned = _INTRA_PARA_WS.sub(" ", part)
            if cleaned:
                current.append(Text(content=cleaned))
            if i < len(parts) - 1:
                close_paragraph()

    close_paragraph()
    return paragraphs


def _equation_spans(text: str) -> list[tuple[int, int, str]]:
    spans: list[tuple[int, int, str]] = []
    for pat in _PATTERNS:
        for m in pat.finditer(text):
            grp = m.group(2) if m.lastindex and m.lastindex >= 2 else m.group(1)
            if any(_overlaps(m.start(), m.end(), s, e) for s, e, _ in spans):
                continue
            spans.append((m.start(), m.end(), grp.strip()))
    spans.sort(key=lambda x: x[0])
    return spans


def _strip_outer_text_whitespace(segs: list[Segment]) -> list[Segment]:
    if segs and isinstance(segs[0], Text):
        first = Text(content=segs[0].content.lstrip())
        segs = [first, *segs[1:]] if first.content else segs[1:]
    if segs and isinstance(segs[-1], Text):
        last = Text(content=segs[-1].content.rstrip())
        segs = [*segs[:-1], last] if last.content else segs[:-1]
    return segs


def _overlaps(a_s: int, a_e: int, b_s: int, b_e: int) -> bool:
    return a_s < b_e and b_s < a_e
