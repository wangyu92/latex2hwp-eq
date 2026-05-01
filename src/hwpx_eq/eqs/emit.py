"""IR -> EQS string."""

from __future__ import annotations

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
from hwpx_eq.mappings import (
    BIGOP_NAME_EQS,
    DEC_NAME_EQS,
    DELIM_LATEX_TO_EQS,
    FUNC_NAME_EQS,
    GREEK_NAME_EQS,
    OP_NAME_EQS,
)
from hwpx_eq.mathfonts import EQS_NATIVE, has_unicode_form, to_unicode_char

_MATRIX_KW_EQS = {"plain": "matrix", "p": "pmatrix", "b": "bmatrix", "v": "vmatrix", "V": "Vmatrix"}


def emit(node: Node) -> str:
    return _emit(node).strip()


def _emit_unicode_font(kind: str, base: Node) -> str:
    """For mathcal/mathbb/mathfrak: walk the base and substitute ASCII letters
    with the corresponding Mathematical Alphanumeric Symbols codepoints.
    """
    out: list[str] = []

    def walk(n: Node) -> None:
        if isinstance(n, Char):
            out.append("".join(to_unicode_char(kind, c) for c in n.text))
        elif isinstance(n, Group):
            for it in n.items:
                walk(it)
        else:
            out.append(_emit(n))

    walk(base)
    body = " ".join(s for s in out if s)
    return _wrap(body)


def _wrap(s: str) -> str:
    return "{" + s + "}"


def _emit(node: Node) -> str:
    if isinstance(node, Char):
        return node.text
    if isinstance(node, Op):
        return OP_NAME_EQS[node.name]
    if isinstance(node, Greek):
        return GREEK_NAME_EQS[node.name]
    if isinstance(node, Func):
        return FUNC_NAME_EQS[node.name]
    if isinstance(node, Group):
        return " ".join(_emit(it) for it in node.items)
    if isinstance(node, Frac):
        return f"{_wrap(_emit(node.num))} over {_wrap(_emit(node.den))}"
    if isinstance(node, Sqrt):
        return f"sqrt {_wrap(_emit(node.radicand))}"
    if isinstance(node, Root):
        return f"root {_wrap(_emit(node.index))} of {_wrap(_emit(node.radicand))}"
    if isinstance(node, SupSub):
        s = _emit(node.base)
        if node.sub is not None:
            s += f" _ {_wrap(_emit(node.sub))}"
        if node.sup is not None:
            s += f" ^ {_wrap(_emit(node.sup))}"
        return s
    if isinstance(node, BigOp):
        s = BIGOP_NAME_EQS[node.name]
        if node.lower is not None:
            s += f" _ {_wrap(_emit(node.lower))}"
        if node.upper is not None:
            s += f" ^ {_wrap(_emit(node.upper))}"
        return s
    if isinstance(node, Delim):
        ld = DELIM_LATEX_TO_EQS.get(node.left, node.left)
        rd = DELIM_LATEX_TO_EQS.get(node.right, node.right)
        return f"left {ld} {_emit(node.body)} right {rd}"
    if isinstance(node, Decorator):
        if has_unicode_form(node.kind):
            return _emit_unicode_font(node.kind, node.base)
        if node.kind in EQS_NATIVE:
            return f"{EQS_NATIVE[node.kind]} {_wrap(_emit(node.base))}"
        return f"{DEC_NAME_EQS[node.kind]} {_wrap(_emit(node.base))}"
    if isinstance(node, Matrix):
        rows = ["&".join(_emit(c) for c in row) for row in node.rows]
        body = "#".join(rows)
        kw = _MATRIX_KW_EQS.get(node.kind, "matrix")
        return f"{kw}{{{body}}}"
    if isinstance(node, Cases):
        rows = ["&".join(_emit(c) for c in row) for row in node.rows]
        body = "#".join(rows)
        return f"cases{{{body}}}"
    if isinstance(node, Pile):
        body = "#".join(_emit(r) for r in node.rows)
        kw = {"l": "lpile", "c": "cpile", "r": "rpile"}.get(node.align, "pile")
        return f"{kw}{{{body}}}"
    if isinstance(node, TextLit):
        # EQS uses `rm "text"` for upright text; quotes preserved.
        return f'rm "{node.text}"'
    if isinstance(node, Raw):
        return node.text if node.lang == "eqs" else ""
    raise TypeError(f"Unknown node type: {type(node).__name__}")
