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
DIGITS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]


def build(variable, out_dir, style, weight, tabular):
    font = instancer.instantiateVariableFont(TTFont(variable), {"wght": weight})
    name = "Manrope-%s%s" % (style, "-Tnum" if tabular else "")
    if tabular:
        for table in font["cmap"].tables:
            if table.isUnicode():
                for i, digit in enumerate(DIGITS):
                    if ord("0") + i in table.cmap:
                        table.cmap[ord("0") + i] = digit + ".tf"
    family = "Manrope %s%s" % (style, " Tnum" if tabular else "")
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
