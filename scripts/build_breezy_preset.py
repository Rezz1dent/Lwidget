#!/usr/bin/env python3
"""Build the Breezy Minimal KWGT preset with a combined icon font.

Usage: build_breezy_preset.py BASE.kwgt OUT.kwgt

Takes a preset that bundles the Meteo icon font (icons/meteo.ttf + meteo.json),
adds the Breezy Weather widget icons (Material Design Icons, Apache-2.0, see
scripts/mdi_weather_icons.json) as extra glyphs, stores the result as
the same icons/meteo.ttf + meteo.json and points the weather icon at
$br(breezy, icon_glyph)$, so the bridge decides the style (filled, outline, Breezy).

Requires: pip install fonttools
"""
import copy
import io
import json
import os
import sys
import time
import uuid
import zipfile

from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.svgLib.path import parse_path
from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
# Keep the file name and internal font name of the original Meteo font: KWGT showed
# "?" on the home screen for the same font saved as icons/breezy_icons.ttf
# (fine in the editor), while icons/meteo.ttf is known to work.
FONT_NAME = "meteo"
FIRST_CODE = 0xE980
TITLE = "Breezy Minimal v25 • Icons"
ICON_FORMULA = "$br(breezy, icon_glyph)$"
# MDI glyphs leave more padding than Meteo ones: enlarge them around the center
# so that switching the style keeps a similar visual size.
MDI_ZOOM = 1.12


def build_font(meteo_ttf, meteo_json, mdi):
    font = TTFont(io.BytesIO(meteo_ttf))
    em = font["head"].unitsPerEm
    ascent = font["hhea"].ascent
    box = mdi["viewBox"]
    scale = em / box
    k = MDI_ZOOM
    shift = (1 - k) * box / 2
    selection = json.loads(meteo_json)
    cmaps = [t for t in font["cmap"].tables if t.isUnicode()]
    max_order = max(i["properties"]["order"] for i in selection["icons"])
    max_id = max(i["properties"]["id"] for i in selection["icons"])

    for n, (name, icon) in enumerate(sorted(mdi["icons"].items())):
        code = FIRST_CODE + n
        glyph_name = "uni%04X" % code
        # SVG (y down, 24 units) -> font units (y up, baseline at 0, ascent on top).
        tt_pen = TTGlyphPen(None)
        pen = TransformPen(Cu2QuPen(tt_pen, max_err=1.0, reverse_direction=True),
                           (scale * k, 0, 0, -scale * k, scale * shift, ascent - scale * shift))
        for d in icon["paths"]:
            parse_path(d, pen)
        glyph = tt_pen.glyph()
        glyph.recalcBounds(font["glyf"])
        font["glyf"][glyph_name] = glyph
        font["hmtx"][glyph_name] = (em, getattr(glyph, "xMin", 0))
        for table in cmaps:
            table.cmap[code] = glyph_name

        svg = SVGPathPen(None)
        json_pen = TransformPen(svg, (scale * k, 0, 0, scale * k, scale * shift, scale * shift))
        for d in icon["paths"]:
            parse_path(d, json_pen)
        selection["icons"].append({
            "icon": {"paths": [svg.getCommands()], "attrs": [{}], "grid": 24,
                     "tags": [name], "isMulticolor": False, "isMulticolor2": False},
            "attrs": [{}],
            "properties": {"order": max_order + 1 + n, "id": max_id + 1 + n,
                           "prevSize": 32, "code": code, "name": name},
            "setIdx": 0, "setId": 0, "iconIdx": max_id + 1 + n,
        })

    # glyf[...] = glyph already appended the names to the glyph order.
    font.setGlyphOrder(font["glyf"].glyphOrder)
    out = io.BytesIO()
    font.save(out)
    return out.getvalue(), json.dumps(selection, indent="\t").encode("utf-8")


def main(base, target):
    with open(os.path.join(HERE, "mdi_weather_icons.json"), encoding="utf-8") as f:
        mdi = json.load(f)
    source = zipfile.ZipFile(base)
    ttf, selection = build_font(source.read("icons/meteo.ttf"),
                                source.read("icons/meteo.json"), mdi)

    preset = json.loads(source.read("preset.json").decode("utf-8"))
    info = preset["preset_info"]
    info["title"] = TITLE
    info["id"] = str(uuid.uuid4())
    info["ts"] = int(time.time() * 1000)
    info["description"] = (
        "Flat, transparent, two-column widget. Date+alarm on one line; Today high/low below. "
        "Right: temperature, Like+wind+humidity, Tomorrow high/low. Weather icon style "
        "(filled, outline, Breezy) is chosen in Breezy Bridge 1.3+. Icons: Meteo font and "
        "Material Design Icons by Pictogrammers (Apache-2.0).")
    icons = 0
    for item in preset["preset_root"]["viewgroup_items"]:
        if "icon_set" in item and "icon_icon" in item.get("internal_formulas", {}):
            item["icon_set"] = "kfile://org.kustom.provider/icons/%s.ttf" % FONT_NAME
            item["internal_formulas"]["icon_icon"] = ICON_FORMULA
            item["internal_title"] = "Row 1 • Current weather icon (style from bridge)"
            icons += 1
    assert icons == 1, icons

    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as out:
        for entry in source.infolist():
            if entry.filename.startswith("icons/%s." % FONT_NAME):
                continue
            data = source.read(entry.filename)
            if entry.filename == "preset.json":
                data = json.dumps(preset, ensure_ascii=False, indent=2).encode("utf-8")
            out.writestr(entry, data)
        for ext, data in (("ttf", ttf), ("json", selection)):
            entry = copy.copy(source.getinfo("icons/meteo." + ext))
            entry.filename = "icons/%s.%s" % (FONT_NAME, ext)
            out.writestr(entry, data)


if __name__ == "__main__":
    main(*sys.argv[1:3])
