"""EQS string -> IR. Hand-rolled tokenizer + recursive descent parser.

EQS grammar handled (Tier 1):
    expr   := over_expr+
    over_expr := power ('over' power)*
    power  := atom (('_' | '^') atom)*
    atom   := '{' expr* '}'
            | 'sqrt' atom
            | 'root' atom 'of' atom
            | 'left' delim expr* 'right' delim
            | bigop ('_' atom | '^' atom)*
            | DECORATOR atom
            | 'rm' QUOTED
            | GREEK | FUNC | OP_KW | OP_ASCII | NUMBER | IDENT_CHAR
"""

from __future__ import annotations

from dataclasses import dataclass

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
    Root,
    Sqrt,
    SupSub,
    TextLit,
)
from hwpx_eq.mathfonts import EQS_NATIVE_REV

_MATRIX_KINDS = {
    "matrix": "plain",
    "pmatrix": "p",
    "bmatrix": "b",
    "vmatrix": "v",
    "Vmatrix": "V",
}


@dataclass
class Tok:
    kind: str
    value: str


_MULTI_CHAR_OPS = ("<->", "<=>", "<=", ">=", "!=", "~=", "==", "<-", "->", "=>")
_SINGLE_ASCII_OPS = "+-=<>,;:"
_DELIM_CHARS = "()[]|."


def tokenize(s: str) -> list[Tok]:
    out: list[Tok] = []
    i, n = 0, len(s)
    while i < n:
        c = s[i]
        if c.isspace():
            i += 1
            continue
        if c in "{}_^":
            out.append(Tok({"{": "LBRACE", "}": "RBRACE", "_": "USCORE", "^": "CARET"}[c], c))
            i += 1
            continue
        if c == "&":
            out.append(Tok("AMP", "&"))
            i += 1
            continue
        if c == "#":
            out.append(Tok("HASH", "#"))
            i += 1
            continue
        matched = False
        for op in _MULTI_CHAR_OPS:
            if s.startswith(op, i):
                out.append(Tok("ASCII_OP", op))
                i += len(op)
                matched = True
                break
        if matched:
            continue
        if c in _SINGLE_ASCII_OPS:
            out.append(Tok("ASCII_OP", c))
            i += 1
            continue
        if c.isalpha():
            j = i
            while j < n and s[j].isalpha():
                j += 1
            out.append(Tok("WORD", s[i:j]))
            i = j
            continue
        if c.isdigit():
            j = i
            while j < n and (s[j].isdigit() or s[j] == "."):
                j += 1
            out.append(Tok("NUMBER", s[i:j]))
            i = j
            continue
        if c == '"':
            j = i + 1
            while j < n and s[j] != '"':
                j += 1
            out.append(Tok("QUOTED", s[i + 1 : j]))
            i = j + 1 if j < n else j
            continue
        if c in _DELIM_CHARS:
            out.append(Tok("DELIM_CHAR", c))
            i += 1
            continue
        out.append(Tok("CHAR", c))
        i += 1
    return out


def parse(s: str) -> Node:
    p = _Parser(tokenize(s))
    items = p.parse_seq()
    if p.cur is not None:
        raise ValueError(f"trailing tokens at position {p.i}: {p.cur}")
    return _wrap_seq(items)


class _Parser:
    def __init__(self, tokens: list[Tok]) -> None:
        self.toks = tokens
        self.i = 0

    @property
    def cur(self) -> Tok | None:
        return self.toks[self.i] if self.i < len(self.toks) else None

    def advance(self) -> Tok:
        t = self.toks[self.i]
        self.i += 1
        return t

    def parse_seq(self, stop_words: tuple[str, ...] = ()) -> list[Node]:
        items: list[Node] = []
        while self.cur is not None:
            t = self.cur
            if t.kind == "RBRACE":
                break
            if t.kind == "WORD" and t.value in stop_words:
                break
            items.append(self.parse_over())
        return items

    def parse_over(self) -> Node:
        left = self.parse_power()
        while self.cur and self.cur.kind == "WORD" and self.cur.value == "over":
            self.advance()
            right = self.parse_power()
            left = Frac(left, right)
        return left

    def parse_power(self) -> Node:
        base = self.parse_atom()
        sup: Node | None = None
        sub: Node | None = None
        while self.cur and self.cur.kind in ("USCORE", "CARET"):
            mark = self.advance().kind
            arg = self.parse_atom()
            if mark == "USCORE":
                sub = arg
            else:
                sup = arg
        if sup is not None or sub is not None:
            return SupSub(base, sup=sup, sub=sub)
        return base

    def parse_atom(self) -> Node:
        t = self.cur
        if t is None:
            raise ValueError("unexpected end of input")

        if t.kind == "LBRACE":
            self.advance()
            items = self.parse_seq()
            if self.cur and self.cur.kind == "RBRACE":
                self.advance()
            return _wrap_seq(items)

        if t.kind == "WORD":
            w = t.value
            if w == "sqrt":
                self.advance()
                return Sqrt(self.parse_atom())
            if w == "root":
                self.advance()
                idx = self.parse_atom()
                if self.cur and self.cur.kind == "WORD" and self.cur.value == "of":
                    self.advance()
                rad = self.parse_atom()
                return Root(idx, rad)
            if w == "left":
                self.advance()
                left_d = self._consume_delim()
                items = self.parse_seq(stop_words=("right",))
                if self.cur and self.cur.kind == "WORD" and self.cur.value == "right":
                    self.advance()
                right_d = self._consume_delim()
                return Delim(left=left_d, right=right_d, body=_wrap_seq(items))
            if w == "rm":
                self.advance()
                if self.cur and self.cur.kind == "QUOTED":
                    return TextLit(self.advance().value)
                # `rm {body}` form -> Decorator('mathrm', body)
                if self.cur and self.cur.kind == "LBRACE":
                    return Decorator("mathrm", self.parse_atom())
                return TextLit("")
            if w in EQS_NATIVE_REV:
                self.advance()
                return Decorator(EQS_NATIVE_REV[w], self.parse_atom())
            if w in _MATRIX_KINDS:
                self.advance()
                return self._parse_table(matrix_kind=_MATRIX_KINDS[w])
            if w == "cases":
                self.advance()
                return self._parse_table(matrix_kind=None)
            if w in M.BIGOP_EQS:
                self.advance()
                lower: Node | None = None
                upper: Node | None = None
                while self.cur and self.cur.kind in ("USCORE", "CARET"):
                    mark = self.advance().kind
                    arg = self.parse_atom()
                    if mark == "USCORE":
                        lower = arg
                    else:
                        upper = arg
                return BigOp(M.BIGOP_EQS[w], lower=lower, upper=upper)
            if w in M.DEC_EQS:
                self.advance()
                return Decorator(M.DEC_EQS[w], self.parse_atom())
            if w in M.GREEK_EQS:
                self.advance()
                return Greek(M.GREEK_EQS[w])
            if w in M.FUNC_EQS:
                self.advance()
                return Func(M.FUNC_EQS[w])
            if w in M.OP_EQS:
                self.advance()
                return Op(M.OP_EQS[w])
            self.advance()
            if len(w) == 1:
                return Char(w)
            return Group(items=tuple(Char(c) for c in w))

        if t.kind in ("AMP", "HASH"):
            # Outside table context: treat as literal char.
            self.advance()
            return Char(t.value)

        if t.kind == "ASCII_OP":
            self.advance()
            if t.value in M.OP_EQS:
                return Op(M.OP_EQS[t.value])
            return Char(t.value)

        if t.kind == "NUMBER":
            self.advance()
            return Char(t.value)

        if t.kind == "DELIM_CHAR":
            self.advance()
            return Char(t.value)

        if t.kind == "CHAR":
            self.advance()
            return Char(t.value)

        raise ValueError(f"unexpected token at position {self.i}: {t}")

    def _parse_table(self, matrix_kind: str | None) -> Node:
        """Parse a `{... & ... # ... & ...}` table body.

        If matrix_kind is given, return Matrix; otherwise Cases.
        """
        if not (self.cur and self.cur.kind == "LBRACE"):
            return Matrix(kind=matrix_kind, rows=()) if matrix_kind else Cases(rows=())
        self.advance()  # consume '{'

        rows: list[tuple[Node, ...]] = []
        row: list[Node] = []
        cell_items: list[Node] = []

        def end_cell() -> None:
            row.append(_wrap_seq(cell_items))
            cell_items.clear()

        def end_row() -> None:
            end_cell()
            rows.append(tuple(row))
            row.clear()

        while self.cur is not None and self.cur.kind != "RBRACE":
            t = self.cur
            if t.kind == "AMP":
                self.advance()
                end_cell()
                continue
            if t.kind == "HASH":
                self.advance()
                end_row()
                continue
            cell_items.append(self.parse_over())

        if self.cur and self.cur.kind == "RBRACE":
            self.advance()

        if cell_items or row:
            end_row()

        while rows and all(_is_empty_node(c) for c in rows[-1]):
            rows.pop()

        if matrix_kind is not None:
            return Matrix(kind=matrix_kind, rows=tuple(rows))
        return Cases(rows=tuple(rows))

    def _consume_delim(self) -> str:
        """Consume the next token as a delimiter character (for left/right)."""
        t = self.cur
        if t is None:
            return "."
        # Allow LBRACE/RBRACE used as delim after left/right.
        if t.kind in ("DELIM_CHAR", "LBRACE", "RBRACE", "ASCII_OP", "CHAR"):
            self.advance()
            return t.value
        if t.kind == "WORD" and t.value in ("lbrace", "rbrace"):
            self.advance()
            return "{" if t.value == "lbrace" else "}"
        # No delim: invisible
        return "."


def _wrap_seq(items: list[Node]) -> Node:
    if not items:
        return Group(items=())
    if len(items) == 1:
        return items[0]
    return Group(items=tuple(items))


def _is_empty_node(node: Node) -> bool:
    return isinstance(node, Group) and not node.items
