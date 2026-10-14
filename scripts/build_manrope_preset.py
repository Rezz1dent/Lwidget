#!/usr/bin/env python3
"""Breezy Minimal v29: Manrope, soft shadow, dimmed secondary rows, umbrella.

Usage: build_manrope_preset.py BASE.kwgt FONTS_DIR OUT.kwgt

BASE is the v28 preset (Breezy icons via Iconify). FONTS_DIR comes from
make_manrope_fonts.py. KWGT keys (fonts in fonts/ as kfile://, fx_shadow,
config_visible on an OverlapLayerModule) were taken from a preset exported
by KWGT after setting them in the editor.
"""
import copy
import json
import os
import sys
import time
import uuid
import zipfile

TITLE = "Breezy Minimal v33 • Manrope"
FONT = "kfile://org.kustom.provider/fonts/%s.ttf"
HOURS_FONT = "Manrope-ExtraBold-Tnum"
MINUTES_FONT = "Manrope-ExtraLight-Tnum"
TEMP_FONT = "Manrope-SemiBold"
ROW_FONT = "Manrope-Regular"
FONTS = [HOURS_FONT, MINUTES_FONT, TEMP_FONT, ROW_FONT]

WHITE = "#FFF9FBFF"
SECONDARY = "#B8FFFFFF"  # ~72% white
# Minimal shadow, tuned by hand in the KWGT editor (exported test preset):
# 41% black, distance 1, direction 15; blur 6 on the 70-size texts, 2 on the rows.
# Keep the blur small: KWGT grows the element's frame by the blur, which pushes the
# text down.
SHADOW_SIZE = 70.0
SHADOW_BLUR = 6


def shadow(size, distance=1, blur=None, direction=15):
    k = size / SHADOW_SIZE
    return {"fx_shadow": "OUTER",
            "fx_shadow_blur": blur if blur is not None else max(2, round(SHADOW_BLUR * min(k, 1))),
            "fx_shadow_direction": direction,
            "fx_shadow_distance": distance,
            "fx_shadow_color": "#68000000"}


MINUTES_SHADOW = {}
ICON_SHADOW = {"blur": 10, "direction": 0}
UMBRELLA_SHADOW = {"blur": 2}
# Raise everything so the content is centered in the widget frame (v31 sat ~18 low).
RAISE = 18.0


# Manrope's ascent is 0.138 em larger than the system font's: move the text up
# by that much so it sits where the system font did (and the last row is not cut).
ASCENT_SHIFT = 0.138
DEFAULT_TEXT_SIZE = 20.0

# Clock and current temperature: a bit larger than the original 70.
CLOCK_SIZE = 78.0
CLOCK_X = 40.0
# Middle rows (date, wind) moved down so they sit closer to the bottom rows.
MIDDLE_ROW_DOWN = 8.0
BIG_TEXTS = ("Clock • large", "Row 1 • Breezy temperature")
MIDDLE_ROWS = ("Date • next to alarm", "Row 2 • Like / arrow wind / humidity")
# Tabular digits are 0.62 em wide: "HH" is 1.24 * size.
MINUTES_X = CLOCK_X + round(1.24 * CLOCK_SIZE)

# Tomorrow's precipitation arrives as "60%": keep the digits for the comparison.
PRECIP = 'tc(reg, br(breezy, tomorrow_precip), "[^0-9]", "")'
RAIN = "%s >= 70" % PRECIP
UMBRELLA_WIDTH = 85


def main(base, fonts_dir, target):
    source = zipfile.ZipFile(base)
    preset = json.loads(source.read("preset.json").decode("utf-8"))
    info = preset["preset_info"]
    info["title"] = TITLE
    info["id"] = str(uuid.uuid4())
    info["ts"] = int(time.time() * 1000)
    info["description"] = (
        "Flat, transparent, two-column widget in Manrope (reboot the phone once after the "
        "first import so the home screen loads the fonts): bold hours, thin minutes, soft "
        "shadow, dimmed secondary rows. Umbrella with tomorrow's precipitation next to "
        "Tomorrow only when it is 70% or more. Weather icon: Material Design Icons as in "
        "Breezy Weather (Iconify mdi), data from Breezy Bridge 1.4+.")

    items = preset["preset_root"]["viewgroup_items"]
    by_title = {item.get("internal_title"): item for item in items}
    result = []
    for item in items:
        title = item.get("internal_title") or ""
        if title.startswith("Outline •"):
            continue  # replaced by the shadow
        if title == "Next alarm • next to date":
            continue  # merged into the date row: Manrope is wider, the rows would overlap
        if title in BIG_TEXTS:
            item["text_size"] = CLOCK_SIZE
        if title in MIDDLE_ROWS:
            item["position_offset_y"] = item.get("position_offset_y", 0.0) + MIDDLE_ROW_DOWN
        if item["internal_type"] == "TextModule":
            size = item.get("text_size", DEFAULT_TEXT_SIZE)
            item.update(shadow(size))
            item["position_offset_y"] = float(round(
                item.get("position_offset_y", 0.0) - ASCENT_SHIFT * size))
            item["text_family"] = FONT % ROW_FONT
            item["paint_color"] = SECONDARY
        if title == "Clock • large":
            item["internal_title"] = "Clock • hours"
            item["text_expression"] = "$df(HH)$"
            item["text_family"] = FONT % HOURS_FONT
            item["paint_color"] = WHITE
            item["position_offset_x"] = CLOCK_X
            minutes = copy.deepcopy(item)
            minutes["internal_title"] = "Clock • minutes"
            minutes["text_expression"] = '$df(":mm")$'
            minutes["text_family"] = FONT % MINUTES_FONT
            minutes.update(shadow(CLOCK_SIZE, **MINUTES_SHADOW))
            minutes["position_offset_x"] = float(MINUTES_X)
            result += [item, minutes]
            continue
        if title == "Date • next to alarm":
            item["internal_title"] = "Date + next alarm"
            alarm = by_title["Next alarm • next to date"]["text_expression"].strip()
            item["text_expression"] = (
                item["text_expression"][:-1] + ' + " " + ' + alarm[1:])
        if title == "Row 1 • Breezy temperature":
            item["text_family"] = FONT % TEMP_FONT
            item["paint_color"] = WHITE
        if title == "Row 3 • Tomorrow maximum/minimum":
            x = item.get("position_offset_x", 40.0)
            item.setdefault("internal_toggles", {})["position_offset_x"] = 10
            item.setdefault("internal_formulas", {})["position_offset_x"] = (
                "$if(%s, %d, %d)$" % (RAIN, x + UMBRELLA_WIDTH, x))
            umbrella_y = item.get("position_offset_y", 145.0)
            umbrella_x = x
        if item["internal_type"] == "FontIconModule":
            item.update(shadow(item.get("icon_size", 50.0), **ICON_SHADOW))
        result.append(item)

    row = by_title["Row 3 • Tomorrow maximum/minimum"]
    result.append({
        "internal_type": "OverlapLayerModule",
        "internal_title": "Umbrella • tomorrow precipitation ≥ 70%",
        "position_anchor": "TOPRIGHT",
        "position_offset_x": umbrella_x,
        "position_offset_y": umbrella_y,
        "internal_toggles": {"config_visible": 10},
        "internal_formulas": {"config_visible": "$if(%s, ALWAYS, REMOVE)$" % RAIN},
        "viewgroup_items": [
            dict({"internal_type": "FontIconModule",
                  "internal_title": "Umbrella icon",
                  "icon_set": "iconify://mdi?name=Material%20Design%20Icons",
                  "icon_icon": "umbrella-outline",
                  "icon_size": 22.0,
                  "paint_color": SECONDARY,
                  "position_anchor": "TOPLEFT",
                  }, **shadow(22.0, **UMBRELLA_SHADOW)),
            dict({"internal_type": "TextModule",
                  "internal_title": "Umbrella percent",
                  "text_expression": "$%s + \"%%\"$" % PRECIP,
                  "text_family": FONT % ROW_FONT,
                  "paint_color": SECONDARY,
                  "position_anchor": "TOPLEFT",
                  "position_offset_x": 26.0}, **shadow(DEFAULT_TEXT_SIZE)),
        ],
    })
    for key in ("internal_events",):
        if key in row:
            result[-1][key] = row[key]
    for item in result:
        if item["internal_type"] != "ShapeModule":
            item["position_offset_y"] = item.get("position_offset_y", 0.0) - RAISE
    preset["preset_root"]["viewgroup_items"] = result

    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as out:
        for entry in source.infolist():
            if entry.filename.startswith(("icons/", "fonts/")):
                continue
            data = source.read(entry.filename)
            if entry.filename == "preset.json":
                data = json.dumps(preset, ensure_ascii=False, indent=2).encode("utf-8")
            out.writestr(entry, data)
        template = source.getinfo("preset.json")
        for name in FONTS:
            entry = copy.copy(template)
            entry.filename = "fonts/%s.ttf" % name
            with open(os.path.join(fonts_dir, name + ".ttf"), "rb") as f:
                out.writestr(entry, f.read())


if __name__ == "__main__":
    main(*sys.argv[1:4])
