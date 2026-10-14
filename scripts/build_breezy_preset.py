#!/usr/bin/env python3
"""Build the Breezy Minimal KWGT preset that shows Breezy's own weather icons.

Usage: build_breezy_preset.py BASE.kwgt OUT.kwgt

Breezy Weather's widgets use Material Design Icons. KWGT 3.80+ has them built in
(icon set: Iconify -> "mdi"), so the preset bundles no icon font: the bridge sends
the MDI icon name as $br(breezy, icon_mdi)$.

Custom icon fonts bundled in the preset were tried (v24-v26) and do not work: the
KWGT editor draws them, but the home-screen widget shows "?". The old Meteo icons
only worked because Meteo is a font built into KWGT.

The Iconify icon set is stored by KWGT as "iconify://mdi?name=Material%20Design%20Icons"
(taken from a preset exported by KWGT, v28).
"""
import json
import sys
import time
import uuid
import zipfile

TITLE = "Breezy Minimal v28 • Breezy icons"
ICON_SET = "iconify://mdi?name=Material%20Design%20Icons"
ICON_FORMULA = "$br(breezy, icon_mdi)$"


def main(base, target):
    source = zipfile.ZipFile(base)
    preset = json.loads(source.read("preset.json").decode("utf-8"))
    info = preset["preset_info"]
    info["title"] = TITLE
    info["id"] = str(uuid.uuid4())
    info["ts"] = int(time.time() * 1000)
    info["description"] = (
        "Flat, transparent, two-column widget. Date+alarm on one line; Today high/low below. "
        "Right: temperature, Like+wind+humidity, Tomorrow high/low. Weather icon: Material "
        "Design Icons as in Breezy Weather (KWGT icon set Iconify -> mdi), day/night from "
        "Breezy Bridge 1.4+.")
    icons = 0
    for item in preset["preset_root"]["viewgroup_items"]:
        if "icon_set" in item and "icon_icon" in item.get("internal_formulas", {}):
            item["icon_set"] = ICON_SET
            item["internal_formulas"]["icon_icon"] = ICON_FORMULA
            item["internal_title"] = "Row 1 • Current weather icon (Breezy, Iconify mdi)"
            icons += 1
    assert icons == 1, icons

    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as out:
        for entry in source.infolist():
            if entry.filename.startswith("icons/"):
                continue  # Meteo font is no longer used
            data = source.read(entry.filename)
            if entry.filename == "preset.json":
                data = json.dumps(preset, ensure_ascii=False, indent=2).encode("utf-8")
            out.writestr(entry, data)


if __name__ == "__main__":
    main(*sys.argv[1:3])
