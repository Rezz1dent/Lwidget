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
6. In KWGT, use `$br(breezy, temp)$`, `$br(breezy, today_compact)$`, etc. The bridge exposes 34 variables, all searchable in its settings screen; tap any variable to copy its formula.

### Day/night icons

`icon_flat` and `icon` already switch to night variants (moon, moon behind a cloud) using Breezy's
hourly `isDaylight` data, so the widget only needs `$br(breezy, icon_flat)$`. `is_day` is `1` by day
and `0` at night. The bridge re-sends cached data at the next sunrise/sunset with an inexact alarm,
so the icon switches even without a Breezy refresh (precision: Breezy's hourly steps, plus a few
minutes of alarm delay).

### Precipitation now

`precip_now` is the current hour's precipitation from Breezy's hourly forecast in mm with one
decimal ("0,6"), empty when it is dry. KWGT can show it only while it rains:
`$if(br(breezy, precip_now) != "", br(breezy, precip_now) + " мм")$`.

### Breezy icons

`icon_mdi` and `tomorrow_icon_mdi` hold the [Material Design Icons](https://pictogrammers.com/library/mdi/)
name of the weather, as used by Breezy Weather's own widgets (`weather-night`,
`weather-partly-cloudy`, `weather-pouring`...). KWGT 3.80+ has these icons built in:
in the icon element choose the icon set **Iconify → Material Design Icons (mdi)** and use the
formula `$br(breezy, icon_mdi)$`. Ready preset: `presets/Breezy_Minimal_v28__Breezy_icons.kwgt`
(exported from KWGT; the icon set is stored as `iconify://mdi?name=Material%20Design%20Icons`).
`icon_flat` (built-in Meteo font) still works.

Icon fonts bundled inside a preset do not work on the home screen (the KWGT editor shows them,
the widget shows "?"), so the bridge relies on icon sets built into KWGT.

### Credits

- Weather icons: [Material Design Icons](https://pictogrammers.com/library/mdi/) by Pictogrammers,
  Apache License 2.0, provided by KWGT through Iconify. The bridge only sends icon names.

### Breezy does not list the bridge

Breezy Weather does not declare its own `ACTION_UPDATE_NOTIFIER` in its manifest `<queries>`,
so on Android 11+ it only sees the bridge after the bridge has read its content provider. That
visibility is lost after a reboot or a bridge update; Breezy then shows "no compatible packages"
and removes the bridge from its Update Notifier setting. Since 1.5 the bridge reads the provider on
boot and after its own update. If Breezy still does not list it: open the bridge, tap
**Read Breezy data and send to KWGT**, close Breezy completely, reopen its settings and enable the
bridge again.

### Notes

- The app deliberately has **no launcher icon**. Its icon still appears in Android's app settings and on its APK.
- English is the default interface language; Russian is supported (switch in the top-right corner).
- The provider API is experimental (major version 0); a future Breezy release may require an adapter update.
- Data comes from whichever forecast service Breezy Weather itself uses. This bridge does **not** support other weather apps directly.
