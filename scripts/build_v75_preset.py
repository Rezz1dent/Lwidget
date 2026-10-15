#!/usr/bin/env python3
"""Breezy Minimal v75: middle and bottom rows pick their font size automatically.

Usage: build_v75_preset.py BASE_v74.kwgt OUT.kwgt

KWGT cannot measure rendered text, so each row estimates its width from the number of
characters and icons in the current values (Manrope Regular: ~0.52 em per character,
icons + stack overhead per icon; calibrated against the font so the estimate is never
smaller than the real width) and uses the large size when the row fits, else the small
one. The "maximal" switch always shows the small size (its values are the longest).
Baselines stay put: the y offset moves with the size.
"""
import json
import sys
import time
import uuid
import zipfile

TITLE = "Breezy Minimal v7.5 • Manrope"
FIT = 445                          # content width 457 minus a 12 gap between the halves
MIDDLE = {"big": 22, "small": 20}  # date | wind, rain now, feels like
BOTTOM = {"big": 20, "small": 18}  # alarm, sun | today, tomorrow, umbrella
ASCENT = 1.066

PRECIP = 'tc(reg, br(breezy, tomorrow_precip), "[^0-9]", "")'
# No lv()/#name here: the first build used variables named mi/bi (KWGT functions) and the
# rows vanished. Plain sub-formulas only, so the result is a bare number.
RAIN_NOW = 'if(br(breezy, precip_now) != "", 1, 0)'
MIDDLE_CHARS = ('(tc(len, df("EEEE, d MMM")) + tc(len, br(breezy, wind_ms)) + 2 '
                '+ tc(len, br(breezy, like)) + tc(len, br(breezy, precip_now)))')
MIDDLE_ICONS = '(1 + %s)' % RAIN_NOW
MIDDLE_WIDE = '{big} * (0.52 * {c} + 1.1 * {i}) + 8 + 8 * {i} > {fit}'.format(
    big=MIDDLE["big"], c=MIDDLE_CHARS, i=MIDDLE_ICONS, fit=FIT)
UMBRELLA = ('if(gv(umbrella_test) = 1 | gv(maximal) = 1 | ({p} != "" & {p} >= '
            'if(gv(umbrella_min) > 0, gv(umbrella_min), 70)), 1, 0)').format(p=PRECIP)
TOMORROW_MM = 'if({u} = 1 & br(breezy, tomorrow_precip_mm) != "", 1, 0)'.format(u=UMBRELLA)
BOTTOM_CHARS = ('(if(si(alarmon) = 1, 10, 1) + 5 + tc(len, br(breezy, today_range)) '
                '+ tc(len, tc(reg, br(breezy, tomorrow_compact), "Tomorrow: ", "")) '
                '+ {u} * (tc(len, {p}) + 1) '
                '+ {m} * tc(len, br(breezy, tomorrow_precip_mm)))').format(
                    u=UMBRELLA, p=PRECIP, m=TOMORROW_MM)
BOTTOM_ICONS = '(3 + {u} + {m})'.format(u=UMBRELLA, m=TOMORROW_MM)
BOTTOM_WIDE = '{big} * (0.55 * {c} + 1.3 * {i}) + 16 + 8 * {i} > {fit}'.format(
    big=BOTTOM["big"], c=BOTTOM_CHARS, i=BOTTOM_ICONS, fit=FIT)
MIDDLE_SMALL = 'if(gv(maximal) = 1 | ' + MIDDLE_WIDE + ', %s, %s)'
BOTTOM_SMALL = 'if(gv(maximal) = 1 | ' + BOTTOM_WIDE + ', %s, %s)'


def walk(items):
    for item in items:
        yield item
        yield from walk(item.get("viewgroup_items", []))


def find(items, title):
    return next(i for i in walk(items) if i.get("internal_title") == title)


def formula(item, key, expression):
    item.setdefault("internal_toggles", {})[key] = 10
    item.setdefault("internal_formulas", {})[key] = "$" + expression + "$"


def auto_size(roots, choose, sizes):
    """Size formula on every text and icon; y formula on the roots keeps the baseline.

    `choose` is "if(row is too wide, %s, %s)"; it gets the (small, big) values.
    """
    for root in roots:
        current = next(i for i in walk([root]) if i["internal_type"] == "TextModule")["text_size"]
        y_small = int(root.get("position_offset_y", 0.0)) + round((current - sizes["small"]) * ASCENT)
        y_big = y_small - round((sizes["big"] - sizes["small"]) * ASCENT)
        formula(root, "position_offset_y", choose % (y_small, y_big))
        for item in walk([root]):
            if item["internal_type"] == "TextModule":
                formula(item, "text_size", choose % (sizes["small"], sizes["big"]))
            elif item["internal_type"] == "FontIconModule":
                formula(item, "icon_size", choose % (sizes["small"], sizes["big"]))


def main(base, target):
    source = zipfile.ZipFile(base)
    preset = json.loads(source.read("preset.json").decode("utf-8"))
    preset["preset_info"].update(title=TITLE, id=str(uuid.uuid4()), ts=int(time.time() * 1000))
    items = preset["preset_root"]["viewgroup_items"]

    auto_size([find(items, "Date"), find(items, "Wind + rain now + feels like")],
              MIDDLE_SMALL, MIDDLE)
    auto_size([find(items, "Next alarm + next sunset/sunrise"),
               find(items, "Today + tomorrow + umbrella")],
              BOTTOM_SMALL, BOTTOM)

    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as out:
        for entry in source.infolist():
            data = source.read(entry.filename)
            if entry.filename == "preset.json":
                data = json.dumps(preset, ensure_ascii=False, indent=2).encode("utf-8")
            out.writestr(entry, data)


if __name__ == "__main__":
    main(*sys.argv[1:3])
