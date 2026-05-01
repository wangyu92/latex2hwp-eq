from hwpx_eq.latex.extract import extract


def test_dollar_inline() -> None:
    assert extract("text $a + b$ more") == ["a + b"]


def test_double_dollar_block() -> None:
    assert extract("intro $$\\frac{a}{b}$$ tail") == [r"\frac{a}{b}"]


def test_paren_and_bracket() -> None:
    assert extract(r"x \(a\) y \[b\] z") == ["a", "b"]


def test_equation_environment() -> None:
    assert extract(r"\begin{equation} x + y \end{equation}") == ["x + y"]


def test_multiple_in_order() -> None:
    src = "$x$ then $$\\frac{1}{2}$$ end $y$"
    assert extract(src) == ["x", r"\frac{1}{2}", "y"]


def test_no_double_count() -> None:
    # $$ should not also match as two $...$
    assert extract("$$a$$") == ["a"]
