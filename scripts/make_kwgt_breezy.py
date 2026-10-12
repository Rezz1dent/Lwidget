#!/usr/bin/env python3
"""Convert our editable AccuWeather KWGT v2 preset to Breezy's bridge variables."""
import io
import json
import os
import urllib.request
import zipfile

URL = (
    "https://raw.githubusercontent.com/Rezz1dent/Lwidget/"
    "assets/kwgt-accuweather/kwgt/Minimal_Clock_AccuWeather_v2.kwgt"
)
with urllib.request.urlopen(URL, timeout=40) as response:
    original = response.read()

source = zipfile.ZipFile(io.BytesIO(original))
preset = json.loads(source.read("preset.json").decode("utf-8"))
counter = {"temp": 0, "feels": 0, "condition": 0, "icon": 0}

def transform(obj):
    if isinstance(obj, dict):
        return {k: transform(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [transform(v) for v in obj]
    if isinstance(obj, str):
        if "wi(flik)" in obj or "wi(feels)" in obj:
            counter["feels"] += 1
            return "$br(breezy, feels)$"
        if "wi(cond)" in obj or "wi(condition)" in obj:
            counter["condition"] += 1
            return "$br(breezy, condition)$"
        if "wi(icon)" in obj:
            counter["icon"] += 1
            return "$br(breezy, icon)$"
        if "wi(temp)" in obj:
            counter["temp"] += 1
            return "$br(breezy, temp)$"
    return obj

preset = transform(preset)
if not (counter["temp"] and counter["feels"]):
    raise RuntimeError(f"Missing temperature or feels-like formula in template: {counter}")

os.makedirs("dist", exist_ok=True)
out = "dist/Minimal_Clock_Breezy_Weather.kwgt"
with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as dest:
    for name in source.namelist():
        if name == "preset.json":
            dest.writestr(name, json.dumps(preset, ensure_ascii=False, separators=(",", ":")))
        else:
            dest.writestr(name, source.read(name))
with zipfile.ZipFile(out) as check:
    assert check.testzip() is None
    json.loads(check.read("preset.json"))
print(f"Updated formulas: {counter}")
print(f"Created {out} ({os.stat(out).st_size} bytes)")
