#!/usr/bin/env python3
"""Generate a stable KWGT preset with flat, individually anchored items.

The last experimental version created nested OverlapGroupModule objects and
displayed an empty widget on Android. This version deliberately uses only
the proven top-level modules from the existing working preset.
"""
import io
import json
import os
import urllib.request
import zipfile

URL = (
    "https://raw.githubusercontent.com/Rezz1dent/Lwidget/"
    "assets/kwgt-accuweather/kwgt/Minimal_Clock_AccuWeather_v2.kwgt"
)
with urllib.request.urlopen(URL, timeout=45) as response:
    base = response.read()

src = zipfile.ZipFile(io.BytesIO(base))
preset = json.loads(src.read("preset.json").decode("utf-8"))
root = preset["preset_root"]
items = root["viewgroup_items"]
assert len(items) == 8, f"Unexpected base preset item count {len(items)}"
assert all(item["internal_type"] in ("ShapeModule", "TextModule") for item in items)

background, clock, date, alarm, temp, icon, feels, condition = items

def place(item, anchor, x, y, size):
    item["position_anchor"] = anchor
    item["position_offset_x"] = float(x)
    item["position_offset_y"] = float(y)
    item["text_size"] = float(size)

# Keep the original shape and flat root structure because these have
# already been displayed successfully in KWGT on the user's Oppo.
clock["internal_title"] = "Clock • left"
place(clock, "TOPLEFT", 28, 12, 66)

# A SINGLE Kustom formula with the entire date format, no split expressions.
date["internal_title"] = "Date • weekday, day, month"
date["text_expression"] = '$df("EEE, dd MMM")$'
place(date, "TOPLEFT", 34, 98, 21)

# Always render something here so a missing Android next-alarm can be diagnosed.
# '◷ —' means Kustom has not received the next alarm from Android.
alarm["internal_title"] = "Next alarm • ◷ — if Android provides none"
alarm["text_expression"] = '$if(si(alarmon)=1, "◷ " + df("HH:mm", si(alarmd)), "◷ —")$'
place(alarm, "TOPLEFT", 34, 134, 18)

temp["internal_title"] = "Breezy • current temperature"
temp["text_expression"] = "$br(breezy, temp)$"
place(temp, "TOPRIGHT", 80, 21, 37)
temp["text_style"] = "BOLD"

icon["internal_title"] = "Breezy • weather symbol"
icon["text_expression"] = "$br(breezy, icon)$"
place(icon, "TOPRIGHT", 22, 22, 35)

feels["internal_title"] = "Breezy • feels like"
feels["text_expression"] = "$br(breezy, feels)$"
place(feels, "TOPRIGHT", 25, 79, 18)
feels.pop("text_size_type", None)
feels.pop("text_width", None)
feels.pop("text_max_lines", None)

condition["internal_title"] = "Breezy • current conditions"
condition["text_expression"] = "$tc(ell, br(breezy, condition), 17)$"
place(condition, "TOPRIGHT", 25, 118, 18)
condition.pop("text_size_type", None)
condition.pop("text_width", None)
condition.pop("text_max_lines", None)

# Completely transparent canvas while retaining the known-good rectangle shape.
background["paint_color"] = "#00000000"
background["internal_title"] = "Transparent background (0% opacity)"
# Some KWGT versions use the root background settings as well.
root["background_color"] = "#00000000"

# Readable but quiet palette: ivory for primary values, cool white for
# supporting information. Thin near-black strokes keep it legible on photos.
clock["paint_color"] = "#FFF7F9FF"
temp["paint_color"] = "#FFF7F9FF"
icon["paint_color"] = "#FFD5E9FF"
date["paint_color"] = "#FFE6EDF9"
alarm["paint_color"] = "#FFE0EAF7"
feels["paint_color"] = "#FFE6ECF5"
condition["paint_color"] = "#FFF0F4FB"

# Kustom's action payload format is shared by text and group modules.
# Explicit ACTION intent strings let Android pick the Clock / Calendar apps
# installed on the user's device, rather than hardcoding Google apps.
breezy_intent = (
    "intent:#Intent;action=android.intent.action.MAIN;"
    "category=android.intent.category.LAUNCHER;package=org.breezyweather;end"
)
clock_intent = "intent:#Intent;action=android.intent.action.SHOW_ALARMS;end"
calendar_intent = (
    "intent:#Intent;action=android.intent.action.MAIN;"
    "category=android.intent.category.APP_CALENDAR;end"
)

def tap(module, android_intent):
    module["internal_events"] = [
        dict(type="SINGLE_TAP", action="LAUNCH_APP", intent=android_intent)
    ]

for module in (temp, icon, feels, condition):
    tap(module, breezy_intent)
for module in (clock, alarm):
    tap(module, clock_intent)
tap(date, calendar_intent)

# Keep every existing item as a *top-level* module: the earlier experiment
# with nested Overlap Groups produced a blank widget on this OPPO launcher.
# A stroked duplicate is drawn under each original text at the exact same
# coordinates. This is a genuine subtle outline, not a blur over the text.
import copy
foreground = [clock, date, alarm, temp, icon, feels, condition]
outlines = []
for module in foreground:
    outline = copy.deepcopy(module)
    outline["internal_title"] = "Outline • " + module["internal_title"]
    outline["paint_color"] = "#B8000000"
    outline["paint_style"] = "STROKE"
    outline["paint_stroke"] = 1.8 if module in (clock, temp, icon) else 1.5
    outline.pop("internal_events", None)
    outlines.append(outline)
root["viewgroup_items"] = [background] + outlines + foreground

# Leave all original module types and the previously working background intact.
preset["preset_info"].update(
    title="Minimal Clock Breezy • Glassless v5",
    description="Transparent, stroked text, tap to open Breezy, Clock and Calendar.",
)
os.makedirs("dist", exist_ok=True)
out = "dist/Minimal_Clock_Breezy_Polished_v5.kwgt"
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as dest:
    for name in src.namelist():
        if name == "preset.json":
            dest.writestr(name, json.dumps(preset, ensure_ascii=False, separators=(",", ":")))
        else:
            dest.writestr(name, src.read(name))

with zipfile.ZipFile(out) as result:
    assert result.testzip() is None
    check = json.loads(result.read("preset.json"))
    flat = check["preset_root"]["viewgroup_items"]
    assert len(flat) == 15
    assert all(x["internal_type"] in ("TextModule", "ShapeModule") for x in flat)
    assert flat[0]["paint_color"] == "#00000000"
    assert sum(x.get("paint_style") == "STROKE" for x in flat) == 7
    assert all(x.get("paint_stroke", 0) <= 2.0 for x in flat if x.get("paint_style") == "STROKE")
    assert all("internal_events" in x for x in flat[8:])
    assert all("internal_events" not in x for x in flat[1:8])
    assert all(x["internal_events"][0]["action"] == "LAUNCH_APP" for x in flat[8:])
    assert "org.breezyweather" in flat[11]["internal_events"][0]["intent"]
    assert "SHOW_ALARMS" in flat[8]["internal_events"][0]["intent"]
    assert "APP_CALENDAR" in flat[9]["internal_events"][0]["intent"]
    assert flat[9]["text_expression"] == '$df("EEE, dd MMM")$'
    assert flat[10]["text_expression"].startswith("$if(si(alarmon)=1")
    assert flat[11]["position_anchor"] == "TOPRIGHT"
    for field in ("temp", "icon", "feels", "condition"):
        assert "br(breezy, " + field + ")" in json.dumps(check, ensure_ascii=False)
print("V5_STYLED_FLAT_KWGT_VERIFIED", [(x["internal_type"], x.get("internal_title", "")) for x in flat])
print("FILE", out, "SIZE", os.stat(out).st_size)
