from hwpx_eq.latex.extract import (
    Equation,
    Paragraph,
    Table,
    Text,
    extract,
    extract_blocks,
    extract_segments,
)


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


# -------- extract_blocks: tables --------


def test_blocks_simple_table() -> None:
    src = "| h1 | h2 |\n|---|---|\n| a | b |"
    blocks = extract_blocks(src)
    assert len(blocks) == 1
    tbl = blocks[0]
    assert isinstance(tbl, Table)
    assert tbl.has_header is True
    assert tbl.rows == (
        ((Text("h1"),), (Text("h2"),)),
        ((Text("a"),), (Text("b"),)),
    )


def test_blocks_table_with_equation_in_cell() -> None:
    src = "| a | b |\n|---|---|\n| 1 | $x^2$ |"
    blocks = extract_blocks(src)
    assert len(blocks) == 1
    tbl = blocks[0]
    assert isinstance(tbl, Table)
    assert tbl.rows[1][1] == (Equation(latex="x^2"),)


def test_blocks_table_alignment_marker_ignored() -> None:
    src = "| a | b |\n|:---|---:|\n| 1 | 2 |"
    blocks = extract_blocks(src)
    assert isinstance(blocks[0], Table)


def test_blocks_paragraph_table_paragraph() -> None:
    src = "Intro text.\n\n| h | k |\n|---|---|\n| 1 | 2 |\n\nAfter."
    blocks = extract_blocks(src)
    assert len(blocks) == 3
    assert isinstance(blocks[0], Paragraph) and blocks[0].segments == (Text("Intro text."),)
    assert isinstance(blocks[1], Table)
    assert isinstance(blocks[2], Paragraph) and blocks[2].segments == (Text("After."),)


def test_blocks_pipe_in_equation_does_not_break_table_detection() -> None:
    # An equation containing `|` should not be mistaken for a table cell.
    src = "value $|x|$ here.\n\n| a | b |\n|---|---|\n| 1 | 2 |"
    blocks = extract_blocks(src)
    assert len(blocks) == 2
    assert isinstance(blocks[0], Paragraph)
    assert any(isinstance(s, Equation) for s in blocks[0].segments)
    assert isinstance(blocks[1], Table)


def test_blocks_malformed_table_falls_back_to_paragraph() -> None:
    # Missing delimiter row → not a table.
    src = "| h1 | h2 |\n| a | b |"
    blocks = extract_blocks(src)
    assert len(blocks) == 1
    assert isinstance(blocks[0], Paragraph)


def test_blocks_table_with_uneven_rows_pads_to_header() -> None:
    src = "| h1 | h2 | h3 |\n|---|---|---|\n| 1 | 2 |"
    blocks = extract_blocks(src)
    tbl = blocks[0]
    assert isinstance(tbl, Table)
    # Header has 3 cols, data row has 2 → padded to 3.
    assert len(tbl.rows[1]) == 3
