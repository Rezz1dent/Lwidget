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
place(clock, "TOPLEFT", 34, 19, 62)

# A SINGLE Kustom formula with the entire date format, no split expressions.
date["internal_title"] = "Date • weekday, day, month"
date["text_expression"] = '$df("EEE, dd MMM")$'
place(date, "TOPLEFT", 38, 108, 20)

# Always render something here so a missing Android next-alarm can be diagnosed.
# '◷ —' means Kustom has not received the next alarm from Android.
alarm["internal_title"] = "Next alarm • ◷ — if Android provides none"
alarm["text_expression"] = '$if(si(alarmon)=1, "◷ " + df("HH:mm", si(alarmd)), "◷ —")$'
place(alarm, "TOPLEFT", 38, 146, 17)

temp["internal_title"] = "Breezy • current temperature"
temp["text_expression"] = "$br(breezy, temp)$"
place(temp, "TOPRIGHT", 80, 29, 40)
temp["text_style"] = "BOLD"

icon["internal_title"] = "Breezy • weather symbol"
icon["text_expression"] = "$br(breezy, icon)$"
place(icon, "TOPRIGHT", 22, 32, 34)

feels["internal_title"] = "Breezy • feels like"
feels["text_expression"] = "$br(breezy, feels)$"
place(feels, "TOPRIGHT", 27, 87, 17)
feels.pop("text_size_type", None)
feels.pop("text_width", None)
feels.pop("text_max_lines", None)

condition["internal_title"] = "Breezy • current conditions"
condition["text_expression"] = "$tc(ell, br(breezy, condition), 17)$"
place(condition, "TOPRIGHT", 27, 121, 19)
condition.pop("text_size_type", None)
condition.pop("text_width", None)
condition.pop("text_max_lines", None)

# Completely transparent canvas while retaining the known-good rectangle shape.
background["paint_color"] = "#00000000"
background["internal_title"] = "Transparent background (0% opacity)"
# Some KWGT versions use the root background settings as well.
root["background_color"] = "#00000000"

# V6: Arctic Blue, a flat glassless design (there is deliberately NO panel).
# The translucent accents are only hairlines, all text remains legible on photos.
import copy

PRIMARY = "#FFFAFCFF"
ICE = "#FF9DDDFF"
SOFT = "#FFE1F3FF"
MUTED = "#FFC4D9EC"

clock["paint_color"] = PRIMARY
clock["text_family"] = "sans-serif-light"
clock["text_style"] = "NORMAL"
temp["paint_color"] = PRIMARY
temp["text_family"] = "sans-serif-medium"
temp["text_style"] = "BOLD"
icon["paint_color"] = ICE
date["paint_color"] = SOFT
date["text_family"] = "sans-serif-medium"
alarm["paint_color"] = MUTED
feels["paint_color"] = SOFT
condition["paint_color"] = PRIMARY
condition["text_family"] = "sans-serif-medium"

# Small editorial labels and extra Breezy v2 measurements. Missing bridge
# fields render as empty text and never overwrite core current conditions.
def text_from(template, title, expression, anchor, x, y, size, color):
    item = copy.deepcopy(template)
    item["internal_title"] = title
    item["text_expression"] = expression
    place(item, anchor, x, y, size)
    item["text_family"] = "sans-serif-medium"
    item["text_style"] = "NORMAL"
    item["paint_color"] = color
    for field in ("text_width", "text_size_type", "text_max_lines"):
        item.pop(field, None)
    return item

now_label = text_from(date, "Header • СЕЙЧАС", "СЕЙЧАС", "TOPRIGHT", 28, 7, 12, ICE)
brand_label = text_from(date, "Signature • BREEZY / LIVE", "●  BREEZY / LIVE",
                       "TOPLEFT", 38, 189, 13, ICE)
wind = text_from(feels, "Wind • Breezy bridge v2", "$br(breezy, wind_text)$",
                 "TOPRIGHT", 27, 158, 14, SOFT)
tomorrow = text_from(feels, "Tomorrow • Breezy bridge v2", "$br(breezy, tomorrow)$",
                     "TOPRIGHT", 27, 187, 13, MUTED)

# Four fine, non-interactive accent marks; no opaque widget background.
def bar(title, width, height, anchor, x, y, color):
    item = copy.deepcopy(background)
    item.update(
        internal_title=title, shape_type="RECT",
        shape_width=float(width), shape_height=float(height),
        shape_corners=float(min(height / 2.0, 3.0)),
        paint_color=color, paint_style="FILL",
        position_anchor=anchor,
        position_offset_x=float(x), position_offset_y=float(y)
    )
    item.pop("internal_events", None)
    return item

decorations = [
    bar("Accent • clock left rail", 3, 56, "TOPLEFT", 20, 31, "#FF85D4FF"),
    bar("Accent • left underline", 40, 2, "TOPLEFT", 38, 215, "#A685D4FF"),
    bar("Accent • weather top", 46, 2, "TOPRIGHT", 27, 4, "#FF85D4FF"),
    bar("Accent • weather bottom", 56, 2, "TOPRIGHT", 27, 216, "#A685D4FF"),
]

# Preserve verified KWGT touch syntax and original Android intents.
breezy_intent = (
    "intent:#Intent;action=android.intent.action.MAIN;"
    "category=android.intent.category.LAUNCHER;package=org.breezyweather;end"
)
clock_intent = "intent:#Intent;action=android.intent.action.SHOW_ALARMS;end"
calendar_intent = (
    "intent:#Intent;action=android.intent.action.MAIN;"
    "category=android.intent.category.APP_CALENDAR;end"
)

def tap(item, intent):
    item["internal_events"] = [
        dict(type="SINGLE_TAP", action="LAUNCH_APP", intent=intent)
    ]

for item in (temp, icon, feels, condition, wind, tomorrow, now_label, brand_label):
    tap(item, breezy_intent)
for item in (clock, alarm):
    tap(item, clock_intent)
tap(date, calendar_intent)

# Each text has a 1-2px stroke underneath. Root remains FLAT;
# nested groups were shown to import as a blank widget on the OPPO.
foreground = [
    clock, date, alarm, temp, icon, feels, condition,
    now_label, brand_label, wind, tomorrow
]
outlines = []
for item in foreground:
    stroke = copy.deepcopy(item)
    stroke["internal_title"] = "Outline • " + item["internal_title"]
    stroke["paint_color"] = "#BC050E1B"
    stroke["paint_style"] = "STROKE"
    stroke["paint_stroke"] = 1.65 if item in (clock, temp, icon) else 1.3
    stroke.pop("internal_events", None)
    outlines.append(stroke)

root["viewgroup_items"] = [background] + decorations + outlines + foreground
preset["preset_info"].update(
    title="Breezy Arctic • KWGT v6",
    description="Transparent arctic-blue clock/weather widget with accents, dark text outlines, touch actions and optional wind/tomorrow data.",
)

os.makedirs("dist", exist_ok=True)
out = "dist/Breezy_Arctic_KWGT_v6.kwgt"
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as dest:
    for name in src.namelist():
        if name == "preset.json":
            dest.writestr(name, json.dumps(preset, ensure_ascii=False, separators=(",", ":")))
        else:
            dest.writestr(name, src.read(name))

with zipfile.ZipFile(out) as archive:
    assert archive.testzip() is None
    check = json.loads(archive.read("preset.json"))
    modules = check["preset_root"]["viewgroup_items"]
    assert len(modules) == 27, len(modules)
    assert all(x["internal_type"] in ("TextModule", "ShapeModule") for x in modules)
    assert modules[0]["paint_color"] == "#00000000"
    assert sum(x.get("paint_style") == "STROKE" for x in modules) == 11
    assert sum(x.get("internal_events") is not None for x in modules) == 11
    assert all("internal_events" not in x for x in modules[1:16])
    for key in ("temp", "icon", "feels", "condition", "wind_text", "tomorrow"):
        assert "br(breezy, " + key + ")" in json.dumps(check, ensure_ascii=False)
    assert "SHOW_ALARMS" in json.dumps(check)
    assert "APP_CALENDAR" in json.dumps(check)
    assert "org.breezyweather" in json.dumps(check)
print("V6_ARCTIC_FLAT_PRESET_VERIFIED",
      [(x["internal_type"], x.get("internal_title", "")) for x in modules])
print("FILE", out, "SIZE", os.stat(out).st_size)
