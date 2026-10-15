#!/usr/bin/env python3
"""Breezy Minimal v54: v50 layout + full date, tomorrow icon, sun times, umbrella in stacks.

Usage: build_v54_preset.py BASE_v50.kwgt FONTS_DIR OUT.kwgt

Starts from the hand-tuned v50 (presets/Breezy_Minimal_v50__Manrope__control.kwgt):
- temperature and icon as in v50;
- left middle row: "Четверг, 15 октября" (smaller for long names);
- bottom left: next alarm, then the next sunset/sunrise (KWGT ai(), its own location);
- bottom right: today's range, then calendar icon + tomorrow's range; with rain the
  umbrella replaces the calendar icon and the percent follows the range;
- weather icon: sun/moon variant from KWGT's ai(isday), not the bridge's last update.

Rows are stack groups: KWGT lays the parts out by their real width, so the gaps stay
even without width estimates. The umbrella group is hidden with config_visible = REMOVE,
which also removes its place in the row. The umbrella settings stay in the root globals
(umbrella_test, umbrella_min).
"""
import copy
import json
import os
import sys
import time
import uuid
import zipfile

TITLE = "Breezy Minimal v58 • Manrope"
MDI = "iconify://mdi?name=Material%20Design%20Icons"
FONT = "kfile://org.kustom.provider/fonts/%s.ttf"
FONTS = ["Manrope-ExtraBold-Tnum", "Manrope-ExtraLight-Tnum", "Manrope-SemiBold",
         "Manrope-Regular"]
ROW_ICON = 22.0

DATE = '$tc(cap, df("EEEE")) + df(", d MMMM")$'
DATE_SIZE = '$if(gv(maximal) = 1 | tc(len, df("EEEE, d MMMM")) > 20, 20, 23)$'
ALARM = ('$if(si(alarmon)=1, "◷ " + df("HH:mm", si(alarmd)) + " (" + df("EEE", si(alarmd))'
         ' + ")", "◷ —")$')
SUN_ICON = '$if(ai(isday) = 1, "weather-sunset-down", "weather-sunset-up")$'
SUN_TIME = ("$df(HH:mm, if(ai(isday) = 1, ai(sunset), df(H) >= 12, "
            "ai(sunrise, a1d), ai(sunrise)))$")
TOMORROW = '$tc(reg, br(breezy, tomorrow_compact), "Tomorrow: ", "")$'
# Tomorrow's precipitation as digits in the local variable p ("" when Breezy has none).
PRECIP = 'lv(p, tc(reg, br(breezy, tomorrow_precip), "[^0-9]", ""))'
RAIN = ('gv(umbrella_test) = 1 | gv(maximal) = 1 | (#p != "" & #p >= '
        'if(gv(umbrella_min) > 0, gv(umbrella_min), 70))')
UMBRELLA_VISIBLE = '$%s + if(%s, ALWAYS, REMOVE)$' % (PRECIP, RAIN)
# With rain the umbrella takes the calendar icon's place in front of tomorrow's range.
TOMORROW_ICON = '$%s + if(%s, "umbrella-outline", "calendar-arrow-right")$' % (PRECIP, RAIN)
# Day/night from KWGT's own astronomy (location, real time): the bridge's choice can be
# hours old when Breezy or the bridge's alarm did not run. Swap sun/moon variants.
WEATHER_ICON = (
    '$lv(i, br(breezy, icon_mdi)) + if(ai(isday) = 1, '
    'tc(reg, tc(reg, #i, "^weather-night-partly-cloudy$", "weather-partly-cloudy"), '
    '"^weather-night$", "white-balance-sunny"), '
    'tc(reg, tc(reg, #i, "^weather-partly-cloudy$", "weather-night-partly-cloudy"), '
    '"^white-balance-sunny$", "weather-night"))$')
GROUP_MARGIN = 8.0
UMBRELLA_PERCENT = '$%s + if(#p = "", 0, #p) + "%%"$' % PRECIP

# Global switch "maximal": every row shows its longest realistic value, to check that
# nothing overlaps (winter temperatures, longest weekday and month, umbrella at 100%).
# The bridge sends temperatures with "-" (hyphen), drawn as a narrow minus by our fonts.
MAXIMAL = {"index": 3, "type": "SWITCH", "title": "Maximal: longest values everywhere (test)"}
LONGEST = {
    "Date": "Воскресенье, 28 сентября",
    "Next alarm": "◷ 20:08 (пн)",
    "Sun time": "22:58",
    "Today range": "-35/-42°",
    "Tomorrow range": "-35/-42°",
    "Umbrella percent": "100%",
    "Row 1 • Breezy temperature": "-35°",
    "Row 2 • Like / arrow wind / humidity": "↖ 12,5 м/с like -42°",
}


def maximal(item):
    """Wrap the text formula: the longest value while the "maximal" switch is on."""
    title = item.get("internal_title")
    if item.get("internal_type") == "TextModule" and title in LONGEST:
        expression = item["text_expression"]
        inner = expression[1:-1] if expression.startswith("$") else '"%s"' % expression
        item["text_expression"] = '$if(gv(maximal) = 1, "%s", %s)$' % (LONGEST[title], inner)
    for child in item.get("viewgroup_items", []):
        maximal(child)


def strip(item, *prefixes):
    return {k: v for k, v in item.items() if k.startswith(prefixes)}


def row_text(style, title, expression):
    item = strip(style, "text_", "paint_", "fx_")
    item.update(internal_type="TextModule", internal_title=title, text_expression=expression)
    return item


def row_icon(style, title, icon, formula=None):
    item = strip(style, "paint_", "fx_")
    item.update(internal_type="FontIconModule", internal_title=title, icon_set=MDI,
                icon_icon=icon, icon_size=ROW_ICON)
    if formula:
        item.update(internal_toggles={"icon_icon": 10}, internal_formulas={"icon_icon": formula})
    return item


def stack(title, children, margin, anchor=None, x=None, y=None, events=None):
    item = {"internal_type": "StackLayerModule", "internal_title": title,
            "config_stacking": "HORIZONTAL_CENTER", "config_margin": margin,
            "viewgroup_items": children}
    if anchor:
        item.update(position_anchor=anchor, position_offset_x=x, position_offset_y=y)
    if events:
        item["internal_events"] = events
    return item


def main(base, fonts_dir, target):
    source = zipfile.ZipFile(base)
    preset = json.loads(source.read("preset.json").decode("utf-8"))
    info = preset["preset_info"]
    info.update(title=TITLE, id=str(uuid.uuid4()), ts=int(time.time() * 1000))
    info["description"] = (
        "Manrope clock, Breezy temperature and icon; full date, "
        "next alarm and sunrise/sunset on the left; today, tomorrow and the umbrella (Globals: "
        "umbrella_test, umbrella_min) on the right. Reboot the phone once after the first "
        "import so the home screen loads the fonts. Data from Breezy Bridge 1.4+.")

    items = preset["preset_root"]["viewgroup_items"]
    by_title = {item.get("internal_title"): item for item in items}
    style = by_title["Row 2 • Like / arrow wind / humidity"]       # row text style
    icon_style = dict(by_title["Umbrella • icon (see Globals)"])   # row icon style
    icon_style.pop("internal_toggles", None)
    icon_style.pop("internal_formulas", None)
    date_row = by_title["Date + next alarm"]
    tomorrow_row = by_title["Row 3 • Tomorrow maximum/minimum"]
    today_row = by_title["Today • Breezy high/low"]
    icon = by_title["Row 1 • Current weather icon (Breezy, Iconify mdi)"]
    left_x = date_row["position_offset_x"]
    right_x = style["position_offset_x"]
    bottom_y = today_row["position_offset_y"]

    date_row.update(internal_title="Date", text_expression=DATE)
    date_row.setdefault("internal_toggles", {})["text_size"] = 10
    date_row.setdefault("internal_formulas", {})["text_size"] = DATE_SIZE

    alarm_sun = stack("Next alarm + next sunset/sunrise", [
        row_text(style, "Next alarm", ALARM),
        stack("Sun", [row_icon(icon_style, "Sun icon", "weather-sunset-down", SUN_ICON),
                      row_text(style, "Sun time", SUN_TIME)], 3),
    ], GROUP_MARGIN, "TOPLEFT", left_x, bottom_y, date_row.get("internal_events"))

    percent = stack("Umbrella percent (Globals: umbrella_test, umbrella_min)", [
        row_text(style, "Umbrella percent", UMBRELLA_PERCENT)], 0)
    percent["internal_toggles"] = {"config_visible": 10}
    percent["internal_formulas"] = {"config_visible": UMBRELLA_VISIBLE}
    tomorrow = stack("Today + tomorrow (+ umbrella)", [
        row_text(style, "Today range", "$br(breezy, today_range)$"),
        stack("Tomorrow", [
            row_icon(icon_style, "Tomorrow icon: calendar, or umbrella with rain",
                     "calendar-arrow-right", TOMORROW_ICON),
            row_text(style, "Tomorrow range", TOMORROW),
            percent,
        ], 4),
    ], GROUP_MARGIN, "TOPRIGHT", right_x, bottom_y, tomorrow_row.get("internal_events"))
    icon["internal_formulas"]["icon_icon"] = WEATHER_ICON

    dropped = {"Today • Breezy high/low", "Row 3 • Tomorrow maximum/minimum",
               "Umbrella • percent (see Globals)", "Umbrella • icon (see Globals)"}
    result = []
    for item in items:
        if item.get("internal_title") in dropped:
            continue
        result.append(item)
        if item is date_row:
            result.append(alarm_sun)
        if item is style:
            result.append(tomorrow)
    for item in result:
        maximal(item)
    preset["preset_root"]["globals_list"]["maximal"] = MAXIMAL
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
