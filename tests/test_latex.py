"""Tier 1 LaTeX parse/emit + LaTeX↔EQS roundtrip."""

from __future__ import annotations

import pytest

from hwpx_eq.eqs.emit import emit as emit_eqs
from hwpx_eq.eqs.parse import parse as parse_eqs
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
    Op,
    Root,
    Sqrt,
    SupSub,
    TextLit,
)
from hwpx_eq.latex.emit import emit as emit_latex
from hwpx_eq.latex.parse import parse as parse_latex

# -------- parse: LaTeX -> IR --------


@pytest.mark.parametrize(
    "src,expected",
    [
        ("a", Char("a")),
        (r"\frac{a}{b}", Frac(Char("a"), Char("b"))),
        (r"\sqrt{x}", Sqrt(Char("x"))),
        (r"\sqrt[n]{x}", Root(Char("n"), Char("x"))),
        (r"\sqrt x", Sqrt(Char("x"))),
        ("a^2", SupSub(Char("a"), sup=Char("2"))),
        ("a_i", SupSub(Char("a"), sub=Char("i"))),
        ("a_i^n", SupSub(Char("a"), sup=Char("n"), sub=Char("i"))),
        ("a^n_i", SupSub(Char("a"), sup=Char("n"), sub=Char("i"))),
        (r"\alpha + \beta", Group((Greek("alpha"), Op("plus"), Greek("beta")))),
        (r"\sin x", Group((Func("sin"), Char("x")))),
        (r"a \le b", Group((Char("a"), Op("le"), Char("b")))),
        (r"\hat{A}", Decorator("hat", Char("A"))),
        (r"\hat A", Decorator("hat", Char("A"))),
        (
            r"\sum_{i=1}^n a",
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
            r"\int_a^b f",
            Group((BigOp("int", lower=Char("a"), upper=Char("b")), Char("f"))),
        ),
        (
            r"\left( a+b \right)",
            Delim("(", ")", Group((Char("a"), Op("plus"), Char("b")))),
        ),
    ],
)
def test_parse_latex_golden(src: str, expected) -> None:
    assert parse_latex(src) == expected


# -------- emit: IR -> LaTeX --------


@pytest.mark.parametrize(
    "node,expected",
    [
        (Char("a"), "a"),
        (Frac(Char("a"), Char("b")), r"\frac{a}{b}"),
        (Sqrt(Char("x")), r"\sqrt{x}"),
        (Root(Char("n"), Char("x")), r"\sqrt[n]{x}"),
        (SupSub(Char("a"), sup=Char("2")), "a^{2}"),
        (SupSub(Char("a"), sub=Char("i"), sup=Char("n")), "a_{i}^{n}"),
        (Greek("alpha"), r"\alpha"),
        (Greek("Omega"), r"\Omega"),
        (Op("times"), r"\times"),
        (Op("le"), r"\le"),
        (Op("infty"), r"\infty"),
        (Func("sin"), r"\sin"),
        (BigOp("sum", lower=Char("i"), upper=Char("n")), r"\sum_{i}^{n}"),
        (Decorator("hat", Char("A")), r"\hat{A}"),
        (
            Delim("(", ")", Group((Char("a"), Op("plus"), Char("b")))),
            r"\left( a + b \right)",
        ),
    ],
)
def test_emit_latex_golden(node, expected: str) -> None:
    assert emit_latex(node) == expected


# -------- LaTeX -> EQS roundtrip via IR --------


@pytest.mark.parametrize(
    "latex_src,eqs_expected",
    [
        ("a", "a"),
        (r"\frac{a}{b}", "{a} over {b}"),
        (r"\sqrt{x}", "sqrt {x}"),
        (r"\sqrt[n]{x}", "root {n} of {x}"),
        ("a^2", "a ^ {2}"),
        ("a_i", "a _ {i}"),
        ("a_i^n", "a _ {i} ^ {n}"),
        (r"\alpha", "alpha"),
        (r"\Omega", "Omega"),
        (r"\sin x", "sin x"),
        (r"\hat{A}", "hat {A}"),
        (r"\sum_{i=1}^n", "sum _ {i = 1} ^ {n}"),
        (r"\int_a^b", "int _ {a} ^ {b}"),
    ],
)
def test_latex_to_eqs(latex_src: str, eqs_expected: str) -> None:
    assert emit_eqs(parse_latex(latex_src)) == eqs_expected


# -------- EQS -> LaTeX roundtrip via IR --------


@pytest.mark.parametrize(
    "eqs_src,latex_expected",
    [
        ("a", "a"),
        ("{a} over {b}", r"\frac{a}{b}"),
        ("sqrt {x}", r"\sqrt{x}"),
        ("root {n} of {x}", r"\sqrt[n]{x}"),
        ("alpha", r"\alpha"),
        ("Omega", r"\Omega"),
        ("sin x", r"\sin x"),
        ("hat {A}", r"\hat{A}"),
        ("sum _ {i} ^ {n}", r"\sum_{i}^{n}"),
    ],
)
def test_eqs_to_latex(eqs_src: str, latex_expected: str) -> None:
    assert emit_latex(parse_eqs(eqs_src)) == latex_expected


# -------- Full round trip: LaTeX → EQS → LaTeX (semantic equivalence) --------


@pytest.mark.parametrize(
    "src",
    [
        r"\frac{a}{b}",
        r"\sqrt{x}",
        r"a^{2}",
        r"\sum_{i}^{n}",
        r"\alpha + \beta",
    ],
)
def test_full_roundtrip(src: str) -> None:
    ir1 = parse_latex(src)
    eqs = emit_eqs(ir1)
    ir2 = parse_eqs(eqs)
    assert ir1 == ir2, f"\nLaTeX: {src}\nEQS: {eqs}\nir1: {ir1}\nir2: {ir2}"


# -------- Tier 2: matrix / cases / text --------


def test_parse_matrix_env() -> None:
    src = r"\begin{matrix} a & b \\ c & d \end{matrix}"
    ir = parse_latex(src)
    assert ir == Matrix(
        kind="plain",
        rows=((Char("a"), Char("b")), (Char("c"), Char("d"))),
    )


def test_parse_pmatrix_env() -> None:
    src = r"\begin{pmatrix} 1 & 0 \\ 0 & 1 \end{pmatrix}"
    ir = parse_latex(src)
    assert ir == Matrix(
        kind="p",
        rows=((Char("1"), Char("0")), (Char("0"), Char("1"))),
    )


def test_parse_cases_env() -> None:
    src = r"\begin{cases} x^2 & x \ge 0 \\ -x & x < 0 \end{cases}"
    ir = parse_latex(src)
    assert isinstance(ir, Cases)
    assert len(ir.rows) == 2
    val0, _ = ir.rows[0]
    assert val0 == SupSub(Char("x"), sup=Char("2"))


def test_parse_text() -> None:
    assert parse_latex(r"\text{hello}") == TextLit("hello")


def test_emit_matrix() -> None:
    m = Matrix(kind="p", rows=((Char("a"), Char("b")), (Char("c"), Char("d"))))
    assert emit_latex(m) == r"\begin{pmatrix} a & b \\ c & d \end{pmatrix}"


def test_matrix_full_roundtrip() -> None:
    src = r"\begin{pmatrix} 1 & 2 \\ 3 & 4 \end{pmatrix}"
    assert emit_latex(parse_latex(src)) == src


def test_cases_full_roundtrip() -> None:
    src = r"\begin{cases} a & b \\ c & d \end{cases}"
    assert emit_latex(parse_latex(src)) == src
