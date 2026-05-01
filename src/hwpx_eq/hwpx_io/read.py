"""HWPX file -> EQS strings or LaTeX strings."""

from __future__ import annotations

import os
import zipfile
from collections.abc import Iterator

from lxml import etree

from hwpx_eq.eqs.parse import parse as parse_eqs
from hwpx_eq.hwpx_io.ns import HP
from hwpx_eq.latex.emit import emit as emit_latex
from hwpx_eq.latex.extract import Equation, Segment, Text


def iter_equations(hwpx_path: str) -> Iterator[str]:
    """Yield EQS script strings for every <hp:equation> in document order across sections."""
    hwpx_path = os.fspath(hwpx_path)
    with zipfile.ZipFile(hwpx_path) as zf:
        section_names = sorted(
            n for n in zf.namelist() if n.startswith("Contents/section") and n.endswith(".xml")
        )
        for name in section_names:
            with zf.open(name) as f:
                root = etree.parse(f).getroot()
            for eq in root.iter(f"{{{HP}}}equation"):
                script = eq.find(f"{{{HP}}}script")
                if script is not None and script.text:
                    yield script.text


def read_eqs(hwpx_path: str) -> list[str]:
    return list(iter_equations(hwpx_path))


def read_latex(hwpx_path: str) -> list[str]:
    return [emit_latex(parse_eqs(s)) for s in iter_equations(hwpx_path)]


def read_mixed(hwpx_path: str) -> list[list[Segment]]:
    """Walk the document and return paragraphs of Text/Equation segments.

    Text comes from <hp:t>, equations from <hp:equation><hp:script>. Empty
    paragraphs (e.g. python-hwpx's blank placeholder) are dropped. Consecutive
    Text segments inside one paragraph are merged into one.
    """
    hwpx_path = os.fspath(hwpx_path)
    paragraphs: list[list[Segment]] = []
    with zipfile.ZipFile(hwpx_path) as zf:
        section_names = sorted(
            n for n in zf.namelist() if n.startswith("Contents/section") and n.endswith(".xml")
        )
        for name in section_names:
            with zf.open(name) as f:
                root = etree.parse(f).getroot()
            for p in root.findall(f".//{{{HP}}}p"):
                segments = _segments_in_paragraph(p)
                if segments:
                    paragraphs.append(segments)
    return paragraphs


def _segments_in_paragraph(p: etree._Element) -> list[Segment]:
    out: list[Segment] = []
    for run in p.findall(f"{{{HP}}}run"):
        for child in run:
            tag = etree.QName(child).localname
            if tag == "t":
                if child.text:
                    out.append(Text(content=child.text))
            elif tag == "equation":
                script = child.find(f"{{{HP}}}script")
                if script is not None and script.text:
                    latex = emit_latex(parse_eqs(script.text))
                    out.append(Equation(latex=latex))
    return _merge_adjacent_text(out)


def _merge_adjacent_text(segs: list[Segment]) -> list[Segment]:
    out: list[Segment] = []
    for seg in segs:
        if isinstance(seg, Text) and out and isinstance(out[-1], Text):
            out[-1] = Text(content=out[-1].content + seg.content)
        else:
            out.append(seg)
    return out
