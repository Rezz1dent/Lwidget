#!/usr/bin/env python3
"""Build a responsive two-column KWGT preset from an existing valid .kwgt."""
import io
import json
import os
import urllib.request
import zipfile

SOURCE_URL = (
    "https://raw.githubusercontent.com/Rezz1dent/Lwidget/"
    "assets/kwgt-accuweather/kwgt/Minimal_Clock_AccuWeather_v2.kwgt"
)
with urllib.request.urlopen(SOURCE_URL, timeout=50) as response:
    source_data = response.read()
source = zipfile.ZipFile(io.BytesIO(source_data))
preset = json.loads(source.read("preset.json").decode("utf-8"))
old = preset["preset_root"]["viewgroup_items"]
assert len(old) >= 8

# Preserve already proven KWGT text modules, avoiding speculative module schemas.
clock, date, alarm = [dict(old[index]) for index in (1, 2, 3)]
temp, icon, feels, condition = [dict(old[index]) for index in (4, 5, 6, 7)]

def position(element, anchor, x, y):
    element.update(
        position_anchor=anchor, position_offset_x=float(x),
        position_offset_y=float(y)
    )
    return element

def anchor_shape(width, height):
    return dict(
        internal_type="ShapeModule", internal_title="Invisible layout guide",
        shape_type="RECT", shape_width=float(width), shape_height=float(height),
        shape_corners=0, paint_color="#00000000", position_anchor="CENTER"
    )

# Groups are anchored to opposing edges of the ACTUAL KWGT widget bounds,
# not to x coordinates of a fixed 4-column widget.
left = dict(
    internal_type="OverlapGroupModule", internal_title="LEFT • Clock / Date / Alarm",
    position_anchor="TOPLEFT", position_offset_x=24.0,
    position_offset_y=5.0, viewgroup_items=[
        anchor_shape(270, 218),
        position(clock, "TOPLEFT", 3, 15),
        position(date, "TOPLEFT", 5, 132),
        position(alarm, "TOPLEFT", 5, 177)
    ]
)
right = dict(
    internal_type="OverlapGroupModule", internal_title="RIGHT • Breezy Weather",
    position_anchor="TOPRIGHT", position_offset_x=22.0,
    position_offset_y=5.0, viewgroup_items=[
        anchor_shape(250, 218),
        position(temp, "TOPRIGHT", 55, 22),
        position(icon, "TOPRIGHT", 1, 20),
        position(feels, "TOPRIGHT", 0, 105),
        position(condition, "TOPRIGHT", 0, 150)
    ]
)

# Do not use a fixed-width centered background shape: its dimensions don't
# follow 5-column launcher resize. KWGT's root background fills the viewport.
root = preset["preset_root"]
root["background_type"] = "SOLID"
root["background_color"] = "#E01C2432"
root["viewgroup_items"] = [left, right]

temp["text_expression"] = "$br(breezy, temp)$"
temp["internal_title"] = "Current temperature • Breezy"
temp["text_size"] = 41.0
icon["text_expression"] = "$br(breezy, icon)$"
icon["internal_title"] = "Current weather symbol • Breezy"
icon["text_size"] = 41.0
feels["text_expression"] = "$br(breezy, feels)$"
feels["internal_title"] = "Feels like • Breezy"
feels["text_size"] = 20.0
feels.pop("text_size_type", None)
feels.pop("text_width", None)
condition["text_expression"] = "$tc(ell, br(breezy, condition), 22)$"
condition["internal_title"] = "Description • Breezy (truncated)"
condition["text_size"] = 20.0
condition.pop("text_size_type", None)
condition.pop("text_width", None)
date["text_expression"] = "$df(EEE)$, $df(dd MMM)$"

preset["preset_info"].update(
    title="Minimal Clock • Breezy • Responsive 5-column",
    description="Independent left/right anchor groups. Requires Breezy-to-KWGT bridge.",
    width=720, height=235, features="LOCATION"
)
out = "dist/Minimal_Clock_Breezy_Responsive.kwgt"
os.makedirs("dist", exist_ok=True)
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as result:
    for name in source.namelist():
        if name == "preset.json":
            result.writestr(name, json.dumps(preset, ensure_ascii=False, separators=(",", ":")))
        elif name != "preset_thumb.png":
            result.writestr(name, source.read(name))
with zipfile.ZipFile(out) as result:
    assert result.testzip() is None
    obj = json.loads(result.read("preset.json"))
    assert len(obj["preset_root"]["viewgroup_items"]) == 2
    assert all(x["internal_type"] == "OverlapGroupModule"
               for x in obj["preset_root"]["viewgroup_items"])
    fields = json.dumps(obj, ensure_ascii=False)
    for key in ("temp", "feels", "condition", "icon"):
        assert "br(breezy, " + key + ")" in fields
print("Responsive left/right groups and weather expressions verified")
print("Created", out, os.path.getsize(out), "bytes")
