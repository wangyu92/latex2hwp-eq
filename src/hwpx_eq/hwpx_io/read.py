"""HWPX file -> EQS strings or LaTeX strings."""

from __future__ import annotations

import os
import zipfile
from collections.abc import Iterator

from lxml import etree

from hwpx_eq.eqs.parse import parse as parse_eqs
from hwpx_eq.hwpx_io.ns import HP
from hwpx_eq.latex.emit import emit as emit_latex
from hwpx_eq.latex.extract import Block, Equation, Paragraph, Segment, Table, Text


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


def read_mixed(hwpx_path: str) -> list[Block]:
    """Walk the document and return Paragraph and Table blocks in order.

    Top-level paragraphs become Paragraph blocks. A paragraph that hosts an
    <hp:tbl> (python-hwpx puts each table inside its own <hp:p>) becomes a
    Table block. Empty placeholder paragraphs are dropped.
    """
    hwpx_path = os.fspath(hwpx_path)
    blocks: list[Block] = []
    with zipfile.ZipFile(hwpx_path) as zf:
        section_names = sorted(
            n for n in zf.namelist() if n.startswith("Contents/section") and n.endswith(".xml")
        )
        for name in section_names:
            with zf.open(name) as f:
                root = etree.parse(f).getroot()
            # Only iterate direct <hp:p> children of the section so we don't
            # double-count paragraphs nested inside table cells.
            for p in root.findall(f"{{{HP}}}p"):
                tbl_elem = p.find(f".//{{{HP}}}tbl")
                if tbl_elem is not None:
                    blocks.append(_table_from_element(tbl_elem))
                    continue
                segments = _segments_in_paragraph(p)
                if segments:
                    blocks.append(Paragraph(segments=tuple(segments)))
    return blocks


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


def _table_from_element(tbl: etree._Element) -> Table:
    """Build a Table IR block from a <hp:tbl> XML element."""
    rows: list[tuple[tuple[Segment, ...], ...]] = []
    has_header = False
    tr_elements = tbl.findall(f"{{{HP}}}tr")
    for r_idx, tr in enumerate(tr_elements):
        tcs = tr.findall(f"{{{HP}}}tc")
        if r_idx == 0 and tcs and all(tc.get("header") == "1" for tc in tcs):
            has_header = True
        row: list[tuple[Segment, ...]] = []
        for tc in tcs:
            cell_segs: list[Segment] = []
            # Cell paragraphs live in <hp:subList>/<hp:p>.
            for cell_p in tc.findall(f"{{{HP}}}subList/{{{HP}}}p"):
                cell_segs.extend(_segments_in_paragraph(cell_p))
            row.append(tuple(_merge_adjacent_text(cell_segs)))
        rows.append(tuple(row))
    return Table(rows=tuple(rows), has_header=has_header)


def _merge_adjacent_text(segs: list[Segment]) -> list[Segment]:
    out: list[Segment] = []
    for seg in segs:
        if isinstance(seg, Text) and out and isinstance(out[-1], Text):
            out[-1] = Text(content=out[-1].content + seg.content)
        else:
            out.append(seg)
    return out
