"""LaTeX string -> IR. Walks pylatexenc node tree, then pairs sub/sup and \\left/\\right."""

from __future__ import annotations

from dataclasses import dataclass

from pylatexenc.latexwalker import (
    LatexCharsNode,
    LatexEnvironmentNode,
    LatexGroupNode,
    LatexMacroNode,
    LatexMathNode,
    LatexSpecialsNode,
    LatexWalker,
)

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
    Raw,
    Root,
    Sqrt,
    SupSub,
    TextLit,
)
from hwpx_eq.mathfonts import LATEX_TO_KIND as MATH_FONT_LATEX

_MATRIX_ENV_KINDS = {
    "matrix": "plain",
    "pmatrix": "p",
    "bmatrix": "b",
    "vmatrix": "v",
    "Vmatrix": "V",
}


@dataclass
class _SubSupMarker:
    kind: str  # '_' or '^'


@dataclass
class _LRMarker:
    kind: str  # 'left' or 'right'


# LaTeX uses \le \ge \ne \approx \equiv. ASCII multi-char ops are non-standard;
# we only split on single ASCII chars to avoid false matches.


def parse(s: str) -> Node:
    """Parse a LaTeX math fragment into IR. Outer dollar/braces are not required."""
    walker = LatexWalker(s)
    nodes, _, _ = walker.get_latex_nodes()
    return _build_from_node_list(nodes)


def _build_from_node_list(nodes) -> Node:
    things = _walk_things(nodes)
    things = _pair_left_right(things)
    items = _pair_supsub(things)
    return _wrap_seq(items)


def _walk_things(nodes) -> list:
    out: list = []
    for n in nodes:
        out.extend(_emit_things(n))
    return out


def _emit_things(node) -> list:
    if isinstance(node, LatexCharsNode):
        return _split_chars(node.chars)
    if isinstance(node, LatexGroupNode):
        return [_build_from_node_list(node.nodelist)]
    if isinstance(node, LatexMacroNode):
        return [_macro_to_atom(node)]
    if isinstance(node, LatexMathNode):
        return _walk_things(node.nodelist)
    if isinstance(node, LatexSpecialsNode):
        return _split_chars(node.specials_chars)
    if isinstance(node, LatexEnvironmentNode):
        if node.environmentname in _MATRIX_ENV_KINDS:
            rows = _split_table_rows(node.nodelist)
            return [Matrix(kind=_MATRIX_ENV_KINDS[node.environmentname], rows=rows)]
        if node.environmentname == "cases":
            rows = _split_table_rows(node.nodelist)
            return [Cases(rows=rows)]
        env = node.environmentname
        return [Raw(f"\\begin{{{env}}}...\\end{{{env}}}", lang="latex")]
    return [Raw(str(node), lang="latex")]


def _split_chars(s: str) -> list:
    """Split a CharsNode payload into IR atoms + sub/sup markers."""
    out: list = []
    i, n = 0, len(s)
    while i < n:
        c = s[i]
        if c.isspace():
            i += 1
            continue
        if c in "_^":
            out.append(_SubSupMarker(c))
            i += 1
            continue
        if c in "+-=<>,;:":
            if c in M.OP_LATEX:
                out.append(Op(M.OP_LATEX[c]))
            else:
                out.append(Char(c))
            i += 1
            continue
        out.append(Char(c))
        i += 1
    return out


def _macro_to_atom(node) -> Node:
    cmd = "\\" + node.macroname
    args = list(node.nodeargd.argnlist) if node.nodeargd and node.nodeargd.argnlist else []

    if node.macroname == "frac":
        num = _arg_to_node(args[0]) if len(args) > 0 else Group(items=())
        den = _arg_to_node(args[1]) if len(args) > 1 else Group(items=())
        return Frac(num, den)
    if node.macroname == "sqrt":
        if len(args) >= 2 and args[0] is not None:
            return Root(_arg_to_node(args[0]), _arg_to_node(args[1]))
        if len(args) >= 1 and args[0] is not None:
            return Sqrt(_arg_to_node(args[0]))
        if len(args) >= 2 and args[1] is not None:
            return Sqrt(_arg_to_node(args[1]))
        return Sqrt(Group(items=()))
    if node.macroname in ("left", "right"):
        return _LRMarker(node.macroname)
    if cmd in M.DEC_LATEX:
        base = _arg_to_node(args[0]) if args and args[0] is not None else Group(items=())
        return Decorator(M.DEC_LATEX[cmd], base)
    if cmd in MATH_FONT_LATEX:
        base = _arg_to_node(args[0]) if args and args[0] is not None else Group(items=())
        return Decorator(MATH_FONT_LATEX[cmd], base)
    if node.macroname == "text":
        if args and isinstance(args[0], LatexGroupNode):
            return TextLit(_chars_of(args[0]))
        if args and isinstance(args[0], LatexCharsNode):
            return TextLit(args[0].chars)
        return TextLit("")
    if cmd in M.GREEK_LATEX:
        return Greek(M.GREEK_LATEX[cmd])
    if cmd in M.BIGOP_LATEX:
        return BigOp(M.BIGOP_LATEX[cmd])
    if cmd in M.FUNC_LATEX:
        return Func(M.FUNC_LATEX[cmd])
    if cmd in M.OP_LATEX:
        return Op(M.OP_LATEX[cmd])
    return Raw(cmd, lang="latex")


def _arg_to_node(node) -> Node:
    if node is None:
        return Group(items=())
    if isinstance(node, LatexGroupNode):
        return _build_from_node_list(node.nodelist)
    return _build_from_node_list([node])


def _chars_of(group_node: LatexGroupNode) -> str:
    parts: list[str] = []
    for c in group_node.nodelist:
        if isinstance(c, LatexCharsNode):
            parts.append(c.chars)
    return "".join(parts).strip()


def _split_table_rows(nodes) -> tuple[tuple[Node, ...], ...]:
    rows: list[tuple[Node, ...]] = []
    cur_row: list[Node] = []
    cur_cell_nodes: list = []

    def flush_cell() -> None:
        cur_row.append(_build_from_node_list(cur_cell_nodes))
        cur_cell_nodes.clear()

    def flush_row() -> None:
        flush_cell()
        rows.append(tuple(cur_row))
        cur_row.clear()

    for n in nodes:
        if isinstance(n, LatexMacroNode) and n.macroname == "\\":
            flush_row()
            continue
        if isinstance(n, LatexSpecialsNode) and n.specials_chars == "&":
            flush_cell()
            continue
        cur_cell_nodes.append(n)

    if cur_cell_nodes or cur_row:
        flush_row()

    while rows and all(
        isinstance(c, Group) and not c.items for c in rows[-1]
    ):
        rows.pop()

    return tuple(rows)


def _pair_left_right(things: list) -> list:
    out: list = []
    i = 0
    while i < len(things):
        t = things[i]
        if isinstance(t, _LRMarker) and t.kind == "left":
            left_delim = _atom_to_delim(things[i + 1]) if i + 1 < len(things) else "."
            depth = 1
            j = i + 2
            inner: list = []
            while j < len(things):
                th = things[j]
                if isinstance(th, _LRMarker):
                    if th.kind == "left":
                        depth += 1
                        inner.append(th)
                    else:  # right
                        depth -= 1
                        if depth == 0:
                            break
                        inner.append(th)
                else:
                    inner.append(th)
                j += 1
            right_delim = "."
            if j < len(things) and j + 1 < len(things):
                right_delim = _atom_to_delim(things[j + 1])
            inner = _pair_left_right(inner)
            inner_items = _pair_supsub(inner)
            out.append(Delim(left_delim, right_delim, _wrap_seq(inner_items)))
            i = j + 2
            continue
        if isinstance(t, _LRMarker) and t.kind == "right":
            i += 1
            continue
        out.append(t)
        i += 1
    return out


def _atom_to_delim(thing) -> str:
    if isinstance(thing, Char):
        return thing.text
    return "."


def _pair_supsub(things: list) -> list:
    out: list = []
    i = 0
    while i < len(things):
        t = things[i]
        if isinstance(t, _SubSupMarker):
            i += 1
            continue
        sup = sub = None
        j = i + 1
        while j + 1 <= len(things) - 1 and isinstance(things[j], _SubSupMarker):
            mark = things[j].kind
            arg = things[j + 1]
            if isinstance(arg, _SubSupMarker):
                break
            if mark == "_":
                sub = arg
            else:
                sup = arg
            j += 2
        # Edge: marker at end of list with no arg — handle by checking j inside list bounds
        while j < len(things) and isinstance(things[j], _SubSupMarker):
            mark = things[j].kind
            if j + 1 >= len(things):
                j += 1
                break
            arg = things[j + 1]
            if isinstance(arg, _SubSupMarker):
                break
            if mark == "_":
                sub = arg
            else:
                sup = arg
            j += 2
        if sup is not None or sub is not None:
            if isinstance(t, BigOp):
                out.append(BigOp(t.name, lower=sub, upper=sup))
            else:
                out.append(SupSub(t, sup=sup, sub=sub))
            i = j
        else:
            out.append(t)
            i += 1
    return out


def _wrap_seq(items: list) -> Node:
    items = [it for it in items if not isinstance(it, (_SubSupMarker, _LRMarker))]
    if not items:
        return Group(items=())
    if len(items) == 1:
        return items[0]
    return Group(items=tuple(items))
