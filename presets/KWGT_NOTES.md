# KWGT notes for the Breezy presets

Working notes for building and editing `.kwgt` presets in this repo. "Verified" means seen on
the device (Android 15, ColorOS/HyperOS-style launcher) or in a preset exported by KWGT itself;
everything else is from documentation or community guides and should be checked once.

Sources: presets exported from KWGT on the device (`claude_test`, `test2`…`test5`, `AllInOne v252`),
[A guide to Kode basics (Tored)](https://theothertored.github.io/kode-guide/),
[Kustom docs: functions](https://docs.kustom.rocks/docs/reference/functions/) (not reachable from the
build container; summaries via search), [Kustom forum](https://forum.kustom.rocks/).

## Lessons learned on the device (verified)

- **Fonts bundled in the preset** (`fonts/*.ttf`, `kfile://org.kustom.provider/fonts/…`) work on the
  home screen only **after a reboot** the first time; the editor shows them immediately.
- **Icon fonts bundled in the preset** (`icons/x.ttf` + `x.json`, IcoMoon) did **not** work on the home
  screen ("?" or a wrong glyph), even though the editor drew them. The old Meteo icons only worked
  because Meteo is **built into KWGT**. Use built-in sets instead:
  Iconify Material Design Icons = `"icon_set": "iconify://mdi?name=Material%20Design%20Icons"`,
  icon names as on pictogrammers.com (`weather-night`, `umbrella-outline`, `calendar-arrow-right`…).
- **Shadow blur grows the element's frame** and pushes the text down/right. Keep blur small (2–6) and
  make the shadow light with the color's alpha instead (`#68000000`).
- An **Iconify icon** draws its shadow much farther than text with the same distance.
- **A transparent icon still casts its shadow**: hide both `paint_color` and `fx_shadow_color`.
- **Children of an Overlap group ignored their x offset** in one test (percent drawn over the umbrella).
  For things in a row use a **Stack group** instead.
- Widget size comes from the launcher; with the **Auto** sizing mode KWGT stores the scale it computed
  (`config_scale_value`). The user's working setup: grid 8×3, scale 155.
- **Manrope ascent** is 0.138 em taller than the system font: switching fonts moves text down.
- KWGT shows weekday/month names in the **system language**; for English words write them out:
  `if(df(f)=1, MONDAY, df(f)=2, TUESDAY, …)`.

## Preset file format

A `.kwgt` is a zip: `preset.json`, `preset_thumb_portrait.jpg`, `preset_thumb_landscape.jpg`,
optional `fonts/`, `icons/`, `bitmaps/`. `preset_info` holds title, id (uuid), ts, width/height of the
widget it was saved from; `preset_root` is the `RootLayerModule`.

### Common item keys

| Key | Values / notes |
|---|---|
| `internal_type` | `TextModule`, `ShapeModule`, `FontIconModule`, `BitmapModule`, `OverlapLayerModule`, `StackLayerModule`, `KomponentModule`, root `RootLayerModule` |
| `internal_title` | name shown in the editor list |
| `position_anchor` | `TOPLEFT`, `TOP`, `TOPRIGHT`, `CENTERLEFT`, `CENTER` (default), `BOTTOM`, `BOTTOMRIGHT`… |
| `position_offset_x/y` | offset from the anchor; for `…RIGHT` anchors x counts from the right edge |
| `position_padding_top/bottom/right/left` | padding |
| `paint_color` | `#AARRGGBB` |
| `paint_mode` | `CLEAR` erases what is below (cut text in half with a rectangle), `DST` invisible (tap areas) |
| `internal_events` | taps: `[{"type": "SINGLE_TAP", "action": "LAUNCH_APP", "intent": "intent:#Intent;…;end"}]` |
| `internal_toggles` | per property: `10` = formula, `100` = bound to a global, `0` = fixed value |
| `internal_formulas` | `{"property": "$formula$"}` (with toggle 10) |
| `internal_globals` | `{"property": "global_name"}` (with toggle 100) |
| `config_visible` | visibility formula on groups: `ALWAYS` / `NEVER` / `REMOVE` |

### Text (`TextModule`)

`text_expression`, `text_size`, `text_family` (`sans-serif-light`, `sans-serif-medium`, or
`kfile://org.kustom.provider/fonts/X.ttf`), `text_align` (`LEFT`/`CENTER`/`RIGHT`),
`text_filter` (`["UP"]`, `["LO"]`), `text_size_type` (`FIT_TO_BOX` scales the font so the text fits
`text_width`), `text_width`.
Shadow: `fx_shadow: "OUTER"`, `fx_shadow_blur`, `fx_shadow_distance`, `fx_shadow_direction`,
`fx_shadow_color`.
No **letter spacing** key seen yet; the forum says Text has none and "Morphing Text" has character
spacing. Workaround used in v51: our own font with empty **spacer glyphs** of exact width
(`Manrope-Light-Spaced.ttf`, U+E100+k = k·0.002 em) placed between the letters.

### Shapes, icons, bitmaps

- `ShapeModule`: `shape_type` (`RECT`…), `shape_width`, `shape_height`, `shape_corners`.
- `FontIconModule`: `icon_set`, `icon_icon`, `icon_size` (+ formula on `icon_icon`).
- `BitmapModule`: `bitmap_mode: "VECTOR"`, `bitmap_width`, `bitmap_bitmap`, `bitmap_svg` (SVG string).

### Groups

- `OverlapLayerModule`: children on top of each other; size = largest child; `config_visible`.
- `StackLayerModule`: children in a row/column; `config_stacking` (`HORIZONTAL_CENTER`,
  `HORIZONTAL_BOTTOM`, `VERTICAL_CENTER`, `VERTICAL_RIGHT`…), `config_margin` (gap, can be negative),
  `config_scale_value` (scale of the group). Use it for "hours | minutes", "icon + percent", etc.
- `KomponentModule`: reusable block with its own `globals_list`.

### Globals (root or Komponent `globals_list`)

```json
"globals_list": {
  "fontbold": {"index": 1, "type": "FONT",   "title": "FontBold", "value": "kfile://org.kustom.provider/fonts/Roboto-Bold.ttf"},
  "color":    {"index": 3, "type": "COLOR",  "title": "Color",    "value": "#FFFFFFFF"},
  "rain":     {"index": 4, "type": "SWITCH", "title": "rain"},
  "url":      {"index": 5, "type": "TEXT",   "title": "url",      "value": "https://…"}
}
```

Read in formulas with `gv(name)`; bind a property with toggle `100` + `internal_globals`.
`NUMBER` is assumed to follow the same shape with `"value"`.

## Kode (formulas) essentials

- Only text between `$…$` is evaluated. Quote strings with `"…"`; unquoted words are strings too
  (`ALWAYS`, `weather-night`), but `-`, `,`, `(` etc. need quotes.
- Strings that look like numbers are converted: `"05" + 1` = 6. Comparisons `= != < > <= >=`,
  `~=` = contains / regex test.
- `&` and `|` have **equal precedence**, evaluated left to right: use parentheses.
  Non-1 numbers count as false for `&`/`|`; empty string is false for `if()`.
- `if(c1, v1, c2, v2, …, else)`: multiple pairs, no nesting needed; no else returns `""`.
- **`lv(name, value)`** stores a local variable (returns `""`), read with `#name`:
  `$lv(p, tc(reg, br(breezy, tomorrow_precip), "[^0-9]", "")) + if(#p >= 70, #p + "%")$`.
  Use it to avoid repeating long sub-formulas.
  **Never name a variable like a Kode function** (`mi`, `bi`, `si`, `df`...): v75's first build
  used `lv(mi, …)` / `lv(bi, …)` in size formulas and the rows vanished on the phone; plain
  sub-formulas worked. Numeric properties (`text_size`, `icon_size`, `position_offset_y`) take
  formulas like any other (toggle 10).
- `df(format[, date])`: `HH:mm`, `EEEE` (weekday, system language), `d MMM`; `df(f)` weekday 1=Mon…7=Sun,
  `df(e)` used for weekday in AllInOne; literal text in single quotes: `df("m 'min'")`.
- Dates: `dp()`, Kustom date format `2022y11M10d13h13m41s`, offsets `a1d` (add) / `r2h` (remove).
- `tf(timespan[, format])`: tokens `h m s D H M S`.
- `tc(mode, text, …)`: `low`, `up`, `cap`, `cut`, `ell`, `len`, `split`, `reg` (regex replace, `$1`),
  `count`, `lines`, `html`, `lpad`/`rpad`, `n2w`, `roman`, `fmt`, `nfmt`…
- `mu(mode, …)`: `round`, `floor`, `ceil`, `min`, `max`, `abs`, `sqrt`, `rnd`…
- `ai(…)` (astronomy, from KWGT's location, offline): `sunrise`, `sunset`, `isday` (1/0),
  `nsunrise`/`nsunset` (time until next, use with `tf()`), `moonrise`, `moonset`, `mphase`, `mill`;
  `df(HH:mm, ai(sunset))`.
- `si(alarmon)`, `si(alarmd)` (next alarm), `bi(level)`, `bi(charging)`, `mi(title)`, `ci(…)` calendar,
  `wg(url, mode…)` web get, `br(name, var)` broadcast variables (our bridge: `br(breezy, …)`).
