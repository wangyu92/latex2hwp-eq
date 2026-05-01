"""HWPX file -> EQS strings or LaTeX strings."""

from __future__ import annotations

import os
import zipfile
from collections.abc import Iterator

from lxml import etree

from hwpx_eq.eqs.parse import parse as parse_eqs
from hwpx_eq.hwpx_io.ns import HP
from hwpx_eq.latex.emit import emit as emit_latex


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
