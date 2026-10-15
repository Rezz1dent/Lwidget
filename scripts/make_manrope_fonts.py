#!/usr/bin/env python3
"""Static Manrope weights for the KWGT preset, from the variable font of google/fonts.

Usage: make_manrope_fonts.py Manrope[wght].ttf OUT_DIR

The clock fonts (*-Tnum) map the digits to Manrope's tabular figures (zero.tf...),
so "HH" always has the same width and the minutes can sit at a fixed position.
Requires: pip install fonttools
"""
import os
import sys

from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

WEIGHTS = [("ExtraLight", 200, True), ("Regular", 400, False),
           ("SemiBold", 600, False), ("ExtraBold", 800, True)]
# Light with spacer glyphs for the weekday word (see add_spacers).
SPACED = ("Light", 300)
SPACER_FIRST = 0xE100
SPACER_STEP = 4      # font units per step (unitsPerEm 2000 -> 0.002 em)
SPACER_COUNT = 450   # up to 0.9 em
DIGITS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]


def add_spacers(font):
    """Empty glyphs U+E100+k with advance k * SPACER_STEP: exact letter spacing in KWGT,
    which has no letter-spacing setting for text."""
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    cmaps = [t for t in font["cmap"].tables if t.isUnicode()]
    for k in range(1, SPACER_COUNT + 1):
        name = "spacer%d" % k
        font["glyf"][name] = TTGlyphPen(None).glyph()
        font["hmtx"][name] = (k * SPACER_STEP, 0)
        for table in cmaps:
            table.cmap[SPACER_FIRST + k] = name
    font.setGlyphOrder(font["glyf"].glyphOrder)


def build(variable, out_dir, style, weight, tabular, spacers=False):
    font = instancer.instantiateVariableFont(TTFont(variable), {"wght": weight})
    if spacers:
        add_spacers(font)
    name = "Manrope-%s%s" % (style, "-Tnum" if tabular else "-Spaced" if spacers else "")
    if tabular:
        for table in font["cmap"].tables:
            if table.isUnicode():
                for i, digit in enumerate(DIGITS):
                    if ord("0") + i in table.cmap:
                        table.cmap[ord("0") + i] = digit + ".tf"
    family = "Manrope %s%s" % (style, " Tnum" if tabular else " Spaced" if spacers else "")
    for record in font["name"].names:
        if record.nameID in (1, 4):
            record.string = family
        elif record.nameID == 2:
            record.string = "Regular"
        elif record.nameID == 6:
            record.string = name
        elif record.nameID == 16:
            record.string = "Manrope"
        elif record.nameID == 17:
            record.string = style
    font.save(os.path.join(out_dir, name + ".ttf"))
    return name


if __name__ == "__main__":
    os.makedirs(sys.argv[2], exist_ok=True)
    for style, weight, tabular in WEIGHTS:
        print(build(sys.argv[1], sys.argv[2], style, weight, tabular))
    print(build(sys.argv[1], sys.argv[2], SPACED[0], SPACED[1], False, spacers=True))
