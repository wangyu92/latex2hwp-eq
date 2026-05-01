from __future__ import annotations

import sys
from pathlib import Path

import click

from hwpx_eq import __version__
from hwpx_eq.hwpx_io.read import read_latex, read_mixed
from hwpx_eq.hwpx_io.write import write_from_latex, write_mixed
from hwpx_eq.latex.extract import (
    Equation,
    Text,
    extract_segments,
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
        paragraphs = extract_segments(text)
        if not paragraphs:
            raise click.ClickException("input is empty")
        write_mixed(
            paragraphs, str(output), font_size_pt=font_size, page_width_mm=page_width
        )
        n_eq = sum(1 for p in paragraphs for s in p if isinstance(s, Equation))
        click.echo(
            f"wrote {len(paragraphs)} paragraph(s), {n_eq} equation(s) at {font_size}pt"
            f"{page_note} -> {output}"
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
        paragraphs = read_mixed(str(input_path))
        body = _format_mixed(paragraphs, out_format)
        n_para = len(paragraphs)
        n_eq = sum(1 for p in paragraphs for s in p if isinstance(s, Equation))
        summary = f"{n_para} paragraph(s), {n_eq} equation(s)"
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


def _format_mixed(paragraphs: list[list], out_format: str) -> str:
    """Render mixed-mode paragraphs. Display equations get block delimiters;
    inline equations (paragraph mixes text with at least one equation) get
    inline delimiters. Plain mode uses bare LaTeX with no delimiters.
    """
    out_paragraphs: list[str] = []
    for para in paragraphs:
        only_eq = len(para) == 1 and isinstance(para[0], Equation)
        parts: list[str] = []
        for seg in para:
            if isinstance(seg, Text):
                parts.append(seg.content)
                continue
            # Equation
            if out_format == "plain":
                parts.append(seg.latex)
            elif out_format == "tex":
                parts.append(f"\\[{seg.latex}\\]" if only_eq else f"\\({seg.latex}\\)")
            else:  # md
                parts.append(f"$${seg.latex}$$" if only_eq else f"${seg.latex}$")
        out_paragraphs.append("".join(parts))
    return "\n\n".join(out_paragraphs)


if __name__ == "__main__":
    main()
