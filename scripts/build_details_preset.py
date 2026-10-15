#!/usr/bin/env python3
"""Breezy Minimal v52: full Russian date, tomorrow icon, next sunrise/sunset.

Usage: build_details_preset.py BASE_v51.kwgt OUT.kwgt

On top of v51 (build_weekday_preset.py):
- left middle row: "Четверг, 15 октября" (smaller font for long names, so it never
  runs into the wind row);
- "Tomorrow:" replaced by the MDI icon calendar-arrow-right (icon + range in a stack
  group, which keeps the umbrella shift formula);
- next to the alarm: the next sunset by day / sunrise by night, from KWGT's own
  astronomy (ai(), KWGT location, works offline) with weather-sunset-down/up icons.
"""
import json
import sys
import time
import uuid
import zipfile

TITLE = "Breezy Minimal v53 • Weekday"
MDI = "iconify://mdi?name=Material%20Design%20Icons"
ROW_SIZE = 23.0
ICON_SIZE = 22.0

DATE = '$tc(cap, df("EEEE")) + df(", d MMMM")$'
# "Воскресенье, 15 сентября" + the longest wind row would touch: shrink long dates.
DATE_SIZE = '$if(tc(len, df("EEEE, d MMMM")) > 20, 20, 23)$'
NEXT_SUN = "if(ai(isday) = 1, ai(sunset), df(H) >= 12, ai(sunrise, a1d), ai(sunrise))"


def stack(title, anchor, base, children):
    item = {"internal_type": "StackLayerModule", "internal_title": title,
            "config_stacking": "HORIZONTAL_CENTER", "config_margin": 4.0,
            "position_anchor": anchor,
            "position_offset_x": base.get("position_offset_x", 20.0),
            "position_offset_y": base.get("position_offset_y", 145.0),
            "viewgroup_items": children}
    for key in ("internal_toggles", "internal_formulas", "internal_events"):
        if key in base:
            item[key] = {k: v for k, v in base[key].items() if k == "position_offset_x"} \
                if key != "internal_events" else base[key]
    return item


def child_text(base, title, expression):
    item = {k: v for k, v in base.items()
            if k.startswith(("text_", "paint_", "fx_"))}
    item.update(internal_type="TextModule", internal_title=title, text_expression=expression)
    return item


def child_icon(base, title, icon, formula=None):
    item = {k: v for k, v in base.items() if k.startswith(("paint_", "fx_"))}
    item.update(internal_type="FontIconModule", internal_title=title, icon_set=MDI,
                icon_icon=icon, icon_size=ICON_SIZE)
    if formula:
        item.update(internal_toggles={"icon_icon": 10}, internal_formulas={"icon_icon": formula})
    return item


def main(base, target):
    source = zipfile.ZipFile(base)
    preset = json.loads(source.read("preset.json").decode("utf-8"))
    info = preset["preset_info"]
    info.update(title=TITLE, id=str(uuid.uuid4()), ts=int(time.time() * 1000))
    info["description"] += (" Full Russian date, tomorrow as a calendar icon, next "
                            "sunrise/sunset from KWGT's location.")

    result = []
    for item in preset["preset_root"]["viewgroup_items"]:
        title = item.get("internal_title")
        if title == "Date":
            item["text_expression"] = DATE
            item.setdefault("internal_toggles", {})["text_size"] = 10
            item.setdefault("internal_formulas", {})["text_size"] = DATE_SIZE
        elif title == "Row 3 • Tomorrow maximum/minimum":
            item = stack("Tomorrow • calendar icon + range", "TOPRIGHT", item, [
                child_icon(item, "Tomorrow icon", "calendar-arrow-right"),
                child_text(item, "Tomorrow range",
                           '$tc(reg, br(breezy, tomorrow_compact), "Tomorrow: ", "")$'),
            ])
        elif title == "Next alarm":
            alarm = item["text_expression"]
            item = stack("Next alarm + next sunrise/sunset", "TOPLEFT", item, [
                child_text(item, "Next alarm", alarm[:-1] + ' + "  "$'),
                child_icon(item, "Sun icon", "weather-sunset-down",
                           '$if(ai(isday) = 1, "weather-sunset-down", "weather-sunset-up")$'),
                child_text(item, "Sun time", "$df(HH:mm, %s)$" % NEXT_SUN),
            ])
        result.append(item)
    preset["preset_root"]["viewgroup_items"] = result

    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as out:
        for entry in source.infolist():
            data = source.read(entry.filename)
            if entry.filename == "preset.json":
                data = json.dumps(preset, ensure_ascii=False, indent=2).encode("utf-8")
            out.writestr(entry, data)


if __name__ == "__main__":
    main(*sys.argv[1:3])
