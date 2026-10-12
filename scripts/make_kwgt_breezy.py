#!/usr/bin/env python3
"""KWGT v9: balanced three-line typography and colors with three weather rows and two outline icons.

Keeps the known-good top-level Kustom module structure (no nested OverlapGroups).
Data is supplied exclusively by the Breezy -> KWGT mini bridge v3.
"""
import copy
import io
import json
import os
import urllib.request
import zipfile

URL = (
    "https://raw.githubusercontent.com/Rezz1dent/Lwidget/"
    "assets/kwgt-accuweather/kwgt/Minimal_Clock_AccuWeather_v2.kwgt"
)
with urllib.request.urlopen(URL, timeout=50) as response:
    raw = response.read()
archive = zipfile.ZipFile(io.BytesIO(raw))
preset = json.loads(archive.read("preset.json").decode("utf-8"))
root = preset["preset_root"]
original = root["viewgroup_items"]
assert len(original) == 8, len(original)
assert all(item["internal_type"] in ("ShapeModule", "TextModule") for item in original)
background, clock, date, alarm, temp, original_icon, feels, condition = original

COLOR_MAIN = "#FFF9FBFF"
COLOR_ICE = "#FFD7EDFF"
COLOR_SOFT = "#FFC6D7E7"
BLACK_OUTLINE = "#BF06111D"
BREEZY = (
    "intent:#Intent;action=android.intent.action.MAIN;"
    "category=android.intent.category.LAUNCHER;package=org.breezyweather;end"
)
CLOCK = "intent:#Intent;action=android.intent.action.SHOW_ALARMS;end"
CALENDAR = (
    "intent:#Intent;action=android.intent.action.MAIN;"
    "category=android.intent.category.APP_CALENDAR;end"
)

def arrange(item, title, expr, anchor, x, y, size, color):
    item["internal_title"] = title
    item["text_expression"] = expr
    item["position_anchor"] = anchor
    item["position_offset_x"] = float(x)
    item["position_offset_y"] = float(y)
    item["text_size"] = float(size)
    item["paint_color"] = color
    item["text_family"] = "sans-serif-medium"
    for key in ("text_width", "text_size_type", "text_max_lines"):
        item.pop(key, None)
    return item

def tap(item, target):
    item["internal_events"] = [
        {"type": "SINGLE_TAP", "action": "LAUNCH_APP", "intent": target}
    ]
    return item

# Left column:
# 1) Clock, 2) date AND alarm side by side, 3) today's high/low.
arrange(clock, "Clock • large", "$df(HH:mm)$", "TOPLEFT", 30, 21, 62, COLOR_MAIN)
clock["text_family"] = "sans-serif-light"
tap(clock, CLOCK)

arrange(date, "Date • next to alarm", '$df("EEE, dd MMM")$',
        "TOPLEFT", 30, 101, 16, COLOR_ICE)
tap(date, CALENDAR)

arrange(alarm, "Next alarm • next to date",
        '$if(si(alarmon)=1, "◷ " + df("HH:mm", si(alarmd)), "◷ —")$',
        "TOPLEFT", 121, 101, 15, COLOR_SOFT)
tap(alarm, CLOCK)

today = arrange(copy.deepcopy(feels), "Today • Breezy high/low",
                "$br(breezy, today_compact)$",
                "TOPLEFT", 30, 139, 17, COLOR_SOFT)
tap(today, BREEZY)

# Right column, exactly 3 lines:
# current temp + outline icon, Like/wind/droplet, tomorrow max/min + outline icon.
arrange(temp, "Row 1 • Breezy temperature", "$br(breezy, temp)$",
        "TOPRIGHT", 79, 32, 40, COLOR_MAIN)
temp["text_style"] = "BOLD"
tap(temp, BREEZY)

details = arrange(feels, "Row 2 • Like / arrow wind / humidity",
                  "$tc(reg, br(breezy, details), \"м/с\", \" м/с\")$", "TOPRIGHT", 27, 102, 13.5, COLOR_ICE)
tap(details, BREEZY)

tomorrow = arrange(condition, "Row 3 • Tomorrow maximum/minimum",
                   "$br(breezy, tomorrow_compact)$",
                   "TOPRIGHT", 72, 139, 17, COLOR_SOFT)
tap(tomorrow, BREEZY)

# Vector glyphs built into KWGT (Material icon pack). The icon name comes
# from Breezy weather codes via the mini bridge; no colored emoji involved.
def font_icon(title, expression, x, y, size):
    module = {
        "internal_type": "FontIconModule",
        "internal_title": title,
        "icon_set": "kfile://org.kustom.widget.provider/icons/material.ttf",
        "icon_icon": "cloud_queue",
        "icon_size": float(size),
        "position_anchor": "TOPRIGHT",
        "position_offset_x": float(x),
        "position_offset_y": float(y),
        "paint_color": COLOR_MAIN,
        "internal_toggles": {"icon_icon": 10},
        "internal_formulas": {"icon_icon": expression},
    }
    tap(module, BREEZY)
    return module

current_glyph = font_icon("Row 1 • Flat outline current weather",
                          "$br(breezy, icon_flat)$", 28, 37, 31)
tomorrow_glyph = font_icon("Row 3 • Flat outline tomorrow weather",
                           '$if(br(breezy, tomorrow_icon_flat)="grain", "cloud_queue", br(breezy, tomorrow_icon_flat))$', 28, 137, 23)

# Match the tomorrow glyph with the pale-blue third-row text instead of
# displaying it in stark white. Current weather stays brighter above.
tomorrow_glyph["paint_color"] = COLOR_SOFT

# Fully transparent root, the proven shape object is retained as a backing
# item for Kustom's importer but draws absolutely nothing.
background["internal_title"] = "Transparent background"
background["paint_color"] = "#00000000"
root["background_color"] = "#00000000"
root["background_type"] = "SOLID"

texts = [clock, date, alarm, today, temp, details, tomorrow]
outlines = []
for item in texts:
    copy_item = copy.deepcopy(item)
    copy_item["internal_title"] = "Outline • " + item["internal_title"]
    copy_item["paint_style"] = "STROKE"
    copy_item["paint_stroke"] = 1.65 if item in (clock, temp) else 1.25
    copy_item["paint_color"] = BLACK_OUTLINE
    copy_item.pop("internal_events", None)
    outlines.append(copy_item)

root["viewgroup_items"] = [background] + outlines + texts + [
    current_glyph, tomorrow_glyph
]
preset["preset_info"].update(
    title="Breezy Minimal v9 • Balanced",
    description=(
        "Flat, transparent, two-column widget. Date+alarm on one line; "
        "Today high/low below. Right: temperature, Like+wind+humidity, "
        "Tomorrow high/low. Dynamic flat Kustom weather icons."
    )
)

out = "dist/Breezy_Minimal_Balanced_v9.kwgt"
os.makedirs("dist", exist_ok=True)
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as output:
    for name in archive.namelist():
        if name == "preset.json":
            output.writestr(
                name, json.dumps(preset, ensure_ascii=False, separators=(",", ":"))
            )
        else:
            output.writestr(name, archive.read(name))

with zipfile.ZipFile(out) as result:
    assert result.testzip() is None
    obj = json.loads(result.read("preset.json"))
    m = obj["preset_root"]["viewgroup_items"]
    assert len(m) == 17, len(m)
    assert sum(item["internal_type"] == "FontIconModule" for item in m) == 2
    assert sum(item.get("paint_style") == "STROKE" for item in m) == 7
    assert sum("internal_events" in item for item in m) == 9
    assert all(item["internal_type"] in ("TextModule", "ShapeModule", "FontIconModule") for item in m)
    assert m[0]["paint_color"] == "#00000000"
    assert m[9]["position_offset_y"] == m[10]["position_offset_y"]  # date and alarm
    # Match actual ColorOS / KWGT editor geometry from the screenshot.
    # Left date and alarm share one top offset; both bottom labels share another.
    assert m[9]["position_offset_y"] == m[10]["position_offset_y"] == 101
    assert m[11]["position_offset_y"] == m[14]["position_offset_y"] == 139
    assert m[10]["position_offset_x"] == 121
    assert m[13]["position_offset_y"] == 102
    assert m[13]["text_size"] == 13.5
    assert m[16]["position_offset_y"] == 137
    assert m[16]["paint_color"] == COLOR_SOFT
    assert m[15]["paint_color"] == COLOR_MAIN
    assert 'tc(reg' in m[13]["text_expression"]
    assert "cloud_queue" in m[16]["internal_formulas"]["icon_icon"]
    expressions = json.dumps(obj, ensure_ascii=False)
    for variable in (
        "temp", "details", "today_compact", "tomorrow_compact",
        "icon_flat", "tomorrow_icon_flat"
    ):
        assert f"br(breezy, {variable})" in expressions, variable
    assert "cloud_queue" in expressions and "material.ttf" in expressions
    assert "org.breezyweather" in expressions
    assert "SHOW_ALARMS" in expressions and "APP_CALENDAR" in expressions
    assert "BREEZY / LIVE" not in expressions
print("V9_PRESET_VALIDATED", [(x["internal_type"], x.get("internal_title")) for x in m])
print("FILE", out, os.stat(out).st_size, "bytes")
, 28, 137, 23)

# Match the tomorrow glyph with the pale-blue third-row text instead of
# displaying it in stark white. Current weather stays brighter above.
tomorrow_glyph["paint_color"] = COLOR_SOFT

# Fully transparent root, the proven shape object is retained as a backing
# item for Kustom's importer but draws absolutely nothing.
background["internal_title"] = "Transparent background"
background["paint_color"] = "#00000000"
root["background_color"] = "#00000000"
root["background_type"] = "SOLID"

texts = [clock, date, alarm, today, temp, details, tomorrow]
outlines = []
for item in texts:
    copy_item = copy.deepcopy(item)
    copy_item["internal_title"] = "Outline • " + item["internal_title"]
    copy_item["paint_style"] = "STROKE"
    copy_item["paint_stroke"] = 1.65 if item in (clock, temp) else 1.25
    copy_item["paint_color"] = BLACK_OUTLINE
    copy_item.pop("internal_events", None)
    outlines.append(copy_item)

root["viewgroup_items"] = [background] + outlines + texts + [
    current_glyph, tomorrow_glyph
]
preset["preset_info"].update(
    title="Breezy Minimal v9 • Balanced",
    description=(
        "Flat, transparent, two-column widget. Date+alarm on one line; "
        "Today high/low below. Right: temperature, Like+wind+humidity, "
        "Tomorrow high/low. Dynamic flat Kustom weather icons."
    )
)

out = "dist/Breezy_Minimal_Balanced_v9.kwgt"
os.makedirs("dist", exist_ok=True)
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as output:
    for name in archive.namelist():
        if name == "preset.json":
            output.writestr(
                name, json.dumps(preset, ensure_ascii=False, separators=(",", ":"))
            )
        else:
            output.writestr(name, archive.read(name))

with zipfile.ZipFile(out) as result:
    assert result.testzip() is None
    obj = json.loads(result.read("preset.json"))
    m = obj["preset_root"]["viewgroup_items"]
    assert len(m) == 17, len(m)
    assert sum(item["internal_type"] == "FontIconModule" for item in m) == 2
    assert sum(item.get("paint_style") == "STROKE" for item in m) == 7
    assert sum("internal_events" in item for item in m) == 9
    assert all(item["internal_type"] in ("TextModule", "ShapeModule", "FontIconModule") for item in m)
    assert m[0]["paint_color"] == "#00000000"
    assert m[9]["position_offset_y"] == m[10]["position_offset_y"]  # date and alarm
    # Match actual ColorOS / KWGT editor geometry from the screenshot.
    # Left date and alarm share one top offset; both bottom labels share another.
    assert m[9]["position_offset_y"] == m[10]["position_offset_y"] == 101
    assert m[11]["position_offset_y"] == m[14]["position_offset_y"] == 139
    assert m[10]["position_offset_x"] == 121
    assert m[13]["position_offset_y"] == 102
    assert m[13]["text_size"] == 13.5
    assert m[16]["position_offset_y"] == 137
    assert m[16]["paint_color"] == COLOR_SOFT
    assert m[15]["paint_color"] == COLOR_MAIN
    assert 'tc(reg' in m[13]["text_expression"]
    assert "cloud_queue" in m[16]["internal_formulas"]["icon_icon"]
    expressions = json.dumps(obj, ensure_ascii=False)
    for variable in (
        "temp", "details", "today_compact", "tomorrow_compact",
        "icon_flat", "tomorrow_icon_flat"
    ):
        assert f"br(breezy, {variable})" in expressions, variable
    assert "cloud_queue" in expressions and "material.ttf" in expressions
    assert "org.breezyweather" in expressions
    assert "SHOW_ALARMS" in expressions and "APP_CALENDAR" in expressions
    assert "BREEZY / LIVE" not in expressions
print("V9_PRESET_VALIDATED", [(x["internal_type"], x.get("internal_title")) for x in m])
print("FILE", out, os.stat(out).st_size, "bytes")
