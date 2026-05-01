from click.testing import CliRunner

from hwpx_eq.cli import main


def test_help_runs() -> None:
    result = CliRunner().invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "tex2hwpx" in result.output
    assert "hwpx2tex" in result.output


def test_version_runs() -> None:
    result = CliRunner().invoke(main, ["--version"])
    assert result.exit_code == 0
