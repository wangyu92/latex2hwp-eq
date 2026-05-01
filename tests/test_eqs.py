"""Tier 1 EQS parse/emit golden pairs + roundtrip."""

from __future__ import annotations

import pytest

from hwpx_eq.eqs.emit import emit
from hwpx_eq.eqs.parse import parse
from hwpx_eq.ir import (
    BigOp,
    Char,
    Decorator,
    Delim,
    Frac,
    Func,
    Greek,
    Group,
    Op,
    Root,
    Sqrt,
    SupSub,
)

# -------- parse: EQS string -> IR --------


@pytest.mark.parametrize(
    "src,expected",
    [
        ("a", Char("a")),
        ("xyz", Group((Char("x"), Char("y"), Char("z")))),
        ("1+2", Group((Char("1"), Op("plus"), Char("2")))),
        ("{a} over {b}", Frac(Char("a"), Char("b"))),
        ("sqrt {x}", Sqrt(Char("x"))),
        ("sqrt x", Sqrt(Char("x"))),
        ("root n of {x}", Root(Char("n"), Char("x"))),
        ("a^2", SupSub(Char("a"), sup=Char("2"))),
        ("a_i", SupSub(Char("a"), sub=Char("i"))),
        ("a_i^n", SupSub(Char("a"), sup=Char("n"), sub=Char("i"))),
        ("alpha + beta", Group((Greek("alpha"), Op("plus"), Greek("beta")))),
        ("sin x", Group((Func("sin"), Char("x")))),
        ("a <= b", Group((Char("a"), Op("le"), Char("b")))),
        ("a != b", Group((Char("a"), Op("ne"), Char("b")))),
        (
            "sum _{i=1} ^n a",
            Group(
                (
                    BigOp(
                        "sum",
                        lower=Group((Char("i"), Op("eq"), Char("1"))),
                        upper=Char("n"),
                    ),
                    Char("a"),
                )
            ),
        ),
        (
            "int _a ^b f",
            Group((BigOp("int", lower=Char("a"), upper=Char("b")), Char("f"))),
        ),
        (
            "left ( a + b right )",
            Delim("(", ")", Group((Char("a"), Op("plus"), Char("b")))),
        ),
        ("hat {A}", Decorator("hat", Char("A"))),
    ],
)
def test_parse_golden(src: str, expected) -> None:
    assert parse(src) == expected


# -------- emit: IR -> EQS string --------


@pytest.mark.parametrize(
    "node,expected",
    [
        (Char("a"), "a"),
        (Frac(Char("a"), Char("b")), "{a} over {b}"),
        (Sqrt(Char("x")), "sqrt {x}"),
        (Root(Char("n"), Char("x")), "root {n} of {x}"),
        (SupSub(Char("a"), sup=Char("2")), "a ^ {2}"),
        (SupSub(Char("a"), sub=Char("i"), sup=Char("n")), "a _ {i} ^ {n}"),
        (Greek("alpha"), "alpha"),
        (Greek("Omega"), "Omega"),
        (Op("times"), "times"),
        (Op("le"), "<="),
        (Op("infty"), "inf"),
        (Func("sin"), "sin"),
        (BigOp("sum", lower=Char("i"), upper=Char("n")), "sum _ {i} ^ {n}"),
        (
            Delim("(", ")", Group((Char("a"), Op("plus"), Char("b")))),
            "left ( a + b right )",
        ),
        (Decorator("hat", Char("A")), "hat {A}"),
    ],
)
def test_emit_golden(node, expected: str) -> None:
    assert emit(node) == expected


# -------- roundtrip: EQS -> IR -> EQS, IR-equivalent --------


@pytest.mark.parametrize(
    "src",
    [
        "a",
        "{a} over {b}",
        "sqrt {x}",
        "root {n} of {x}",
        "a ^ {2}",
        "a _ {i} ^ {n}",
        "alpha",
        "sum _ {i} ^ {n}",
        "hat {A}",
    ],
)
def test_roundtrip_eqs(src: str) -> None:
    assert emit(parse(src)) == src
