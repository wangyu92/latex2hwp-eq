"""IR -> LaTeX string."""

from __future__ import annotations

from hwpx_eq import mappings as M
from hwpx_eq.ir import (
    BigOp,
    Cases,
    Char,
    Decorator,
    Delim,
    Frac,
    Func,
    Greek,
    Group,
    Matrix,
    Node,
    Op,
    Pile,
    Raw,
    Root,
    Sqrt,
    SupSub,
    TextLit,
)
from hwpx_eq.mathfonts import KIND_TO_LATEX as MATH_FONT_KIND_LATEX

_MATRIX_KW_LATEX = {
    "plain": "matrix",
    "p": "pmatrix",
    "b": "bmatrix",
    "v": "vmatrix",
    "V": "Vmatrix",
}


def emit(node: Node) -> str:
    return _e(node).strip()


def _e(n: Node) -> str:
    if isinstance(n, Char):
        return n.text
    if isinstance(n, Op):
        return M.OP_NAME_LATEX[n.name]
    if isinstance(n, Greek):
        return M.GREEK_NAME_LATEX[n.name]
    if isinstance(n, Func):
        return M.FUNC_NAME_LATEX[n.name]
    if isinstance(n, Group):
        return " ".join(_e(it) for it in n.items)
    if isinstance(n, Frac):
        return f"\\frac{{{_e(n.num)}}}{{{_e(n.den)}}}"
    if isinstance(n, Sqrt):
        return f"\\sqrt{{{_e(n.radicand)}}}"
    if isinstance(n, Root):
        return f"\\sqrt[{_e(n.index)}]{{{_e(n.radicand)}}}"
    if isinstance(n, SupSub):
        s = _e(n.base)
        if n.sub is not None:
            s += f"_{{{_e(n.sub)}}}"
        if n.sup is not None:
            s += f"^{{{_e(n.sup)}}}"
        return s
    if isinstance(n, BigOp):
        s = M.BIGOP_NAME_LATEX[n.name]
        if n.lower is not None:
            s += f"_{{{_e(n.lower)}}}"
        if n.upper is not None:
            s += f"^{{{_e(n.upper)}}}"
        return s
    if isinstance(n, Delim):
        return f"\\left{n.left} {_e(n.body)} \\right{n.right}"
    if isinstance(n, Decorator):
        if n.kind in MATH_FONT_KIND_LATEX:
            return f"{MATH_FONT_KIND_LATEX[n.kind]}{{{_e(n.base)}}}"
        return f"{M.DEC_NAME_LATEX[n.kind]}{{{_e(n.base)}}}"
    if isinstance(n, Matrix):
        kw = _MATRIX_KW_LATEX.get(n.kind, "matrix")
        rows = [" & ".join(_e(c) for c in row) for row in n.rows]
        body = " \\\\ ".join(rows)
        return f"\\begin{{{kw}}} {body} \\end{{{kw}}}"
    if isinstance(n, Cases):
        rows = [" & ".join(_e(c) for c in row) for row in n.rows]
        body = " \\\\ ".join(rows)
        return f"\\begin{{cases}} {body} \\end{{cases}}"
    if isinstance(n, Pile):
        rows = " \\\\ ".join(_e(r) for r in n.rows)
        return f"\\begin{{array}}{{{n.align}}} {rows} \\end{{array}}"
    if isinstance(n, TextLit):
        return f"\\text{{{n.text}}}"
    if isinstance(n, Raw):
        return n.text if n.lang == "latex" else ""
    raise TypeError(f"Unknown node: {type(n).__name__}")
