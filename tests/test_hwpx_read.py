"""HWPX read path: extract EQS, convert to LaTeX. Uses our own write as fixture."""

from __future__ import annotations

from pathlib import Path

from hwpx_eq.hwpx_io.read import read_eqs, read_latex
from hwpx_eq.hwpx_io.write import write_from_eqs, write_from_latex


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
