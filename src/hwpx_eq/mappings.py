"""Single source of truth for token mappings.

Each entry: (canonical_name, latex_text, eqs_text). Derived dicts at the bottom
provide lookups in both directions. Add a token here and both directions update.

`latex_text` contains the leading backslash for commands. ASCII operators like
'+' have the same `latex_text` and `eqs_text`.
"""

from __future__ import annotations

GREEK: list[tuple[str, str, str]] = [
    # lowercase
    ("alpha", r"\alpha", "alpha"),
    ("beta", r"\beta", "beta"),
    ("gamma", r"\gamma", "gamma"),
    ("delta", r"\delta", "delta"),
    ("epsilon", r"\epsilon", "epsilon"),
    ("varepsilon", r"\varepsilon", "varepsilon"),
    ("zeta", r"\zeta", "zeta"),
    ("eta", r"\eta", "eta"),
    ("theta", r"\theta", "theta"),
    ("vartheta", r"\vartheta", "vartheta"),
    ("iota", r"\iota", "iota"),
    ("kappa", r"\kappa", "kappa"),
    ("lambda", r"\lambda", "lambda"),
    ("mu", r"\mu", "mu"),
    ("nu", r"\nu", "nu"),
    ("xi", r"\xi", "xi"),
    ("pi", r"\pi", "pi"),
    ("varpi", r"\varpi", "varpi"),
    ("rho", r"\rho", "rho"),
    ("varrho", r"\varrho", "varrho"),
    ("sigma", r"\sigma", "sigma"),
    ("varsigma", r"\varsigma", "varsigma"),
    ("tau", r"\tau", "tau"),
    ("upsilon", r"\upsilon", "upsilon"),
    ("phi", r"\phi", "phi"),
    ("varphi", r"\varphi", "varphi"),
    ("chi", r"\chi", "chi"),
    ("psi", r"\psi", "psi"),
    ("omega", r"\omega", "omega"),
    # uppercase (EQS uses Title case; verify against hwp ground-truth)
    ("Gamma", r"\Gamma", "Gamma"),
    ("Delta", r"\Delta", "Delta"),
    ("Theta", r"\Theta", "Theta"),
    ("Lambda", r"\Lambda", "Lambda"),
    ("Xi", r"\Xi", "Xi"),
    ("Pi", r"\Pi", "Pi"),
    ("Sigma", r"\Sigma", "Sigma"),
    ("Upsilon", r"\Upsilon", "Upsilon"),
    ("Phi", r"\Phi", "Phi"),
    ("Psi", r"\Psi", "Psi"),
    ("Omega", r"\Omega", "Omega"),
]

# Binary/unary operators and relations.
OPERATORS: list[tuple[str, str, str]] = [
    ("plus", "+", "+"),
    ("minus", "-", "-"),
    ("eq", "=", "="),
    ("lt", "<", "<"),
    ("gt", ">", ">"),
    ("comma", ",", ","),
    ("semicolon", ";", ";"),
    ("colon", ":", ":"),
    ("times", r"\times", "times"),
    ("div", r"\div", "div"),
    ("cdot", r"\cdot", "cdot"),
    ("pm", r"\pm", "pm"),
    ("mp", r"\mp", "mp"),
    ("ast", r"\ast", "ast"),
    ("star", r"\star", "star"),
    ("circ", r"\circ", "circ"),
    ("bullet", r"\bullet", "bullet"),
    ("oplus", r"\oplus", "oplus"),
    ("ominus", r"\ominus", "ominus"),
    ("otimes", r"\otimes", "otimes"),
    ("le", r"\le", "<="),
    ("ge", r"\ge", ">="),
    ("ne", r"\ne", "!="),
    ("approx", r"\approx", "~="),
    ("equiv", r"\equiv", "=="),
    ("sim", r"\sim", "sim"),
    ("propto", r"\propto", "propto"),
    ("in", r"\in", "in"),
    ("notin", r"\notin", "notin"),
    ("subset", r"\subset", "subset"),
    ("supset", r"\supset", "supset"),
    ("cup", r"\cup", "cup"),
    ("cap", r"\cap", "cap"),
    ("forall", r"\forall", "forall"),
    ("exists", r"\exists", "exists"),
    ("infty", r"\infty", "inf"),
    ("partial", r"\partial", "partial"),
    ("nabla", r"\nabla", "nabla"),
    ("rightarrow", r"\rightarrow", "->"),
    ("leftarrow", r"\leftarrow", "<-"),
    ("leftrightarrow", r"\leftrightarrow", "<->"),
    ("Rightarrow", r"\Rightarrow", "=>"),
    ("Leftarrow", r"\Leftarrow", "<="),  # collides with le; resolved by parse context
    ("to", r"\to", "->"),
]

FUNCS: list[tuple[str, str, str]] = [
    ("sin", r"\sin", "sin"),
    ("cos", r"\cos", "cos"),
    ("tan", r"\tan", "tan"),
    ("cot", r"\cot", "cot"),
    ("sec", r"\sec", "sec"),
    ("csc", r"\csc", "csc"),
    ("arcsin", r"\arcsin", "arcsin"),
    ("arccos", r"\arccos", "arccos"),
    ("arctan", r"\arctan", "arctan"),
    ("sinh", r"\sinh", "sinh"),
    ("cosh", r"\cosh", "cosh"),
    ("tanh", r"\tanh", "tanh"),
    ("log", r"\log", "log"),
    ("ln", r"\ln", "ln"),
    ("exp", r"\exp", "exp"),
    ("max", r"\max", "max"),
    ("min", r"\min", "min"),
    ("det", r"\det", "det"),
    ("dim", r"\dim", "dim"),
    ("gcd", r"\gcd", "gcd"),
    ("mod", r"\mod", "mod"),
]

BIGOPS: list[tuple[str, str, str]] = [
    ("sum", r"\sum", "sum"),
    ("int", r"\int", "int"),
    ("prod", r"\prod", "prod"),
    ("lim", r"\lim", "lim"),
    ("oint", r"\oint", "oint"),
    ("iint", r"\iint", "iint"),
    ("iiint", r"\iiint", "iiint"),
    ("bigcup", r"\bigcup", "bigcup"),
    ("bigcap", r"\bigcap", "bigcap"),
]

DECORATORS: list[tuple[str, str, str]] = [
    ("hat", r"\hat", "hat"),
    ("widehat", r"\widehat", "widehat"),
    ("bar", r"\bar", "bar"),
    ("overline", r"\overline", "overline"),
    ("vec", r"\vec", "vec"),
    ("dot", r"\dot", "dot"),
    ("ddot", r"\ddot", "ddot"),
    ("tilde", r"\tilde", "tilde"),
    ("widetilde", r"\widetilde", "widetilde"),
    ("check", r"\check", "check"),
    ("acute", r"\acute", "acute"),
    ("grave", r"\grave", "grave"),
]

# Delimiter pairs for \left/\right.
DELIMS: list[tuple[str, str]] = [
    ("(", "("),
    (")", ")"),
    ("[", "["),
    ("]", "]"),
    (r"\{", "{"),
    (r"\}", "}"),
    ("|", "|"),
    (r"\|", "||"),
    (".", "."),  # \left. invisible delim
]


def _bidir(
    table: list[tuple[str, str, str]],
) -> tuple[dict[str, str], dict[str, str], dict[str, str], dict[str, str]]:
    latex_to_name: dict[str, str] = {}
    eqs_to_name: dict[str, str] = {}
    name_to_latex: dict[str, str] = {}
    name_to_eqs: dict[str, str] = {}
    for name, latex, eqs in table:
        # latex/eqs may be ambiguous across categories; first writer wins per dict.
        # Use category-scoped dicts when ambiguity matters.
        latex_to_name.setdefault(latex, name)
        eqs_to_name.setdefault(eqs, name)
        name_to_latex.setdefault(name, latex)
        name_to_eqs.setdefault(name, eqs)
    return latex_to_name, eqs_to_name, name_to_latex, name_to_eqs


GREEK_LATEX, GREEK_EQS, GREEK_NAME_LATEX, GREEK_NAME_EQS = _bidir(GREEK)
OP_LATEX, OP_EQS, OP_NAME_LATEX, OP_NAME_EQS = _bidir(OPERATORS)
FUNC_LATEX, FUNC_EQS, FUNC_NAME_LATEX, FUNC_NAME_EQS = _bidir(FUNCS)
BIGOP_LATEX, BIGOP_EQS, BIGOP_NAME_LATEX, BIGOP_NAME_EQS = _bidir(BIGOPS)
DEC_LATEX, DEC_EQS, DEC_NAME_LATEX, DEC_NAME_EQS = _bidir(DECORATORS)

DELIM_LATEX_TO_EQS = {latex: eqs for latex, eqs in DELIMS}
DELIM_EQS_TO_LATEX = {eqs: latex for latex, eqs in DELIMS}
