HP = "http://www.hancom.co.kr/hwpml/2011/paragraph"
HC = "http://www.hancom.co.kr/hwpml/2011/core"
HH = "http://www.hancom.co.kr/hwpml/2011/head"
HS = "http://www.hancom.co.kr/hwpml/2011/section"

NSMAP = {"hp": HP, "hc": HC, "hh": HH, "hs": HS}

# Defaults below match what 한글 itself emits when saving an equation as
# 글자처럼 취급 (treat as character, inline-flowing). Verified against
# tests/fixtures/golden_hwpx/01_frac.hwpx and friends. Note: <hp:sz>,
# <hp:pos>, <hp:outMargin>, <hp:script> all use the *paragraph* namespace
# (hp), not core (hc) — python-hwpx silently drops foreign-namespace
# children, so getting this wrong causes 한글 to fall back to default
# treatAsChar="0" (floating object) instead of inline.

EQUATION_DEFAULTS = {
    "numberingType": "EQUATION",
    "textWrap": "TOP_AND_BOTTOM",
    "textFlow": "BOTH_SIDES",
    "lock": "0",
    "dropcapstyle": "None",
    "version": "Equation Version 60",
    "baseLine": "65",
    "textColor": "#000000",
    "lineMode": "CHAR",
    "font": "HancomEQN",
}
# baseUnit is overridden per-call by font_size_pt (1pt = 100 baseUnit).

POS_DEFAULTS = {
    "treatAsChar": "1",
    "affectLSpacing": "0",
    "flowWithText": "1",
    "allowOverlap": "0",
    "holdAnchorAndSO": "0",
    "vertRelTo": "PARA",
    "horzRelTo": "PARA",
    "vertAlign": "TOP",
    "horzAlign": "LEFT",
    "vertOffset": "0",
    "horzOffset": "0",
}

SZ_DEFAULTS = {
    "widthRelTo": "ABSOLUTE",
    "heightRelTo": "ABSOLUTE",
    "protect": "0",
}

OUT_MARGIN_DEFAULTS = {"left": "56", "right": "56", "top": "0", "bottom": "0"}
