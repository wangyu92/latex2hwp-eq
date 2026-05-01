from __future__ import annotations

import sys
from pathlib import Path

import click

from hwpx_eq import __version__
from hwpx_eq.hwpx_io.read import read_latex
from hwpx_eq.hwpx_io.write import write_from_latex
from hwpx_eq.latex.extract import extract as extract_latex_math


@click.group()
@click.version_option(__version__, prog_name="hwpx-eq")
def main() -> None:
    """LaTeX <-> HWPX equation converter."""


@main.command("tex2hwpx")
@click.argument("input_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("-o", "--output", type=click.Path(dir_okay=False, path_type=Path), default=None)
@click.option(
    "--mode",
    type=click.Choice(["block", "all"]),
    default="block",
    help="block: detect $...$ etc. all: treat entire file as one equation.",
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
    """Convert a LaTeX/Markdown file into a .hwpx with one paragraph per equation."""
    text = input_path.read_text(encoding="utf-8")
    equations = [text.strip()] if mode == "all" else extract_latex_math(text)
    if not equations:
        raise click.ClickException("no equations found (try --mode all)")
    if output is None:
        output = input_path.with_suffix(".hwpx")
    write_from_latex(
        equations, str(output), font_size_pt=font_size, page_width_mm=page_width
    )
    page_note = f", {page_width:g}mm wide" if page_width else ""
    click.echo(f"wrote {len(equations)} equation(s) at {font_size}pt{page_note} -> {output}")


@main.command("hwpx2tex")
@click.argument("input_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("-o", "--output", type=click.Path(dir_okay=False, path_type=Path), default=None)
@click.option(
    "--format",
    "out_format",
    type=click.Choice(["md", "tex", "plain"]),
    default="md",
    help="md: $$...$$ blocks. tex: \\[...\\] blocks. plain: one per line.",
)
def hwpx2tex_cmd(input_path: Path, output: Path | None, out_format: str) -> None:
    """Extract equations from a .hwpx file and emit LaTeX."""
    eqs = read_latex(str(input_path))
    if out_format == "md":
        body = "\n\n".join(f"$${e}$$" for e in eqs)
    elif out_format == "tex":
        body = "\n\n".join(f"\\[{e}\\]" for e in eqs)
    else:
        body = "\n".join(eqs)
    if output is None:
        sys.stdout.write(body + "\n")
    else:
        output.write_text(body + "\n", encoding="utf-8")
        click.echo(f"wrote {len(eqs)} equation(s) -> {output}")


if __name__ == "__main__":
    main()
