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


def extract(text: str) -> list[str]:
    """Return all math fragments in the given text, in document order."""
    spans: list[tuple[int, int, str]] = []
    for pat in _PATTERNS:
        for m in pat.finditer(text):
            grp = m.group(2) if m.lastindex and m.lastindex >= 2 else m.group(1)
            if any(_overlaps(m.start(), m.end(), s, e) for s, e, _ in spans):
                continue
            spans.append((m.start(), m.end(), grp.strip()))
    spans.sort(key=lambda x: x[0])
    return [g for _, _, g in spans]


def _overlaps(a_s: int, a_e: int, b_s: int, b_e: int) -> bool:
    return a_s < b_e and b_s < a_e
