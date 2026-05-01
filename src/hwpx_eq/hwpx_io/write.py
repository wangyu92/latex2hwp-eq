"""IR or LaTeX -> HWPX file.

Builds a fresh HWPX document with one paragraph per equation. Each paragraph
contains a single <hp:run> with an <hp:equation> child; the EQS payload lives
inside <hp:script> as CDATA. width/height are heuristic; HWP recomputes them
when opening.
"""

from __future__ import annotations

import os
from collections.abc import Iterable

from hwpx import HwpxDocument
from lxml import etree

from hwpx_eq.eqs.emit import emit as emit_eqs
from hwpx_eq.hwpx_io.ns import (
    EQUATION_DEFAULTS,
    HP,
    OUT_MARGIN_DEFAULTS,
    POS_DEFAULTS,
    SZ_DEFAULTS,
)
from hwpx_eq.ir import Node
from hwpx_eq.latex.extract import Equation, Segment, Text
from hwpx_eq.latex.parse import parse as parse_latex

DEFAULT_FONT_SIZE_PT = 10  # 한글 default body font size

# HWPUnit: 1 mm ≈ 283.465 (A4 = 210 mm = 59528 HWPUnit). Used for page geometry.
_HWPUNIT_PER_MM = 59528 / 210


def write_from_eqs(
    eqs_strings: Iterable[str],
    output_path: str,
    font_size_pt: int = DEFAULT_FONT_SIZE_PT,
    page_width_mm: float | None = None,
) -> None:
    doc = _new_doc()
    base_unit = _pt_to_base_unit(font_size_pt)
    for eqs in eqs_strings:
        _append_equation_paragraph(doc, eqs, base_unit=base_unit)
    if page_width_mm is not None:
        _set_page_width(doc, page_width_mm)
    _save(doc, output_path)


def write_from_latex(
    latex_sources: Iterable[str],
    output_path: str,
    font_size_pt: int = DEFAULT_FONT_SIZE_PT,
    page_width_mm: float | None = None,
) -> None:
    write_from_eqs(
        (emit_eqs(parse_latex(src)) for src in latex_sources),
        output_path,
        font_size_pt=font_size_pt,
        page_width_mm=page_width_mm,
    )


def write_from_ir(
    nodes: Iterable[Node],
    output_path: str,
    font_size_pt: int = DEFAULT_FONT_SIZE_PT,
    page_width_mm: float | None = None,
) -> None:
    write_from_eqs(
        (emit_eqs(n) for n in nodes),
        output_path,
        font_size_pt=font_size_pt,
        page_width_mm=page_width_mm,
    )


def write_mixed(
    paragraphs: Iterable[Iterable[Segment]],
    output_path: str,
    font_size_pt: int = DEFAULT_FONT_SIZE_PT,
    page_width_mm: float | None = None,
) -> None:
    """Write paragraphs of mixed Text/Equation segments to a .hwpx file.

    Each input paragraph becomes one <hp:p>; each segment becomes one
    <hp:run> child. Text runs hold a single <hp:t>; equation runs hold the
    same <hp:equation> tree produced by `_build_equation`.
    """
    doc = _new_doc()
    base_unit = _pt_to_base_unit(font_size_pt)
    for segments in paragraphs:
        _append_mixed_paragraph(doc, list(segments), base_unit=base_unit)
    if page_width_mm is not None:
        _set_page_width(doc, page_width_mm)
    _save(doc, output_path)


def _pt_to_base_unit(font_size_pt: int) -> int:
    """HWP baseUnit is in 1/100 pt. So 10pt -> 1000, 8pt -> 800, 15pt -> 1500."""
    return max(100, font_size_pt * 100)


def _set_page_width(doc: HwpxDocument, width_mm: float) -> None:
    """Override the section's page width and shrink side margins proportionally.

    Uses python-hwpx's section properties API so the change actually survives
    serialization. Side margins shrink with the page (clamped to ~3-15 mm).
    """
    width_hwp = int(width_mm * _HWPUNIT_PER_MM)
    side_mm = max(3.0, min(15.0, width_mm * 0.05))
    side_hwp = int(side_mm * _HWPUNIT_PER_MM)
    for section in doc.sections:
        section.properties.set_page_size(width=width_hwp)
        section.properties.set_page_margins(left=side_hwp, right=side_hwp)


def _new_doc() -> HwpxDocument:
    return HwpxDocument.new()


def _append_equation_paragraph(doc: HwpxDocument, eqs: str, base_unit: int) -> None:
    p = doc.add_paragraph("")
    run = p.element.find(f"{{{HP}}}run")
    if run is None:
        run = etree.SubElement(p.element, f"{{{HP}}}run")
        run.set("charPrIDRef", "0")
    for t in run.findall(f"{{{HP}}}t"):
        if not (t.text or "").strip():
            run.remove(t)
    run.append(_build_equation(eqs, base_unit=base_unit))


def _append_mixed_paragraph(
    doc: HwpxDocument, segments: list[Segment], base_unit: int
) -> None:
    p = doc.add_paragraph("")
    # Replace the placeholder run(s) with our own.
    for child in list(p.element):
        p.element.remove(child)
    for seg in segments:
        run = etree.SubElement(p.element, f"{{{HP}}}run")
        run.set("charPrIDRef", "0")
        if isinstance(seg, Text):
            t = etree.SubElement(run, f"{{{HP}}}t")
            t.text = seg.content
        elif isinstance(seg, Equation):
            eqs = emit_eqs(parse_latex(seg.latex))
            run.append(_build_equation(eqs, base_unit=base_unit))
        else:
            raise TypeError(f"unknown segment: {type(seg).__name__}")


def _build_equation(eqs: str, base_unit: int) -> etree._Element:
    eq = etree.SubElement(etree.Element("dummy", nsmap={"hp": HP}), f"{{{HP}}}equation")
    eq.getparent().remove(eq)
    for k, v in EQUATION_DEFAULTS.items():
        eq.set(k, v)
    eq.set("baseUnit", str(base_unit))

    width, height = _estimate_size(eqs, base_unit)
    sz = etree.SubElement(eq, f"{{{HP}}}sz")
    sz.set("width", str(width))
    sz.set("height", str(height))
    for k, v in SZ_DEFAULTS.items():
        sz.set(k, v)

    pos = etree.SubElement(eq, f"{{{HP}}}pos")
    for k, v in POS_DEFAULTS.items():
        pos.set(k, v)

    om = etree.SubElement(eq, f"{{{HP}}}outMargin")
    for k, v in OUT_MARGIN_DEFAULTS.items():
        om.set(k, v)

    script = etree.SubElement(eq, f"{{{HP}}}script")
    script.text = etree.CDATA(eqs)
    return eq


def _estimate_size(eqs: str, base_unit: int) -> tuple[int, int]:
    """Heuristic; HWP recomputes when opening. Scales with base_unit."""
    scale = base_unit / 800.0
    width = int(max(1500, min(12000, len(eqs) * 150)) * scale)
    tall_keywords = ("sum", "int", "prod", "matrix", "over", "sqrt", "root", "pile", "cases")
    height = int((1200 if any(k in eqs for k in tall_keywords) else 800) * scale)
    return width, height


def _save(doc: HwpxDocument, output_path: str) -> None:
    output_path = os.fspath(output_path)
    doc.save_to_path(output_path)
