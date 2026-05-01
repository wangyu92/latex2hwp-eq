"""Verify generated HWPX files have valid structure and embedded equations."""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest
from lxml import etree

from hwpx_eq.hwpx_io.ns import HP, NSMAP
from hwpx_eq.hwpx_io.write import write_from_eqs, write_from_latex


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
