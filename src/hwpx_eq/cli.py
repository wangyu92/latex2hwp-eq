from __future__ import annotations

import sys
from pathlib import Path

import click

from hwpx_eq import __version__
from hwpx_eq.hwpx_io.read import read_latex, read_mixed
from hwpx_eq.hwpx_io.write import write_from_latex, write_mixed
from hwpx_eq.latex.extract import (
    Block,
    Equation,
    Paragraph,
    Table,
    Text,
    extract_blocks,
)
from hwpx_eq.latex.extract import (
    extract as extract_latex_math,
)


@click.group()
@click.version_option(__version__, prog_name="hwpx-eq")
def main() -> None:
    """LaTeX <-> HWPX equation converter."""


@main.command("tex2hwpx")
@click.argument("input_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("-o", "--output", type=click.Path(dir_okay=False, path_type=Path), default=None)
@click.option(
    "--mode",
    type=click.Choice(["block", "all", "mixed"]),
    default="block",
    help=(
        "block: equations only, one per paragraph. "
        "all: treat entire file as one equation. "
        "mixed: keep body text + equations inline, blank lines separate paragraphs."
    ),
)
@click.option(
    "--font-size",
    type=click.IntRange(min=4, max=72),
    default=10,
    help="Equation font size in points (default 10).",
)
@click.option(
    "--page-width",
    type=click.FloatRange(min=20.0, max=420.0),
    default=None,
    help="Page width in mm. Default: A4 (210mm). Try 100 for a narrow equation list.",
)
def tex2hwpx_cmd(
    input_path: Path,
    output: Path | None,
    mode: str,
    font_size: int,
    page_width: float | None,
) -> None:
    """Convert a LaTeX/Markdown file into a .hwpx file."""
    text = input_path.read_text(encoding="utf-8")
    if output is None:
        output = input_path.with_suffix(".hwpx")
    page_note = f", {page_width:g}mm wide" if page_width else ""

    if mode == "mixed":
        blocks = extract_blocks(text)
        if not blocks:
            raise click.ClickException("input is empty")
        write_mixed(
            blocks, str(output), font_size_pt=font_size, page_width_mm=page_width
        )
        n_para = sum(1 for b in blocks if isinstance(b, Paragraph))
        n_table = sum(1 for b in blocks if isinstance(b, Table))
        n_eq = _count_equations(blocks)
        table_note = f", {n_table} table(s)" if n_table else ""
        click.echo(
            f"wrote {n_para} paragraph(s){table_note}, {n_eq} equation(s)"
            f" at {font_size}pt{page_note} -> {output}"
        )
        return

    equations = [text.strip()] if mode == "all" else extract_latex_math(text)
    if not equations:
        raise click.ClickException("no equations found (try --mode all or --mode mixed)")
    write_from_latex(
        equations, str(output), font_size_pt=font_size, page_width_mm=page_width
    )
    click.echo(f"wrote {len(equations)} equation(s) at {font_size}pt{page_note} -> {output}")


@main.command("hwpx2tex")
@click.argument("input_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("-o", "--output", type=click.Path(dir_okay=False, path_type=Path), default=None)
@click.option(
    "--mode",
    type=click.Choice(["equations", "mixed"]),
    default="equations",
    help=(
        "equations: just the equations, one per block. "
        "mixed: preserve surrounding text and paragraph structure."
    ),
)
@click.option(
    "--format",
    "out_format",
    type=click.Choice(["md", "tex", "plain"]),
    default="md",
    help="md: $...$/$$...$$. tex: \\(...\\)/\\[...\\]. plain: no math delimiters.",
)
def hwpx2tex_cmd(
    input_path: Path, output: Path | None, mode: str, out_format: str
) -> None:
    """Extract LaTeX (and optionally surrounding text) from a .hwpx file."""
    if mode == "mixed":
        blocks = read_mixed(str(input_path))
        body = _format_mixed(blocks, out_format)
        n_para = sum(1 for b in blocks if isinstance(b, Paragraph))
        n_table = sum(1 for b in blocks if isinstance(b, Table))
        n_eq = _count_equations(blocks)
        table_note = f", {n_table} table(s)" if n_table else ""
        summary = f"{n_para} paragraph(s){table_note}, {n_eq} equation(s)"
    else:
        eqs = read_latex(str(input_path))
        if out_format == "md":
            body = "\n\n".join(f"$${e}$$" for e in eqs)
        elif out_format == "tex":
            body = "\n\n".join(f"\\[{e}\\]" for e in eqs)
        else:
            body = "\n".join(eqs)
        summary = f"{len(eqs)} equation(s)"

    if output is None:
        sys.stdout.write(body + "\n")
    else:
        output.write_text(body + "\n", encoding="utf-8")
        click.echo(f"wrote {summary} -> {output}")


def _format_mixed(blocks: list[Block], out_format: str) -> str:
    """Render Block list as md/tex/plain text.

    Display equations (paragraph with only one equation) get block delimiters;
    inline equations get inline delimiters. Tables become GFM pipe tables in
    md/plain output and a same-shape table in tex output (still pipe form).
    Plain mode emits bare LaTeX without `$...$` markers.
    """
    rendered: list[str] = []
    for block in blocks:
        if isinstance(block, Paragraph):
            rendered.append(_format_paragraph(block, out_format))
        elif isinstance(block, Table):
            rendered.append(_format_table(block, out_format))
    return "\n\n".join(rendered)


def _format_paragraph(para: Paragraph, out_format: str) -> str:
    only_eq = len(para.segments) == 1 and isinstance(para.segments[0], Equation)
    parts: list[str] = []
    for seg in para.segments:
        if isinstance(seg, Text):
            parts.append(seg.content)
            continue
        if out_format == "plain":
            parts.append(seg.latex)
        elif out_format == "tex":
            parts.append(f"\\[{seg.latex}\\]" if only_eq else f"\\({seg.latex}\\)")
        else:  # md
            parts.append(f"$${seg.latex}$$" if only_eq else f"${seg.latex}$")
    return "".join(parts)


def _format_table(table: Table, out_format: str) -> str:
    """Emit a GFM pipe table. Cells render their inline segments — equations
    always get inline delimiters since cells can't host display math.
    """
    if not table.rows:
        return ""

    def cell_text(cell_segs: tuple) -> str:
        parts: list[str] = []
        for seg in cell_segs:
            if isinstance(seg, Text):
                parts.append(seg.content)
            else:  # Equation
                if out_format == "plain":
                    parts.append(seg.latex)
                elif out_format == "tex":
                    parts.append(f"\\({seg.latex}\\)")
                else:
                    parts.append(f"${seg.latex}$")
        return " ".join(p.strip() for p in parts).strip() or " "

    cols = max(len(r) for r in table.rows)
    rows_text: list[list[str]] = []
    for row in table.rows:
        cells = [cell_text(row[c]) if c < len(row) else " " for c in range(cols)]
        rows_text.append(cells)

    # GFM requires a header row. If the source has none, emit a blank one.
    if table.has_header:
        header = rows_text[0]
        body_rows = rows_text[1:]
    else:
        header = [" "] * cols
        body_rows = rows_text

    lines = [
        "| " + " | ".join(header) + " |",
        "|" + "|".join(["---"] * cols) + "|",
    ]
    for row in body_rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def _count_equations(blocks: list[Block]) -> int:
    n = 0
    for block in blocks:
        if isinstance(block, Paragraph):
            n += sum(1 for s in block.segments if isinstance(s, Equation))
        elif isinstance(block, Table):
            for row in block.rows:
                for cell in row:
                    n += sum(1 for s in cell if isinstance(s, Equation))
    return n


if __name__ == "__main__":
    main()
