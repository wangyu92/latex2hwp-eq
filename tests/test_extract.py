from hwpx_eq.latex.extract import Equation, Text, extract, extract_segments


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


# -------- extract_segments --------


def test_segments_simple_inline() -> None:
    paras = extract_segments("Hello $a+b$ world")
    assert paras == [[Text("Hello "), Equation("a+b"), Text(" world")]]


def test_segments_two_paragraphs() -> None:
    paras = extract_segments("First $a$.\n\nSecond $b$.")
    assert paras == [
        [Text("First "), Equation("a"), Text(".")],
        [Text("Second "), Equation("b"), Text(".")],
    ]


def test_segments_no_equations() -> None:
    paras = extract_segments("Hello world.\n\nSecond para.")
    assert paras == [[Text("Hello world.")], [Text("Second para.")]]


def test_segments_no_text() -> None:
    paras = extract_segments("$a$\n\n$b$")
    assert paras == [[Equation("a")], [Equation("b")]]


def test_segments_collapses_intra_para_whitespace() -> None:
    # Single newlines and runs of spaces collapse to one space.
    paras = extract_segments("line one\nline two   end")
    assert paras == [[Text("line one line two end")]]


def test_segments_strips_paragraph_boundary_whitespace() -> None:
    # Trailing whitespace at paragraph end shouldn't leak as a Text segment.
    paras = extract_segments("alpha   \n\n   beta")
    assert paras == [[Text("alpha")], [Text("beta")]]


def test_segments_multiple_blank_lines() -> None:
    paras = extract_segments("a\n\n\n\nb")
    assert paras == [[Text("a")], [Text("b")]]


def test_segments_equation_then_blank_then_equation() -> None:
    paras = extract_segments("$a$\n\nthen\n\n$b$")
    assert paras == [
        [Equation("a")],
        [Text("then")],
        [Equation("b")],
    ]


def test_segments_preserves_inter_segment_space() -> None:
    paras = extract_segments("name $x$.")
    # Space before $x$ must be preserved in the Text segment.
    assert paras == [[Text("name "), Equation("x"), Text(".")]]


def test_segments_empty_input() -> None:
    assert extract_segments("") == []


def test_segments_whitespace_only_input() -> None:
    assert extract_segments("   \n\n   ") == []
