"""HWPX read path: extract EQS, convert to LaTeX. Uses our own write as fixture."""

from __future__ import annotations

from pathlib import Path

from hwpx_eq.hwpx_io.read import read_eqs, read_latex, read_mixed
from hwpx_eq.hwpx_io.write import write_from_eqs, write_from_latex, write_mixed
from hwpx_eq.latex.extract import Equation, Paragraph, Table, Text


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
    blocks = [
        Paragraph(segments=(Text("Hello "), Equation(r"\frac{a}{b}"), Text(" world"))),
        Paragraph(segments=(Equation(r"\sqrt{x}"),)),
        Paragraph(segments=(Text("Just text."),)),
    ]
    out = tmp_path / "mixed.hwpx"
    write_mixed(blocks, str(out))
    got = read_mixed(str(out))

    assert len(got) == 3
    # Paragraph shapes preserved.
    p0 = got[0]
    assert isinstance(p0, Paragraph)
    assert isinstance(p0.segments[0], Text)
    assert isinstance(p0.segments[1], Equation)
    assert isinstance(p0.segments[2], Text)
    assert p0.segments[0].content == "Hello "
    assert p0.segments[2].content == " world"
    p1 = got[1]
    assert isinstance(p1, Paragraph)
    assert len(p1.segments) == 1 and isinstance(p1.segments[0], Equation)
    assert got[2] == Paragraph(segments=(Text("Just text."),))


def test_read_mixed_skips_default_empty_paragraph(tmp_path: Path) -> None:
    out = tmp_path / "single.hwpx"
    write_mixed([Paragraph(segments=(Text("only this paragraph"),))], str(out))
    got = read_mixed(str(out))
    assert got == [Paragraph(segments=(Text("only this paragraph"),))]


def test_read_mixed_equations_only_paragraphs(tmp_path: Path) -> None:
    out = tmp_path / "eq_only.hwpx"
    write_mixed(
        [
            Paragraph(segments=(Equation(r"\alpha"),)),
            Paragraph(segments=(Equation(r"\beta"),)),
        ],
        str(out),
    )
    got = read_mixed(str(out))
    assert len(got) == 2
    for b in got:
        assert isinstance(b, Paragraph)
        assert len(b.segments) == 1 and isinstance(b.segments[0], Equation)


def test_read_mixed_text_only_paragraphs(tmp_path: Path) -> None:
    out = tmp_path / "text_only.hwpx"
    write_mixed(
        [Paragraph(segments=(Text("first"),)), Paragraph(segments=(Text("second"),))],
        str(out),
    )
    got = read_mixed(str(out))
    assert got == [
        Paragraph(segments=(Text("first"),)),
        Paragraph(segments=(Text("second"),)),
    ]


# -------- Table round-trip --------


def test_table_round_trip(tmp_path: Path) -> None:
    src = Table(
        rows=(
            ((Text("h1"),), (Text("h2"),)),
            ((Text("a"),), (Equation(r"x^2"),)),
            ((Text("b"),), (Text("y"),)),
        ),
        has_header=True,
    )
    out = tmp_path / "tbl.hwpx"
    write_mixed([src], str(out))
    got = read_mixed(str(out))
    assert len(got) == 1
    tbl = got[0]
    assert isinstance(tbl, Table)
    assert tbl.has_header is True
    assert len(tbl.rows) == 3
    # Row 0 is header text
    assert tbl.rows[0][0] == (Text("h1"),)
    assert tbl.rows[0][1] == (Text("h2"),)
    # Row 1 cell (1,1) is an equation. The latex may be re-formatted (a^{2}).
    cell11 = tbl.rows[1][1]
    assert len(cell11) == 1 and isinstance(cell11[0], Equation)
    assert tbl.rows[2] == ((Text("b"),), (Text("y"),))


def test_table_with_no_header(tmp_path: Path) -> None:
    src = Table(
        rows=(((Text("a"),), (Text("b"),)),),
        has_header=False,
    )
    out = tmp_path / "noheader.hwpx"
    write_mixed([src], str(out))
    got = read_mixed(str(out))
    assert isinstance(got[0], Table)
    assert got[0].has_header is False


def test_paragraph_table_paragraph_order_preserved(tmp_path: Path) -> None:
    blocks = [
        Paragraph(segments=(Text("before"),)),
        Table(rows=(((Text("a"),), (Text("b"),)),), has_header=False),
        Paragraph(segments=(Text("after"),)),
    ]
    out = tmp_path / "ordered.hwpx"
    write_mixed(blocks, str(out))
    got = read_mixed(str(out))
    assert len(got) == 3
    assert isinstance(got[0], Paragraph)
    assert isinstance(got[1], Table)
    assert isinstance(got[2], Paragraph)
