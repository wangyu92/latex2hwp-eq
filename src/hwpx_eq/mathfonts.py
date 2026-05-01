"""Math font macro support: \\mathcal, \\mathbb, \\mathfrak, \\math{rm,bf,it,sf,tt}.

EQS handles font modifiers natively for some (rm/bold/it/sf/tt). For
calligraphic / blackboard / fraktur, HWP has no equivalent keyword, so we
emit Unicode codepoints from the Mathematical Alphanumeric Symbols block,
which 한글 renders correctly as long as the font has the glyphs.
"""

from __future__ import annotations

# Decorator kinds we recognize for math fonts.
MATH_FONT_KINDS = (
    "mathrm",
    "mathbf",
    "mathit",
    "mathsf",
    "mathtt",
    "mathcal",
    "mathbb",
    "mathfrak",
)

# LaTeX command (with backslash) -> kind name.
LATEX_TO_KIND = {f"\\{k}": k for k in MATH_FONT_KINDS}
KIND_TO_LATEX = {k: f"\\{k}" for k in MATH_FONT_KINDS}

# Kinds that map to native EQS keywords.
EQS_NATIVE = {
    "mathrm": "rm",
    "mathbf": "bold",
    "mathit": "it",
    "mathsf": "sf",
    "mathtt": "tt",
}

# Reverse: EQS keyword -> kind. Used by EQS parser to recognize `rm {X}` form
# of native font modifiers (TextLit's `rm "..."` is handled separately).
EQS_NATIVE_REV = {v: k for k, v in EQS_NATIVE.items()}

# Unicode block bases for kinds that have no EQS equivalent.
# Each entry: (uppercase_base, lowercase_base, uppercase_overrides, lowercase_overrides)
_UPPER_OVERRIDES_CAL = {
    "B": 0x212C, "E": 0x2130, "F": 0x2131, "H": 0x210B,
    "I": 0x2110, "L": 0x2112, "M": 0x2133, "R": 0x211B,
}
_LOWER_OVERRIDES_CAL = {"e": 0x212F, "g": 0x210A, "o": 0x2134}
_UPPER_OVERRIDES_BB = {
    "C": 0x2102, "H": 0x210D, "N": 0x2115, "P": 0x2119,
    "Q": 0x211A, "R": 0x211D, "Z": 0x2124,
}
_UPPER_OVERRIDES_FRAK = {
    "C": 0x212D, "H": 0x210C, "I": 0x2111, "R": 0x211C, "Z": 0x2128,
}

_UNICODE_BLOCKS = {
    "mathcal": (0x1D49C, 0x1D4B6, _UPPER_OVERRIDES_CAL, _LOWER_OVERRIDES_CAL),
    "mathbb": (0x1D538, 0x1D552, _UPPER_OVERRIDES_BB, {}),
    "mathfrak": (0x1D504, 0x1D51E, _UPPER_OVERRIDES_FRAK, {}),
}


def to_unicode_char(kind: str, c: str) -> str:
    """Map an ASCII letter to its math font Unicode codepoint, or return as-is."""
    block = _UNICODE_BLOCKS.get(kind)
    if block is None or len(c) != 1:
        return c
    upper_base, lower_base, upper_over, lower_over = block
    if "A" <= c <= "Z":
        return chr(upper_over.get(c, upper_base + ord(c) - ord("A")))
    if "a" <= c <= "z":
        return chr(lower_over.get(c, lower_base + ord(c) - ord("a")))
    return c


def has_unicode_form(kind: str) -> bool:
    return kind in _UNICODE_BLOCKS
