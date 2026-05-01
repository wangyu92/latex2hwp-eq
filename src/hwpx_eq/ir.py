"""IR for math equations. Symmetric between LaTeX and EQS."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Char:
    text: str


@dataclass(frozen=True)
class Op:
    name: str


@dataclass(frozen=True)
class Greek:
    name: str


@dataclass(frozen=True)
class Func:
    name: str


@dataclass(frozen=True)
class Group:
    items: tuple[Node, ...]


@dataclass(frozen=True)
class Frac:
    num: Node
    den: Node


@dataclass(frozen=True)
class Sqrt:
    radicand: Node


@dataclass(frozen=True)
class Root:
    index: Node
    radicand: Node


@dataclass(frozen=True)
class SupSub:
    base: Node
    sup: Node | None = None
    sub: Node | None = None


@dataclass(frozen=True)
class BigOp:
    name: str
    lower: Node | None = None
    upper: Node | None = None


@dataclass(frozen=True)
class Delim:
    left: str
    right: str
    body: Node


@dataclass(frozen=True)
class Decorator:
    kind: str
    base: Node


@dataclass(frozen=True)
class Matrix:
    kind: str  # 'plain' | 'p' | 'b' | 'v' | 'V'
    rows: tuple[tuple[Node, ...], ...]


@dataclass(frozen=True)
class Cases:
    rows: tuple[tuple[Node, ...], ...]


@dataclass(frozen=True)
class Pile:
    align: str  # 'l' | 'c' | 'r'
    rows: tuple[Node, ...]


@dataclass(frozen=True)
class TextLit:
    text: str


@dataclass(frozen=True)
class Raw:
    text: str
    lang: str  # 'latex' | 'eqs'


Node = (
    Char
    | Op
    | Greek
    | Func
    | Group
    | Frac
    | Sqrt
    | Root
    | SupSub
    | BigOp
    | Delim
    | Decorator
    | Matrix
    | Cases
    | Pile
    | TextLit
    | Raw
)


def seq(*items: Node) -> Group:
    return Group(items=tuple(items))
