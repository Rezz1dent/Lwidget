# Breezy Bridge

Minimal Android bridge that sends weather from **Breezy Weather** to **KWGT**, without making its own network or location requests.

**Independent, unofficial project.** Not affiliated with Breezy Weather or Kustom Industries.

## Requirements

- Android 8.0+
- Breezy Weather **6.1.0+**, with its experimental weather ContentProvider
- KWGT (Kustom Widget Maker)

## Setup

1. Install the `bridge-debug.apk` from the latest Breezy Bridge Actions build.
2. Open **Settings → Apps → Breezy Bridge → Open app settings**.
3. Tap **Allow access to Breezy Weather** and approve the permission.
4. In Breezy Weather's **Widgets & live wallpapers** settings, configure its **Update Notifier** to send notifications to **Breezy Bridge**.
5. Refresh Breezy Weather. Use **Read Breezy data and send to KWGT** for a manual test.
6. In KWGT, use `$br(breezy, temp)$`, `$br(breezy, today_compact)$`, etc. The bridge exposes 33 variables, all searchable in its settings screen; tap any variable to copy its formula.

### Day/night icons

`icon_flat` and `icon` already switch to night variants (moon, moon behind a cloud) using Breezy's
hourly `isDaylight` data, so the widget only needs `$br(breezy, icon_flat)$`. `is_day` is `1` by day
and `0` at night. The bridge re-sends cached data at the next sunrise/sunset with an inexact alarm,
so the icon switches even without a Breezy refresh (precision: Breezy's hourly steps, plus a few
minutes of alarm delay).

### Icon styles

`icon_glyph` and `tomorrow_icon_glyph` hold a glyph name in the `breezy_meteo` font (extended with the Breezy icons) bundled with
the preset `presets/Breezy_Minimal_v26__Icons.kwgt`. The style is chosen on the bridge settings
screen, the widget formula stays `$br(breezy, icon_glyph)$`:

- **Filled (Meteo)**: the same icons as `icon_flat`.
- **Outline (Meteo)**: outline glyphs of the same font, with fog by day/night and moon behind a cloud.
- **Breezy (Material Design Icons)**: the icons of Breezy Weather's own widgets, including the
  moon with stars.

The preset is built from a Meteo preset with `scripts/build_breezy_preset.py`
(`pip install fonttools`). The settings screen language (English by default, or Russian) is
chosen on the same screen.

### Credits

- Weather icons of the "Breezy" style: [Material Design Icons](https://pictogrammers.com/library/mdi/)
  by Pictogrammers, Apache License 2.0 (paths in `scripts/mdi_weather_icons.json`, as used by
  Breezy Weather's widgets).
- Filled and outline styles: the Meteo icon font (IcoMoon) bundled with the original preset.

### Notes

- The app deliberately has **no launcher icon**. Its icon still appears in Android's app settings and on its APK.
- English is the default interface language; Russian is supported.
- The provider API is experimental (major version 0); a future Breezy release may require an adapter update.
- Data comes from whichever forecast service Breezy Weather itself uses. This bridge does **not** support other weather apps directly.
