"""HWPX read path: extract EQS, convert to LaTeX. Uses our own write as fixture."""

from __future__ import annotations

from pathlib import Path

from hwpx_eq.hwpx_io.read import read_eqs, read_latex, read_mixed
from hwpx_eq.hwpx_io.write import write_from_eqs, write_from_latex, write_mixed
from hwpx_eq.latex.extract import Equation, Text


def test_read_eqs_roundtrip(tmp_path: Path) -> None:
    src = ["{a} over {b}", "sqrt {x}", "alpha + beta"]
    out = tmp_path / "rt.hwpx"
    write_from_eqs(src, str(out))
    assert read_eqs(str(out)) == src


def test_read_empty_hwpx_yields_nothing(tmp_path: Path) -> None:
    out = tmp_path / "empty.hwpx"
    write_from_eqs([], str(out))
    assert read_eqs(str(out)) == []


def test_read_latex_from_written_latex(tmp_path: Path) -> None:
    out = tmp_path / "lx.hwpx"
    write_from_latex([r"\frac{a}{b}", r"\sum_{i=1}^n"], str(out))
    latex = read_latex(str(out))
    assert latex == [r"\frac{a}{b}", r"\sum_{i = 1}^{n}"]


def test_full_roundtrip_latex_hwpx_latex(tmp_path: Path) -> None:
    src = [r"\frac{a}{b}", r"\sqrt{x}", r"\hat{A}"]
    out = tmp_path / "full.hwpx"
    write_from_latex(src, str(out))
    got = read_latex(str(out))
    assert got == src


# -------- read_mixed --------


def test_read_mixed_round_trips_paragraph_structure(tmp_path: Path) -> None:
    paragraphs = [
        [Text("Hello "), Equation(r"\frac{a}{b}"), Text(" world")],
        [Equation(r"\sqrt{x}")],
        [Text("Just text.")],
    ]
    out = tmp_path / "mixed.hwpx"
    write_mixed(paragraphs, str(out))
    got = read_mixed(str(out))

    assert len(got) == 3
    # Paragraph shapes preserved.
    p0 = got[0]
    assert isinstance(p0[0], Text)
    assert isinstance(p0[1], Equation)
    assert isinstance(p0[2], Text)
    assert p0[0].content == "Hello "
    assert p0[2].content == " world"
    assert len(got[1]) == 1 and isinstance(got[1][0], Equation)
    assert got[2] == [Text("Just text.")]


def test_read_mixed_skips_default_empty_paragraph(tmp_path: Path) -> None:
    out = tmp_path / "single.hwpx"
    write_mixed([[Text("only this paragraph")]], str(out))
    got = read_mixed(str(out))
    assert got == [[Text("only this paragraph")]]


def test_read_mixed_equations_only_paragraphs(tmp_path: Path) -> None:
    out = tmp_path / "eq_only.hwpx"
    write_mixed(
        [[Equation(r"\alpha")], [Equation(r"\beta")]],
        str(out),
    )
    got = read_mixed(str(out))
    assert len(got) == 2
    assert all(len(p) == 1 and isinstance(p[0], Equation) for p in got)


def test_read_mixed_text_only_paragraphs(tmp_path: Path) -> None:
    out = tmp_path / "text_only.hwpx"
    write_mixed(
        [[Text("first")], [Text("second")]],
        str(out),
    )
    got = read_mixed(str(out))
    assert got == [[Text("first")], [Text("second")]]
