from hwpx_eq.ir import BigOp, Char, Frac, Greek, Op, SupSub, seq


def test_nodes_are_hashable_and_equal() -> None:
    a = Frac(Char("a"), Char("b"))
    b = Frac(Char("a"), Char("b"))
    assert a == b
    assert hash(a) == hash(b)


def test_seq_helper() -> None:
    g = seq(Char("a"), Op("plus"), Char("b"))
    assert len(g.items) == 3


def test_nested_supsub_with_bigop() -> None:
    # \sum_{i=1}^{n} a_i
    inner = SupSub(BigOp("sum"), sup=Char("n"), sub=seq(Char("i"), Op("eq"), Char("1")))
    assert isinstance(inner, SupSub)
    assert isinstance(inner.base, BigOp)


def test_greek_is_distinct() -> None:
    assert Greek("alpha") != Char("alpha")
