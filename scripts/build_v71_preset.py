#!/usr/bin/env python3
"""Breezy Minimal v71: precipitation now between the wind and "like".

Usage: build_v71_preset.py BASE_v70.kwgt FONTS_DIR OUT.kwgt

Starts from the hand-tuned v70 (presets/Breezy_Minimal_v70__Manrope.kwgt):
- the wind row becomes a stack: wind | drop icon + mm (only while it rains, from the
  bridge's precip_now, Breezy Bridge 1.6+) | like;
- the temperature uses Manrope-Regular (same weight as v70's Manrope.ttf, with the
  narrow minus);
- fonts refreshed from FONTS_DIR (make_manrope_fonts.py).
"""
import copy
import json
import os
import sys
import time
import uuid
import zipfile

TITLE = "Breezy Minimal v7.1 • Manrope"
MDI = "iconify://mdi?name=Material%20Design%20Icons"
FONT = "kfile://org.kustom.provider/fonts/%s.ttf"
FONTS = ["Manrope-ExtraBold-Tnum", "Manrope-ExtraLight-Tnum", "Manrope-Regular"]

WIND = '$if(gv(maximal) = 1, "↖ 12,5 м/с", br(breezy, wind_arrow) + " " + br(breezy, wind_ms))$'
RAIN = '$if(gv(maximal) = 1, "12,5", br(breezy, precip_now))$'
RAIN_VISIBLE = '$if(gv(maximal) = 1 | br(breezy, precip_now) != "", ALWAYS, REMOVE)$'
LIKE = '$if(gv(maximal) = 1, "like -42°", "like " + br(breezy, like))$'


def strip(item, *prefixes):
    return {k: v for k, v in item.items() if k.startswith(prefixes)}


def text(style, title, expression):
    item = strip(style, "text_", "paint_", "fx_")
    item.update(internal_type="TextModule", internal_title=title, text_expression=expression)
    return item


def main(base, fonts_dir, target):
    source = zipfile.ZipFile(base)
    preset = json.loads(source.read("preset.json").decode("utf-8"))
    info = preset["preset_info"]
    info.update(title=TITLE, id=str(uuid.uuid4()), ts=int(time.time() * 1000))

    items = preset["preset_root"]["viewgroup_items"]
    by_title = {item.get("internal_title"): item for item in items}
    wind = by_title["Row 2 • Like / arrow wind / humidity"]
    umbrella_icon = None
    for item in items:
        for child in item.get("viewgroup_items", []):
            for leaf in child.get("viewgroup_items", []):
                if leaf.get("internal_title") == "Umbrella icon":
                    umbrella_icon = leaf

    drop = strip(umbrella_icon, "paint_", "fx_")
    drop.update(internal_type="FontIconModule", internal_title="Rain drop", icon_set=MDI,
                icon_icon="water-outline", icon_size=wind["text_size"] - 2)
    rain = {"internal_type": "StackLayerModule", "internal_title": "Rain now (only while it rains)",
            "config_stacking": "HORIZONTAL_CENTER", "config_margin": 1.0,
            "internal_toggles": {"config_visible": 10},
            "internal_formulas": {"config_visible": RAIN_VISIBLE},
            "viewgroup_items": [drop, text(wind, "Rain mm (precip_now)", RAIN)]}
    row = {"internal_type": "StackLayerModule", "internal_title": "Wind + rain now + like",
           "config_stacking": "HORIZONTAL_CENTER", "config_margin": 8.0,
           "position_anchor": wind["position_anchor"],
           "position_offset_x": wind["position_offset_x"],
           "position_offset_y": wind["position_offset_y"],
           "viewgroup_items": [text(wind, "Wind", WIND), rain, text(wind, "Like", LIKE)]}
    if "internal_events" in wind:
        row["internal_events"] = wind["internal_events"]
    items[items.index(wind)] = row

    temp = by_title["Row 1 • Breezy temperature"]
    if temp.get("text_family", "").endswith("/Manrope.ttf"):
        temp["text_family"] = FONT % "Manrope-Regular"

    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as out:
        for entry in source.infolist():
            if entry.filename.startswith("fonts/"):
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
