#!/usr/bin/env python3
"""Breezy Minimal v72: "feels like" icon, tomorrow's mm next to the umbrella, smaller rows.

Usage: build_v72_preset.py BASE_v71.kwgt OUT.kwgt

On top of v71 (build_v71_preset.py):
- middle row (date | wind, rain now, feels like) in size 20; "like" replaced by the MDI
  icon account-outline;
- bottom row in size 16; the umbrella block gets a drop + tomorrow's precipitation in mm
  (bridge 1.7 tomorrow_precip_mm), only when there is any;
- the "maximal" switch covers the new parts.
Sizes from width estimates of the longest values (see the "maximal" switch).
"""
import json
import sys
import time
import uuid
import zipfile

TITLE = "Breezy Minimal v7.2 • Manrope"
MDI = "iconify://mdi?name=Material%20Design%20Icons"
MIDDLE_SIZE = 20.0
BOTTOM_SIZE = 16.0
ASCENT = 1.066

FEELS = '$if(gv(maximal) = 1, "-42°", br(breezy, like))$'
TOMORROW_MM = '$if(gv(maximal) = 1, "12,5", br(breezy, tomorrow_precip_mm))$'
TOMORROW_MM_VISIBLE = ('$if(gv(maximal) = 1 | br(breezy, tomorrow_precip_mm) != "", '
                       'ALWAYS, REMOVE)$')


def walk(items):
    for item in items:
        yield item
        yield from walk(item.get("viewgroup_items", []))


def resize(group, size):
    """Text to `size`, icons to size - 2 (as in v71)."""
    for item in walk(group.get("viewgroup_items", [group])):
        if item["internal_type"] == "TextModule":
            item["text_size"] = size
        elif item["internal_type"] == "FontIconModule":
            item["icon_size"] = size - 2


def keep_baseline(item, old_size, new_size):
    item["position_offset_y"] = item.get("position_offset_y", 0.0) + round(
        (old_size - new_size) * ASCENT)


def find(items, title):
    return next(item for item in walk(items) if item.get("internal_title") == title)


def main(base, target):
    source = zipfile.ZipFile(base)
    preset = json.loads(source.read("preset.json").decode("utf-8"))
    preset["preset_info"].update(title=TITLE, id=str(uuid.uuid4()),
                                 ts=int(time.time() * 1000))
    items = preset["preset_root"]["viewgroup_items"]

    # Middle row: date + wind stack, "like" -> account-outline icon.
    date, wind_row = find(items, "Date"), find(items, "Wind + rain now + like")
    like = find(items, "Like")
    drop = find(items, "Rain drop")
    feels_icon = dict(drop, internal_title="Feels like icon", icon_icon="account-outline")
    feels = {"internal_type": "StackLayerModule", "internal_title": "Feels like",
             "config_stacking": "HORIZONTAL_CENTER", "config_margin": 1.0,
             "viewgroup_items": [feels_icon, dict(like, internal_title="Feels like value",
                                                  text_expression=FEELS)]}
    wind_row["viewgroup_items"][wind_row["viewgroup_items"].index(like)] = feels
    wind_row["internal_title"] = "Wind + rain now + feels like"
    for item in (date, wind_row):
        keep_baseline(item, item.get("text_size", 23.0) if item is date else 23.0, MIDDLE_SIZE)
        resize(item, MIDDLE_SIZE)

    # Bottom row: tomorrow's mm after the umbrella's percent.
    umbrella = find(items, "Umbrella (Globals: umbrella_test, umbrella_min)")
    percent = find(items, "Umbrella percent")
    mm = {"internal_type": "StackLayerModule",
          "internal_title": "Tomorrow mm (only with precipitation)",
          "config_stacking": "HORIZONTAL_CENTER", "config_margin": 1.0,
          "internal_toggles": {"config_visible": 10},
          "internal_formulas": {"config_visible": TOMORROW_MM_VISIBLE},
          "viewgroup_items": [dict(drop, internal_title="Tomorrow drop"),
                              dict(percent, internal_title="Tomorrow mm",
                                   text_expression=TOMORROW_MM)]}
    umbrella["viewgroup_items"].append(mm)
    umbrella["config_margin"] = 3.0
    for title in ("Next alarm + next sunset/sunrise", "Today + tomorrow + umbrella"):
        row = find(items, title)
        keep_baseline(row, 19.0, BOTTOM_SIZE)
        resize(row, BOTTOM_SIZE)

    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as out:
        for entry in source.infolist():
            data = source.read(entry.filename)
            if entry.filename == "preset.json":
                data = json.dumps(preset, ensure_ascii=False, indent=2).encode("utf-8")
            out.writestr(entry, data)


if __name__ == "__main__":
    main(*sys.argv[1:3])
