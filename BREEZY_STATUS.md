# Breezy Bridge + KWGT widget — project status

Snapshot for picking the work up in a new session. Everything lives on branch
`feature/breezy-bridge-v2` of `Rezz1dent/Lwidget` (the rest of the repo is the old Lwidget
fork, not used any more). Conversation with the owner is in Russian.

## What it is

- **Breezy Bridge** (`bridge/`, Android, Java, no launcher icon, package
  `com.rezz1dent.breezykwgtbridge`): reads Breezy Weather's ContentProvider
  (`org.breezyweather.provider.weather`, needs Breezy 6.1+ and the `READ_PROVIDER`
  permission) when Breezy's "Update Notifier" broadcast arrives, and sends ~35 variables to
  KWGT as `$br(breezy, name)$`. Current version **1.8** (versionCode 11). APK is built by the
  GitHub Actions workflow "Breezy Bridge APK" on every push to `bridge/**`
  (artifact `breezy-bridge-debug`).
- **KWGT preset** "Breezy Minimal" (`presets/`): clock + Breezy weather, Manrope fonts,
  Material Design Icons via KWGT's built-in Iconify set.

Docs in the repo: `bridge/README.md` (setup, variables, credits), `bridge/TODO.md`,
`presets/KWGT_NOTES.md` (KWGT file format, Kode formulas, lessons learned on the phone —
read it before editing presets).

## Current widget: v7.6 (`presets/Breezy_Minimal_v76__Manrope.kwgt`)

Built by a chain of scripts from the owner's hand-tuned exports:
`v70` (exported from the phone) → `build_v71_preset.py` → `build_v72_preset.py` → owner's
hand-tuned `v73` (exported; sizes: middle row 22, bottom row 18) → `build_v73_preset.py`
(alarm icon) = `v74` → `build_v75_preset.py` (automatic row sizes) = `v75` → `build_v76_preset.py` (rain / snow / mix icons) = `v76`. Always start the next change from the newest export of the owner. Fonts come from `make_manrope_fonts.py` (needs the variable
`Manrope[wght].ttf` from google/fonts; static weights, tabular clock digits, narrow minus,
spacer glyphs in `Manrope-Light-Spaced`).

Layout (root ~497 × 190 units at scale 160, widget 1458 × 533 px, grid 8×3, KWGT sizing Auto):

```
05 28            -35° ☀              hours ExtraBold / minutes ExtraLight (95), temp 78, icon 65
───────────────────────────
Воскресенье, 28 сент.   ↖ 12,5 м/с 💧12,5 👤-42°        middle row, size 22 / 20 (auto)
⏰ 20:08 (пн) 🌇 22:58    -35/-42° 📅 -35/-42° ☂ 100% 💧12,5   bottom row, size 20 / 18 (auto)
```

- Middle: date with short month; stack: wind | rain now (`precip_now`, only while it
  rains) | feels-like (`account-outline` icon + `like`).
- Bottom left: stack: alarm (`alarm` / `alarm-off` icon + time) | next sunset by day /
  sunrise by night (KWGT `ai()`, its own location, offline).
- Bottom right: stack: today's range | `calendar-arrow-right` + tomorrow's range | umbrella
  group (`umbrella-outline` + probability + drop + `tomorrow_precip_mm`), hidden with
  `config_visible = REMOVE` below the threshold.
- Precipitation icon (rain now, tomorrow's mm): bridge 1.8 `precip_now_icon` /
  `tomorrow_precip_icon` = `water-outline` (rain), `snowflake` (snow), `snowflake-melt` (mix:
  rain and snow each from a quarter of the sum, or a quarter of ice); drop with an older bridge.
- Weather icon: bridge's `icon_mdi`, sun/moon variant re-chosen in KWGT with `ai(isday)`;
  clear day = outline `weather-sunny`.
- Shadow everywhere: `#68000000`, distance 1, small blur (blur grows the frame and shifts text).
- Root globals: `umbrella_test` (switch, always show umbrella), `umbrella_min` (number, %,
  owner uses 60), `maximal` (switch: every row shows its longest value, for overlap checks),
  `precip_test` (number: 0 data, 1 rain, 2 snow, 3 mix; shows both precipitation blocks and
  the umbrella with that icon).

Automatic sizes (v7.5): KWGT cannot measure text, so each row estimates its width from the
character and icon counts of the current values (middle 0.52 em/char + 1.1 em/icon, bottom
0.55 + 1.3, plus margins; limit 445 units for both halves of a row) and uses the big size
(middle 22, bottom 20) when it fits, else the small one (20 / 18, the owner's sizes). Formulas
sit on `text_size` / `icon_size` of every text and icon and on `position_offset_y` of the row
roots (keeps the baseline). `maximal` always shows the small size. Constants at the top of
`build_v75_preset.py`. Calibration: text widths from the font are exact, stack icons/margins
take ~14% more than nominal; the estimate is deliberately on the wide side.

## Decisions and why

- **Icons**: icon fonts bundled in a preset did not work on the home screen ("?"); only
  KWGT built-in sets work → Iconify `iconify://mdi?name=Material%20Design%20Icons`.
- **Fonts** bundled in the preset (`fonts/*.ttf`) work, but the home screen needs **one phone
  reboot** after the first import (and after a font file with the same name changes).
- **English weekday** with a half-cut word (v51–v53) was tried and dropped by the owner.
- Bridge visibility: Breezy has no `<queries>` entry for its own Update Notifier, so it only
  sees the bridge after the bridge read its provider; the bridge re-reads it on boot/update
  (`BootReceiver`). If Breezy lists "no compatible packages": tap "send to KWGT" in the
  bridge, close Breezy, reopen its settings, enable the bridge.
- Temperatures arrive with "-" (hyphen); the bundled fonts draw it as a narrow minus.

## Open / ideas

- Check v7.5 on the phone: big sizes with short values, switch to small with long ones /
  `maximal`. If the switch comes too early or too late, tune the coefficients or `FIT`.
- Possible upstream issue for Breezy: add its own `ACTION_UPDATE_NOTIFIER` to `<queries>`.
- Publishing the bridge: rename to something neutral (e.g. "Weather Bridge for KWGT"),
  keep "unofficial" note; MDI icons are Apache-2.0, Manrope OFL (`presets/Manrope-OFL.txt`).
