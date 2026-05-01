from hwpx_eq import mappings as M


def test_greek_roundtrip_by_name() -> None:
    for name, latex, eqs in M.GREEK:
        assert M.GREEK_NAME_LATEX[name] == latex
        assert M.GREEK_NAME_EQS[name] == eqs
        assert M.GREEK_LATEX[latex] == name
        assert M.GREEK_EQS[eqs] == name


def test_operators_roundtrip_by_name() -> None:
    # Some EQS strings collide between categories (e.g. '<='); guarded with setdefault.
    # Within OPERATORS we still expect name→text to be deterministic.
    for name, latex, eqs in M.OPERATORS:
        assert M.OP_NAME_LATEX[name] == latex
        assert M.OP_NAME_EQS[name] == eqs


def test_funcs_bigops_decorators_have_unique_names() -> None:
    for cat in [M.FUNCS, M.BIGOPS, M.DECORATORS]:
        names = [n for n, _, _ in cat]
        assert len(names) == len(set(names)), f"duplicate name in {cat[0]}…"


def test_categories_do_not_overlap_on_canonical_name() -> None:
    seen: dict[str, str] = {}
    for cat_name, cat in [
        ("greek", M.GREEK),
        ("op", M.OPERATORS),
        ("func", M.FUNCS),
        ("bigop", M.BIGOPS),
        ("dec", M.DECORATORS),
    ]:
        for name, _, _ in cat:
            assert name not in seen, f"{name} duplicated in {seen[name]} and {cat_name}"
            seen[name] = cat_name


def test_specific_known_mappings() -> None:
    assert M.GREEK_LATEX[r"\alpha"] == "alpha"
    assert M.GREEK_NAME_EQS["Omega"] == "Omega"
    assert M.OP_NAME_LATEX["le"] == r"\le"
    assert M.OP_NAME_EQS["le"] == "<="
    assert M.BIGOP_NAME_LATEX["sum"] == r"\sum"
    assert M.OP_NAME_EQS["infty"] == "inf"
