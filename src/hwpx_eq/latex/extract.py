"""Extract LaTeX math + GFM tables from a .tex/.md file.

Equation markers (longest-first to avoid `$$` being eaten by `$`):
  \\[ ... \\]
  $$ ... $$
  \\( ... \\)
  $ ... $
  \\begin{equation|equation*|align|align*|gather|gather*} ... \\end{...}

Tables: GitHub-flavored markdown pipe tables — header row, `|---|` delimiter,
zero or more data rows. Alignment markers (`:---`, `---:`, `:---:`) are
recognized in the delimiter but ignored for output.
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
_TABLE_ROW = re.compile(r"^\s*\|.*\|\s*$")
_TABLE_DELIMITER = re.compile(r"^\s*\|(\s*:?-+:?\s*\|)+\s*$")
_PLACEHOLDER = re.compile("(\\d+)")


@dataclass(frozen=True)
class Text:
    content: str


@dataclass(frozen=True)
class Equation:
    latex: str


Segment = Text | Equation


@dataclass(frozen=True)
class Paragraph:
    """A block of inline segments (text and equations)."""
    segments: tuple[Segment, ...]


@dataclass(frozen=True)
class Table:
    """A markdown / HWPX table.

    rows[r][c] is a tuple of inline Segments forming cell (r, c)'s content.
    """
    rows: tuple[tuple[tuple[Segment, ...], ...], ...]
    has_header: bool


Block = Paragraph | Table


def extract(text: str) -> list[str]:
    """Return all math fragments in the given text, in document order."""
    return [latex for _, _, latex in _equation_spans(text)]


def extract_blocks(text: str) -> list[Block]:
    """Parse text into a sequence of Paragraph and Table blocks.

    Equations are protected with placeholders before block detection so a `|`
    appearing inside an equation (e.g. `|x|`) doesn't trigger table parsing.
    """
    placeholder_text, ph_map = _replace_equations_with_placeholders(text)
    chunks = _PARAGRAPH_BREAK.split(placeholder_text)
    blocks: list[Block] = []
    for chunk in chunks:
        chunk = chunk.strip("\n")
        if not chunk.strip():
            continue
        table = _try_parse_md_table(chunk, ph_map)
        if table is not None:
            blocks.append(table)
            continue
        segs = _placeholder_text_to_segments(chunk, ph_map)
        if segs:
            blocks.append(Paragraph(segments=tuple(segs)))
    return blocks


def _replace_equations_with_placeholders(text: str) -> tuple[str, dict[str, str]]:
    spans = _equation_spans(text)
    ph_map: dict[str, str] = {}
    parts: list[str] = []
    cursor = 0
    for start, end, latex in spans:
        if start > cursor:
            parts.append(text[cursor:start])
        ph = f"{len(ph_map)}"
        ph_map[ph] = latex
        parts.append(ph)
        cursor = end
    if cursor < len(text):
        parts.append(text[cursor:])
    return "".join(parts), ph_map


def _try_parse_md_table(chunk: str, ph_map: dict[str, str]) -> Table | None:
    lines = chunk.splitlines()
    if len(lines) < 2:
        return None
    if not all(_TABLE_ROW.match(line) for line in lines):
        return None
    if not _TABLE_DELIMITER.match(lines[1]):
        return None
    header_cells = _split_md_row(lines[0])
    cols = len(header_cells)
    rows: list[tuple[tuple[Segment, ...], ...]] = []
    rows.append(_row_to_cells(header_cells, ph_map, cols))
    for line in lines[2:]:
        cells = _split_md_row(line)
        rows.append(_row_to_cells(cells, ph_map, cols))
    return Table(rows=tuple(rows), has_header=True)


def _row_to_cells(
    raw_cells: list[str], ph_map: dict[str, str], cols: int
) -> tuple[tuple[Segment, ...], ...]:
    # Pad/trim to header column count so all rows are rectangular.
    cells = (raw_cells + [""] * cols)[:cols]
    return tuple(
        tuple(_placeholder_text_to_segments(cell, ph_map)) for cell in cells
    )


def _split_md_row(line: str) -> list[str]:
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def _placeholder_text_to_segments(
    text: str, ph_map: dict[str, str]
) -> list[Segment]:
    """Re-expand placeholders into Equation segments and collapse whitespace
    in the surrounding text. Trims leading/trailing whitespace.
    """
    out: list[Segment] = []
    cursor = 0
    for m in _PLACEHOLDER.finditer(text):
        if m.start() > cursor:
            chunk = text[cursor : m.start()]
            for piece in _split_text_on_paragraph_breaks(chunk):
                cleaned = _INTRA_PARA_WS.sub(" ", piece)
                if cleaned:
                    out.append(Text(content=cleaned))
        out.append(Equation(latex=ph_map[m.group(0)]))
        cursor = m.end()
    if cursor < len(text):
        chunk = text[cursor:]
        for piece in _split_text_on_paragraph_breaks(chunk):
            cleaned = _INTRA_PARA_WS.sub(" ", piece)
            if cleaned:
                out.append(Text(content=cleaned))
    return _strip_outer_text_whitespace(out)


def _split_text_on_paragraph_breaks(s: str) -> list[str]:
    # Within a chunk passed here we should not have paragraph breaks (callers
    # split by them earlier). But callers from cells pass cell text which has
    # no breaks anyway. This keeps a single code path safe.
    return _PARAGRAPH_BREAK.split(s)


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


# ---------------------------------------------------------------------------
# Backward-compat: callers that still use `extract_segments` (paragraphs only).


def extract_segments(text: str) -> list[list[Segment]]:
    """Deprecated: use `extract_blocks`. Returns paragraph blocks as nested
    lists of Segment, dropping any tables. Kept temporarily so older callers
    keep working during the migration.
    """
    blocks = extract_blocks(text)
    return [list(b.segments) for b in blocks if isinstance(b, Paragraph)]
