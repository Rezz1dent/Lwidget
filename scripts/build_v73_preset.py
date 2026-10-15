#!/usr/bin/env python3
"""Breezy Minimal v74: MDI alarm icon instead of the "◷" character.

Usage: build_v73_preset.py BASE.kwgt OUT.kwgt   (v74 = the owner's tuned v73 + this)

The next-alarm text in the bottom row becomes a small stack: the MDI icon "alarm"
("alarm-off" when no alarm is set) + the time, in the same style and size as the
sunset/sunrise icon next to it.
"""
import json
import sys
import time
import uuid
import zipfile

TITLE = "Breezy Minimal v7.4 • Manrope"
ALARM_ICON = '$if(gv(maximal) = 1 | si(alarmon) = 1, "alarm", "alarm-off")$'
ALARM_TIME = ('$if(gv(maximal) = 1, "20:08 (пн)", if(si(alarmon) = 1, df("HH:mm", si(alarmd))'
              ' + " (" + df("EEE", si(alarmd)) + ")", "—"))$')


def walk(items):
    for item in items:
        yield item
        yield from walk(item.get("viewgroup_items", []))


def main(base, target):
    source = zipfile.ZipFile(base)
    preset = json.loads(source.read("preset.json").decode("utf-8"))
    preset["preset_info"].update(title=TITLE, id=str(uuid.uuid4()), ts=int(time.time() * 1000))
    items = preset["preset_root"]["viewgroup_items"]

    row = next(i for i in walk(items)
               if i.get("internal_title") == "Next alarm + next sunset/sunrise")
    alarm = next(i for i in row["viewgroup_items"] if i.get("internal_title") == "Next alarm")
    sun_icon = next(i for i in walk(row["viewgroup_items"])
                    if i.get("internal_title") == "Sun icon")
    icon = dict(sun_icon, internal_title="Alarm icon", icon_icon="alarm",
                internal_toggles={"icon_icon": 10}, internal_formulas={"icon_icon": ALARM_ICON})
    alarm_stack = {"internal_type": "StackLayerModule", "internal_title": "Alarm",
                   "config_stacking": "HORIZONTAL_CENTER", "config_margin": 3.0,
                   "viewgroup_items": [icon, dict(alarm, internal_title="Alarm time",
                                                  text_expression=ALARM_TIME)]}
    row["viewgroup_items"][row["viewgroup_items"].index(alarm)] = alarm_stack

    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as out:
        for entry in source.infolist():
            data = source.read(entry.filename)
            if entry.filename == "preset.json":
                data = json.dumps(preset, ensure_ascii=False, indent=2).encode("utf-8")
            out.writestr(entry, data)


if __name__ == "__main__":
    main(*sys.argv[1:3])
