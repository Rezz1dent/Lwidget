#!/usr/bin/env python3
"""Breezy Minimal v76: drop / snowflake / snowflake with a drop for rain, snow and sleet.

Usage: build_v76_preset.py BASE_v75.kwgt OUT.kwgt

The drop of "rain now" and the one next to tomorrow's mm take their icon from bridge 1.8
(precip_now_icon, tomorrow_precip_icon: water-outline / snowflake / snowflake-melt); the drop
stays with an older bridge. New global precip_test (number): 0 = real data, 1 = rain,
2 = snow, 3 = mix; 1-3 also show both blocks (with a sample value when it is dry) and the
umbrella, and the automatic row sizes count them.
"""
import json
import sys
import time
import uuid
import zipfile

TITLE = "Breezy Minimal v7.6 • Manrope"
TEST = "gv(precip_test)"
SAMPLE = "0,8"


def icon(variable):
    return ('$if({t} = 1, "water-outline", {t} = 2, "snowflake", {t} = 3, "snowflake-melt", '
            'br(breezy, {v}) != "", br(breezy, {v}), "water-outline")$').format(t=TEST, v=variable)


ICONS = {"Rain drop": icon("precip_now_icon"), "Tomorrow drop": icon("tomorrow_precip_icon")}
TEXTS = {
    "Rain mm (precip_now)": ('$if(gv(maximal) = 1, "12,5", {t} > 0 & br(breezy, precip_now) = "", '
                             '"{s}", br(breezy, precip_now))$').format(t=TEST, s=SAMPLE),
    "Tomorrow mm": ('$if(gv(maximal) = 1, "12,5", {t} > 0 & br(breezy, tomorrow_precip_mm) = "", '
                    '"{s}", br(breezy, tomorrow_precip_mm))$').format(t=TEST, s=SAMPLE),
}
# Visibility and the row-size estimates (build_v75_preset.py) treat the test like real data.
REPLACE = [
    ('gv(maximal) = 1 | br(breezy, precip_now) != ""',
     'gv(maximal) = 1 | {t} > 0 | br(breezy, precip_now) != ""'),
    ('if(br(breezy, precip_now) != "", 1, 0)',
     'if({t} > 0 | br(breezy, precip_now) != "", 1, 0)'),
    ('tc(len, br(breezy, precip_now))',
     'tc(len, if({t} > 0 & br(breezy, precip_now) = "", "{s}", br(breezy, precip_now)))'),
    ('gv(umbrella_test) = 1 | gv(maximal) = 1 |',
     'gv(umbrella_test) = 1 | gv(maximal) = 1 | {t} > 0 |'),
    ('gv(maximal) = 1 | br(breezy, tomorrow_precip_mm) != ""',
     'gv(maximal) = 1 | {t} > 0 | br(breezy, tomorrow_precip_mm) != ""'),
    ('= 1 & br(breezy, tomorrow_precip_mm) != ""',
     '= 1 & ({t} > 0 | br(breezy, tomorrow_precip_mm) != "")'),
    ('tc(len, br(breezy, tomorrow_precip_mm))',
     'tc(len, if({t} > 0 & br(breezy, tomorrow_precip_mm) = "", "{s}", '
     'br(breezy, tomorrow_precip_mm)))'),
]


def walk(items):
    for item in items:
        yield item
        yield from walk(item.get("viewgroup_items", []))


def main(base, target):
    source = zipfile.ZipFile(base)
    preset = json.loads(source.read("preset.json").decode("utf-8"))
    preset["preset_info"].update(title=TITLE, id=str(uuid.uuid4()), ts=int(time.time() * 1000))
    root = preset["preset_root"]

    count = {old: 0 for old, _ in REPLACE}
    for item in walk(root["viewgroup_items"]):
        formulas = item.get("internal_formulas", {})
        for key, value in formulas.items():
            for old, new in REPLACE:
                count[old] += value.count(old)
                value = value.replace(old, new.format(t=TEST, s=SAMPLE))
            formulas[key] = value
        title = item.get("internal_title")
        if title in ICONS:
            item["internal_toggles"]["icon_icon"] = 10
            item["internal_formulas"]["icon_icon"] = ICONS.pop(title)
        if title in TEXTS:
            item["text_expression"] = TEXTS.pop(title)
    assert not ICONS and not TEXTS and all(count.values()), (ICONS, TEXTS, count)

    globals_list = root["globals_list"]
    globals_list["precip_test"] = {
        "index": len(globals_list) + 1, "type": "NUMBER",
        "title": "Precipitation icon test: 0 data, 1 rain, 2 snow, 3 mix", "value": 0.0}

    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as out:
        for entry in source.infolist():
            data = source.read(entry.filename)
            if entry.filename == "preset.json":
                data = json.dumps(preset, ensure_ascii=False, indent=2).encode("utf-8")
            out.writestr(entry, data)


if __name__ == "__main__":
    main(*sys.argv[1:3])
