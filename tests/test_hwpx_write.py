"""Verify generated HWPX files have valid structure and embedded equations."""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest
from lxml import etree

from hwpx_eq.hwpx_io.ns import HP, NSMAP
from hwpx_eq.hwpx_io.write import write_from_eqs, write_from_latex, write_mixed
from hwpx_eq.latex.extract import Equation, Paragraph, Table, Text


def _read_section_xml(hwpx_path: Path) -> etree._Element:
    with zipfile.ZipFile(hwpx_path) as zf:
        section_names = [
            n for n in zf.namelist()
            if n.startswith("Contents/section") and n.endswith(".xml")
        ]
        assert section_names, "no section xml found"
        with zf.open(section_names[0]) as f:
            return etree.parse(f).getroot()


def test_write_single_equation_creates_valid_zip(tmp_path: Path) -> None:
    out = tmp_path / "single.hwpx"
    write_from_eqs(["{a} over {b}"], str(out))
    assert out.exists()
    assert zipfile.is_zipfile(out)


def test_written_hwpx_contains_equation_element_and_script(tmp_path: Path) -> None:
    out = tmp_path / "frac.hwpx"
    write_from_eqs(["{a} over {b}"], str(out))
    root = _read_section_xml(out)
    eqs = root.findall(f".//{{{HP}}}equation")
    assert len(eqs) == 1
    scripts = eqs[0].findall(f"{{{HP}}}script")
    assert len(scripts) == 1
    assert scripts[0].text and "over" in scripts[0].text


def test_multiple_equations_one_per_paragraph(tmp_path: Path) -> None:
    out = tmp_path / "multi.hwpx"
    src = ["{a} over {b}", "sqrt {x}", "alpha + beta"]
    write_from_eqs(src, str(out))
    root = _read_section_xml(out)
    eqs = root.findall(f".//{{{HP}}}equation")
    assert len(eqs) == 3
    scripts = [e.find(f"{{{HP}}}script").text for e in eqs]
    assert scripts == src


def test_equation_has_required_attributes(tmp_path: Path) -> None:
    out = tmp_path / "attrs.hwpx"
    write_from_eqs(["a + b"], str(out))
    root = _read_section_xml(out)
    eq = root.find(f".//{{{HP}}}equation")
    assert eq is not None
    for k in ("version", "baseLine", "baseUnit", "lineMode", "font"):
        assert eq.get(k), f"missing attr {k}"
    sz = eq.find(f"{{{NSMAP['hp']}}}sz")
    pos = eq.find(f"{{{NSMAP['hp']}}}pos")
    om = eq.find(f"{{{NSMAP['hp']}}}outMargin")
    assert sz is not None and pos is not None and om is not None
    assert pos.get("treatAsChar") == "1", "equation must be inline (글자처럼 취급)"


@pytest.mark.parametrize(
    "latex_src,expected_eqs_substring",
    [
        (r"\frac{a}{b}", "over"),
        (r"\sqrt{x}", "sqrt"),
        (r"\sum_{i=1}^n a_i", "sum"),
    ],
)
def test_write_from_latex(tmp_path: Path, latex_src: str, expected_eqs_substring: str) -> None:
    out = tmp_path / "from_latex.hwpx"
    write_from_latex([latex_src], str(out))
    root = _read_section_xml(out)
    script = root.find(f".//{{{HP}}}equation/{{{HP}}}script")
    assert script is not None
    assert expected_eqs_substring in script.text


# -------- write_mixed --------


def _user_paragraphs(root: etree._Element) -> list[etree._Element]:
    """Return only the paragraphs we authored (skip python-hwpx default empty ones).

    A paragraph counts as authored if it contains an equation or any non-empty
    <hp:t> text. The default blank paragraph has an empty <hp:t> placeholder.
    """
    out = []
    for p in root.findall(f".//{{{HP}}}p"):
        if p.findall(f".//{{{HP}}}equation"):
            out.append(p)
            continue
        for t in p.findall(f"{{{HP}}}run/{{{HP}}}t"):
            if (t.text or "").strip():
                out.append(p)
                break
    return out


def test_write_mixed_creates_text_and_equation_runs(tmp_path: Path) -> None:
    out = tmp_path / "mixed.hwpx"
    paragraphs = [
        [Text("Hello "), Equation(r"\frac{a}{b}"), Text(" world")],
        [Text("Just text.")],
        [Equation(r"\sqrt{x}")],
    ]
    write_mixed(paragraphs, str(out))
    root = _read_section_xml(out)
    user_paras = _user_paragraphs(root)
    assert len(user_paras) == 3

    # Paragraph 1: 3 runs (text, equation, text)
    p1_runs = user_paras[0].findall(f"{{{HP}}}run")
    assert len(p1_runs) == 3
    assert p1_runs[0].find(f"{{{HP}}}t").text == "Hello "
    assert p1_runs[1].find(f"{{{HP}}}equation") is not None
    assert p1_runs[2].find(f"{{{HP}}}t").text == " world"

    # Paragraph 2: 1 text run.
    p2_runs = user_paras[1].findall(f"{{{HP}}}run")
    assert len(p2_runs) == 1
    assert p2_runs[0].find(f"{{{HP}}}t").text == "Just text."

    # Paragraph 3: 1 equation run.
    p3_runs = user_paras[2].findall(f"{{{HP}}}run")
    assert len(p3_runs) == 1
    assert p3_runs[0].find(f"{{{HP}}}equation") is not None


def test_write_mixed_equation_attributes_intact(tmp_path: Path) -> None:
    """Mixed-mode equations must still have treatAsChar=1 and the right attrs."""
    out = tmp_path / "mixed_attrs.hwpx"
    write_mixed(
        [[Text("see "), Equation(r"\alpha"), Text(".")]],
        str(out),
    )
    root = _read_section_xml(out)
    eq = root.find(f".//{{{HP}}}equation")
    assert eq is not None
    pos = eq.find(f"{{{NSMAP['hp']}}}pos")
    assert pos is not None and pos.get("treatAsChar") == "1"


def test_write_mixed_round_trip_via_hwpx2tex(tmp_path: Path) -> None:
    """Equations inside mixed paragraphs round-trip through hwpx2tex."""
    from hwpx_eq.hwpx_io.read import read_latex

    out = tmp_path / "rt.hwpx"
    write_mixed(
        [
            [Text("inline "), Equation(r"\frac{a}{b}"), Text(".")],
            [Equation(r"\sqrt{x}")],
        ],
        str(out),
    )
    assert read_latex(str(out)) == [r"\frac{a}{b}", r"\sqrt{x}"]


def test_write_mixed_text_only(tmp_path: Path) -> None:
    out = tmp_path / "text_only.hwpx"
    write_mixed([[Text("hello world")]], str(out))
    root = _read_section_xml(out)
    user_paras = _user_paragraphs(root)
    assert len(user_paras) == 1
    eqs = root.findall(f".//{{{HP}}}equation")
    assert eqs == []


# -------- write_mixed: tables --------


def test_write_mixed_with_table_creates_hp_tbl(tmp_path: Path) -> None:
    out = tmp_path / "tbl.hwpx"
    table = Table(
        rows=(
            ((Text("h1"),), (Text("h2"),)),
            ((Text("a"),), (Text("b"),)),
        ),
        has_header=True,
    )
    write_mixed([table], str(out))
    root = _read_section_xml(out)
    tbls = root.findall(f".//{{{HP}}}tbl")
    assert len(tbls) == 1
    tcs = tbls[0].findall(f".//{{{HP}}}tc")
    assert len(tcs) == 4  # 2 rows x 2 cols


def test_write_mixed_table_marks_header_row(tmp_path: Path) -> None:
    out = tmp_path / "tbl_header.hwpx"
    table = Table(
        rows=(
            ((Text("h1"),), (Text("h2"),)),
            ((Text("a"),), (Text("b"),)),
        ),
        has_header=True,
    )
    write_mixed([table], str(out))
    root = _read_section_xml(out)
    tbl = root.find(f".//{{{HP}}}tbl")
    rows = tbl.findall(f"{{{HP}}}tr")
    header_cells = rows[0].findall(f"{{{HP}}}tc")
    body_cells = rows[1].findall(f"{{{HP}}}tc")
    assert all(c.get("header") == "1" for c in header_cells)
    assert all(c.get("header") != "1" for c in body_cells)


def test_write_mixed_table_with_equation_cell(tmp_path: Path) -> None:
    out = tmp_path / "tbl_eq.hwpx"
    table = Table(
        rows=(
            ((Text("a"),), (Equation(r"x^2"),)),
        ),
        has_header=False,
    )
    write_mixed([table], str(out))
    root = _read_section_xml(out)
    cell_eqs = root.findall(f".//{{{HP}}}tc//{{{HP}}}equation")
    assert len(cell_eqs) == 1


def test_write_mixed_table_fills_printable_width(tmp_path: Path) -> None:
    """Tables should auto-resize to the printable area (page - left - right)."""
    out = tmp_path / "fit.hwpx"
    table = Table(
        rows=(
            ((Text("h1"),), (Text("h2"),), (Text("h3"),)),
            ((Text("a"),), (Text("b"),), (Text("c"),)),
        ),
        has_header=True,
    )
    write_mixed([table], str(out))
    root = _read_section_xml(out)
    page_pr = root.find(f"{{{HP}}}p/{{{HP}}}run/{{{HP}}}secPr/{{{HP}}}pagePr")
    if page_pr is None:
        # secPr may be elsewhere; fall back to the first pagePr in the section.
        page_pr = root.find(f".//{{{HP}}}pagePr")
    assert page_pr is not None
    page_w = int(page_pr.get("width"))
    margin = page_pr.find(f"{{{HP}}}margin")
    printable = page_w - int(margin.get("left")) - int(margin.get("right"))

    tbl = root.find(f".//{{{HP}}}tbl")
    sz = tbl.find(f"{{{HP}}}sz")
    assert int(sz.get("width")) == printable
    # Cell widths in each row sum to the printable width.
    for tr in tbl.findall(f"{{{HP}}}tr"):
        cell_widths = [int(c.get("width")) for c in tr.findall(f"{{{HP}}}tc/{{{HP}}}cellSz")]
        assert sum(cell_widths) == printable


def test_write_mixed_table_fills_narrow_page(tmp_path: Path) -> None:
    """When --page-width shrinks the page, tables should adapt accordingly."""
    out = tmp_path / "narrow.hwpx"
    table = Table(rows=(((Text("a"),), (Text("b"),)),), has_header=False)
    write_mixed([table], str(out), page_width_mm=100.0)
    root = _read_section_xml(out)
    page_pr = root.find(f".//{{{HP}}}pagePr")
    page_w = int(page_pr.get("width"))
    margin = page_pr.find(f"{{{HP}}}margin")
    printable = page_w - int(margin.get("left")) - int(margin.get("right"))

    tbl = root.find(f".//{{{HP}}}tbl")
    sz = tbl.find(f"{{{HP}}}sz")
    assert int(sz.get("width")) == printable


def test_write_mixed_paragraph_table_paragraph_order(tmp_path: Path) -> None:
    out = tmp_path / "ordered.hwpx"
    blocks = [
        Paragraph(segments=(Text("before"),)),
        Table(rows=(((Text("h"),),), ((Text("v"),),)), has_header=True),
        Paragraph(segments=(Text("after"),)),
    ]
    write_mixed(blocks, str(out))
    root = _read_section_xml(out)
    # All top-level <hp:p>: at least 3 user-authored ones in order plus
    # python-hwpx's placeholder. Verify existence and order of authored chunks
    # by scanning their text/tbl content.
    seq: list[str] = []
    for p in root.findall(f"{{{HP}}}p"):
        if p.find(f".//{{{HP}}}tbl") is not None:
            seq.append("table")
        else:
            ts = p.findall(f"{{{HP}}}run/{{{HP}}}t")
            for t in ts:
                if t.text and t.text.strip():
                    seq.append(t.text.strip())
                    break
    # Filter to only our authored items.
    authored = [s for s in seq if s in ("before", "after", "table")]
    assert authored == ["before", "table", "after"]
