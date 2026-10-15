#!/usr/bin/env python3
"""Breezy Minimal v51: English weekday top-right, its lower half cut off.

Usage: build_weekday_preset.py BASE_v50.kwgt FONTS_DIR OUT.kwgt

Starts from the hand-tuned v50 (presets/Breezy_Minimal_v50__Manrope__control.kwgt):
- the weekday (MONDAY…SUNDAY) right of the clock, all days the same width: KWGT has no
  letter spacing, so the letters are separated by spacer glyphs of exact width from
  Manrope-Light-Spaced.ttf (make_manrope_fonts.py);
- a CLEAR rectangle erases the lower half of the letters;
- below it a smaller current temperature with the icon, and today's range under them;
- left column: date, then the next alarm (today's range moved to the right).

Coordinates are root units: v50's root is ~497 x 190 (1458 x 533 px at scale 160),
content between x 20 and 477.
"""
import copy
import json
import os
import sys
import time
import uuid
import zipfile

from fontTools.ttLib import TTFont

TITLE = "Breezy Minimal v53 • Weekday"
FONT = "kfile://org.kustom.provider/fonts/%s.ttf"
FONTS = ["Manrope-ExtraBold-Tnum", "Manrope-ExtraLight-Tnum", "Manrope-SemiBold",
         "Manrope-Regular", "Manrope-Light-Spaced"]
WORD_FONT = "Manrope-Light-Spaced"
SPACER_FIRST, SPACER_STEP = 0xE100, 4

WHITE = "#FFF9FBFF"
SECONDARY = "#B8FFFFFF"
DAYS = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]

ASCENT, CAP = 1.066, 0.72   # Manrope, in em
EDGE = 20.0                 # right margin, as the other right-column elements
CLOCK_TOP = 14.0            # cap top of the clock digits (hours: y -17, size 95)
WORD_WIDTH = 200.0          # from the clock's right end (~252) + gap to the right edge
WORD_SIZE = 34.0            # WEDNESDAY (5.81 em in Manrope Light) fits WORD_WIDTH
# Word centered between the clock's right end (x 252 from the left) and the right edge:
# with the TOP anchor the offset from the root's center is (252 - EDGE) / 2 whatever
# the root width is.
CLOCK_RIGHT = 252.0
WORD_CENTER_X = (CLOCK_RIGHT - EDGE) / 2
CLOCK_BASELINE = 84.0       # bottom of the clock digits
TEMP_SIZE = 46.0
ICON_SIZE = 36.0
RANGE_SIZE = 16.0
# Under the cut: temperature + icon and today's range, with equal gaps between the cut,
# the two rows and the clock's baseline (see main()).


def shadow(blur):
    return {"fx_shadow": "OUTER", "fx_shadow_blur": blur, "fx_shadow_direction": 15,
            "fx_shadow_distance": 1, "fx_shadow_color": "#68000000"}


def spaced_words(font_path):
    """Each day with spacer glyphs between letters so all are WORD_WIDTH wide."""
    font = TTFont(font_path)
    cmap, hmtx, upm = font.getBestCmap(), font["hmtx"], font["head"].unitsPerEm
    target = WORD_WIDTH / WORD_SIZE * upm
    words = {}
    for day in DAYS:
        letters = sum(hmtx[cmap[ord(c)]][0] for c in day)
        step = round((target - letters) / (len(day) - 1) / SPACER_STEP)
        assert step >= 0, day
        spacer = chr(SPACER_FIRST + step) if step else ""
        words[day] = spacer.join(day)
    return words


def text(title, expression, size, font, color, anchor, x, y, blur=2, **extra):
    item = {"internal_type": "TextModule", "internal_title": title,
            "text_expression": expression, "text_size": size, "text_family": FONT % font,
            "paint_color": color, "position_anchor": anchor,
            "position_offset_x": x, "position_offset_y": round(y, 1)}
    item.update(shadow(blur))
    item.update(extra)
    return item


def top_for_cap(cap_top, size):
    """Module y so that the capital letters start at cap_top."""
    return cap_top - (ASCENT - CAP) * size


def main(base, fonts_dir, target):
    source = zipfile.ZipFile(base)
    preset = json.loads(source.read("preset.json").decode("utf-8"))
    info = preset["preset_info"]
    info.update(title=TITLE, id=str(uuid.uuid4()), ts=int(time.time() * 1000))
    info["description"] = (
        "Manrope clock with the English weekday top-right, its lower half cut off; current "
        "temperature, Breezy icon and today's range under it. Reboot the phone once after the "
        "first import so the home screen loads the fonts. Data from Breezy Bridge 1.4+.")

    items = preset["preset_root"]["viewgroup_items"]
    by_title = {item.get("internal_title"): item for item in items}
    words = spaced_words(os.path.join(fonts_dir, WORD_FONT + ".ttf"))

    # Weekday, cap top level with the clock; erase the lower half of the letters.
    word_cap = WORD_SIZE * CAP
    cut_y = CLOCK_TOP + word_cap / 2
    weekday = text(
        "Weekday • English, same width every day",
        "$if(%s)$" % ", ".join('df(f)=%d, "%s"' % (i + 1, words[d]) for i, d in enumerate(DAYS)),
        WORD_SIZE, WORD_FONT, SECONDARY, "TOP", WORD_CENTER_X, top_for_cap(CLOCK_TOP, WORD_SIZE),
        text_align="CENTER")
    cut = {"internal_type": "ShapeModule", "internal_title": "Weekday • cut (erases lower half)",
           "shape_type": "RECT", "shape_width": WORD_WIDTH + 20, "shape_height": word_cap,
           "paint_mode": "CLEAR", "position_anchor": "TOP",
           "position_offset_x": WORD_CENTER_X, "position_offset_y": round(cut_y, 1)}

    # Current temperature + icon below the cut, today's range under them.
    gap = (CLOCK_BASELINE - cut_y - TEMP_SIZE * CAP - RANGE_SIZE * CAP) / 3
    temp_cap = cut_y + gap
    temp = by_title["Row 1 • Breezy temperature"]
    temp.update(text_size=TEMP_SIZE, position_offset_x=EDGE + ICON_SIZE + 6,
                position_offset_y=round(top_for_cap(temp_cap, TEMP_SIZE), 1))
    temp.update(shadow(4))
    icon = by_title["Row 1 • Current weather icon (Breezy, Iconify mdi)"]
    icon.update(icon_size=ICON_SIZE, position_offset_x=EDGE,
                position_offset_y=round(temp_cap + TEMP_SIZE * CAP / 2 - ICON_SIZE / 2, 1))
    range_cap = temp_cap + TEMP_SIZE * CAP + gap
    today = text("Today • range under the temperature", "$br(breezy, today_range)$",
                 RANGE_SIZE, "Manrope-Regular", SECONDARY, "TOPRIGHT", EDGE,
                 top_for_cap(range_cap, RANGE_SIZE))

    # Left column: date, then the next alarm in the row today's range used.
    date_row = by_title["Date + next alarm"]
    old_today = by_title["Today • Breezy high/low"]
    alarm = copy.deepcopy(date_row)
    date_row.update(internal_title="Date", text_expression='$df("d MMMM")$')
    alarm.update(internal_title="Next alarm",
                 position_offset_y=old_today["position_offset_y"],
                 text_expression='$if(si(alarmon)=1, "◷ " + df("HH:mm", si(alarmd)) + '
                                 '" (" + df("EEE", si(alarmd)) + ")", "◷ —")$')

    result = []
    for item in items:
        if item is old_today:
            continue
        result.append(item)
        if item.get("internal_title") == "Clock • minutes":
            # Drawn before everything on the right, so the cut erases only the word.
            result += [weekday, cut]
        if item is date_row:
            result.append(alarm)
        if item is icon:
            result.append(today)
    preset["preset_root"]["viewgroup_items"] = result

    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as out:
        for entry in source.infolist():
            if entry.filename.startswith("fonts/"):
                continue
            data = source.read(entry.filename)
            if entry.filename == "preset.json":
                data = json.dumps(preset, ensure_ascii=False, indent=2).encode("utf-8")
            out.writestr(entry, data)
        template = source.getinfo("preset.json")
        for name in FONTS:
            entry = copy.copy(template)
            entry.filename = "fonts/%s.ttf" % name
            with open(os.path.join(fonts_dir, name + ".ttf"), "rb") as f:
                out.writestr(entry, f.read())


if __name__ == "__main__":
    main(*sys.argv[1:4])
