# Breezy Bridge + KWGT widget — project status

Snapshot for picking the work up in a new session. Everything lives on branch
`feature/breezy-bridge-v2` of `Rezz1dent/Lwidget` (the rest of the repo is the old Lwidget
fork, not used any more). Conversation with the owner is in Russian.

## What it is

- **Breezy Bridge** (`bridge/`, Android, Java, no launcher icon, package
  `com.rezz1dent.breezykwgtbridge`): reads Breezy Weather's ContentProvider
  (`org.breezyweather.provider.weather`, needs Breezy 6.1+ and the `READ_PROVIDER`
  permission) when Breezy's "Update Notifier" broadcast arrives, and sends ~35 variables to
  KWGT as `$br(breezy, name)$`. Current version **1.7** (versionCode 10). APK is built by the
  GitHub Actions workflow "Breezy Bridge APK" on every push to `bridge/**`
  (artifact `breezy-bridge-debug`).
- **KWGT preset** "Breezy Minimal" (`presets/`): clock + Breezy weather, Manrope fonts,
  Material Design Icons via KWGT's built-in Iconify set.

Docs in the repo: `bridge/README.md` (setup, variables, credits), `bridge/TODO.md`,
`presets/KWGT_NOTES.md` (KWGT file format, Kode formulas, lessons learned on the phone —
read it before editing presets).

## Current widget: v7.4 (`presets/Breezy_Minimal_v74__Manrope.kwgt`)

Built by a chain of scripts from the owner's hand-tuned exports:
`v70` (exported from the phone) → `build_v71_preset.py` → `build_v72_preset.py` → owner's
hand-tuned `v73` (exported; sizes: middle row 22, bottom row 18) → `build_v73_preset.py`
(alarm icon) = `v74`. Always start the next change from the newest export of the owner. Fonts come from `make_manrope_fonts.py` (needs the variable
`Manrope[wght].ttf` from google/fonts; static weights, tabular clock digits, narrow minus,
spacer glyphs in `Manrope-Light-Spaced`).

Layout (root ~497 × 190 units at scale 160, widget 1458 × 533 px, grid 8×3, KWGT sizing Auto):

```
05 28            -35° ☀              hours ExtraBold / minutes ExtraLight (95), temp 78, icon 65
───────────────────────────
Воскресенье, 28 сент.   ↖ 12,5 м/с 💧12,5 👤-42°        middle row, size 22 (owner)
⏰ 20:08 (пн) 🌇 22:58    -35/-42° 📅 -35/-42° ☂ 100% 💧12,5   bottom row, size 18 (owner)
```

- Middle: date with short month; stack: wind | rain now (`precip_now`, only while it
  rains) | feels-like (`account-outline` icon + `like`).
- Bottom left: stack: alarm (`alarm` / `alarm-off` icon + time) | next sunset by day /
  sunrise by night (KWGT `ai()`, its own location, offline).
- Bottom right: stack: today's range | `calendar-arrow-right` + tomorrow's range | umbrella
  group (`umbrella-outline` + probability + drop + `tomorrow_precip_mm`), hidden with
  `config_visible = REMOVE` below the threshold.
- Weather icon: bridge's `icon_mdi`, sun/moon variant re-chosen in KWGT with `ai(isday)`;
  clear day = outline `weather-sunny`.
- Shadow everywhere: `#68000000`, distance 1, small blur (blur grows the frame and shifts text).
- Root globals: `umbrella_test` (switch, always show umbrella), `umbrella_min` (number, %,
  owner uses 60), `maximal` (switch: every row shows its longest value, for overlap checks).

Sizes 20/16 were computed so the rows fit with `maximal` on; the owner then set 22/18 by hand; width estimates: text widths from
the font are exact, stack icons/margins take ~14% more than nominal.

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

- Check v7.4 on the phone with `maximal` on (bottom row has little spare width).
- If size 16 is too small: drop the weekday from the alarm time, or the "°" of the ranges.
- Possible upstream issue for Breezy: add its own `ACTION_UPDATE_NOTIFIER` to `<queries>`.
- Publishing the bridge: rename to something neutral (e.g. "Weather Bridge for KWGT"),
  keep "unofficial" note; MDI icons are Apache-2.0, Manrope OFL (`presets/Manrope-OFL.txt`).
