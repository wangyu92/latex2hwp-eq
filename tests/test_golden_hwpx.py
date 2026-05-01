"""Regression tests against real .hwpx files produced by 한글.

These ground-truth fixtures were written by the user in Hangul Word Processor
and exported as .hwpx. They are the canonical reference for what real EQS
script payloads look like.
"""

from __future__ import annotations

from pathlib import Path

from hwpx_eq.eqs.parse import parse as parse_eqs
from hwpx_eq.hwpx_io.read import iter_equations, read_latex
from hwpx_eq.ir import (
    BigOp,
    Cases,
    Char,
    Decorator,
    Frac,
    Group,
    Matrix,
    Op,
    Root,
    Sqrt,
    SupSub,
)

FIXTURES = Path(__file__).parent / "fixtures" / "golden_hwpx"


def _read_one(name: str) -> str:
    eqs = list(iter_equations(str(FIXTURES / name)))
    assert len(eqs) == 1, f"{name}: expected 1 equation, got {len(eqs)}"
    return eqs[0]


# --- Tier 1: must work today ---


def test_01_frac() -> None:
    src = _read_one("01_frac.hwpx")
    assert src == "a over b"
    assert parse_eqs(src) == Frac(Char("a"), Char("b"))
    assert read_latex(str(FIXTURES / "01_frac.hwpx")) == [r"\frac{a}{b}"]


def test_02_sqrt() -> None:
    src = _read_one("02_sqrt.hwpx")
    assert src == "sqrt {(x+1)}"
    ir = parse_eqs(src)
    assert isinstance(ir, Sqrt)


def test_03_root() -> None:
    src = _read_one("03_root.hwpx")
    assert src == "root n of x"
    assert parse_eqs(src) == Root(Char("n"), Char("x"))
    assert read_latex(str(FIXTURES / "03_root.hwpx")) == [r"\sqrt[n]{x}"]


def test_04_sum() -> None:
    src = _read_one("04_sum.hwpx")
    assert src == "sum_{i=1}^n a_i"
    expected = Group(
        (
            BigOp(
                "sum",
                lower=Group((Char("i"), Op("eq"), Char("1"))),
                upper=Char("n"),
            ),
            SupSub(Char("a"), sub=Char("i")),
        )
    )
    assert parse_eqs(src) == expected


def test_05_int() -> None:
    src = _read_one("05_int.hwpx")
    assert "int" in src
    ir = parse_eqs(src)
    # First child must be BigOp('int', lower=a, upper=b)
    assert isinstance(ir, Group)
    first = ir.items[0]
    assert isinstance(first, BigOp) and first.name == "int"
    assert first.lower == Char("a") and first.upper == Char("b")


def test_10_decorators() -> None:
    src = _read_one("10_decorators.hwpx")
    ir = parse_eqs(src)
    # Should contain three Decorator nodes (hat, bar, vec) interleaved with commas.
    assert isinstance(ir, Group)
    decs = [it for it in ir.items if isinstance(it, Decorator)]
    kinds = [d.kind for d in decs]
    assert kinds == ["hat", "bar", "vec"]


def test_11_hangul_vars() -> None:
    src = _read_one("11_hangul_vars.hwpx")
    ir = parse_eqs(src)
    assert isinstance(ir, Group)
    chars = [it.text for it in ir.items if isinstance(it, Char)]
    assert "가" in chars and "나" in chars and "다" in chars


# --- Tier 2 ---


def _first_matrix(ir) -> Matrix:
    for it in ir.items if isinstance(ir, Group) else [ir]:
        if isinstance(it, Matrix):
            return it
    raise AssertionError(f"no Matrix found in {ir}")


def _first_cases(ir) -> Cases:
    for it in ir.items if isinstance(ir, Group) else [ir]:
        if isinstance(it, Cases):
            return it
    raise AssertionError(f"no Cases found in {ir}")


def test_06_matrix() -> None:
    src = _read_one("06_matrix.hwpx")
    m = _first_matrix(parse_eqs(src))
    assert m.kind == "plain"
    assert m.rows == (
        (Char("1"), Char("2")),
        (Char("3"), Char("4")),
    )


def test_07_pmatrix() -> None:
    src = _read_one("07_pmatrix.hwpx")
    m = _first_matrix(parse_eqs(src))
    assert m.kind == "p"
    assert m.rows == (
        (Char("1"), Char("0")),
        (Char("0"), Char("1")),
    )


def test_08_bmatrix() -> None:
    src = _read_one("08_bmatrix.hwpx")
    m = _first_matrix(parse_eqs(src))
    assert m.kind == "b"
    assert m.rows == (
        (Char("1"), Char("0")),
        (Char("1"), Char("0")),
    )


def test_09_cases() -> None:
    src = _read_one("09_cases.hwpx")
    c = _first_cases(parse_eqs(src))
    # Two rows, two cells each (value & condition).
    assert len(c.rows) == 2
    for r in c.rows:
        assert len(r) == 2
    # First row: x^2  &  x >= 0
    val0, cond0 = c.rows[0]
    assert val0 == SupSub(Char("x"), sup=Char("2"))
    assert cond0 == Group((Char("x"), Op("ge"), Char("0")))
