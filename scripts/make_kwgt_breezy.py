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

# Leave all original module types and the previously working background intact.
preset["preset_info"].update(
    title="Minimal Clock Breezy • Aligned v4",
    description="Flat KWGT layout, left/right anchors, date, next alarm and Breezy bridge variables.",
)
os.makedirs("dist", exist_ok=True)
out = "dist/Minimal_Clock_Breezy_Aligned_v4.kwgt"
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
    assert len(flat) == 8
    assert all(x["internal_type"] in ("TextModule", "ShapeModule") for x in flat)
    assert flat[2]["text_expression"] == '$df("EEE, dd MMM")$'
    assert flat[3]["text_expression"].startswith("$if(si(alarmon)=1")
    assert flat[4]["position_anchor"] == "TOPRIGHT"
    # On OPPO's KWGT preview the old offsets pushed date/alarm to the
    # very bottom. Keep the secondary rows inside a conservative height budget.
    assert flat[2]["position_offset_y"] <= 105
    assert flat[3]["position_offset_y"] <= 140
    assert flat[6]["position_offset_y"] <= 85
    assert flat[7]["position_offset_y"] <= 125
    for field in ("temp", "icon", "feels", "condition"):
        assert "br(breezy, " + field + ")" in json.dumps(check, ensure_ascii=False)
print("ALIGNED_FLAT_KWGT_VERIFIED", [(x["internal_type"], x.get("internal_title","")) for x in flat])
print("FILE", out, "SIZE", os.stat(out).st_size)
