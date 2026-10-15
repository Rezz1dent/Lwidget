# Breezy Bridge — TODO

## Settings screen

- [x] **Language switch in the top-right corner.** (done in 1.5) Replace the "Language" dropdown at the bottom
  with a small rectangle on the same row as the "Breezy Bridge" title, aligned right, showing the
  current language ("EN"). Tapping it opens a short dropdown with "EN / RU". English stays the
  default.

- [x] **Quieter language switch.** (done in 1.6) The "EN ▾" box should not stand out: grey text and grey
  border (like the secondary text), not the blue accent color.

- [x] **Complete setup instructions on the settings screen** (done in 1.6) (both English and Russian strings).
  Replace the short intro ("grant access, then refresh the forecast") with numbered steps:
  1. Allow access to Breezy Weather (button below).
  2. In Breezy Weather: Settings → Widgets & live wallpapers → "Send weather data to Breezy
     Weather Update Notifier" → enable Breezy Bridge.
  3. Turn off battery restrictions for Breezy Bridge (and Breezy Weather) in the system settings,
     so updates are not blocked in the background; ideally a button that opens that screen.
  4. Refresh the weather in Breezy Weather (or tap "Read Breezy data and send to KWGT").
  If Breezy does not list the bridge in step 2: tap "Read Breezy data and send to KWGT", close
  Breezy completely and reopen its settings.

- [x] **Day/night switch can be late.** (done in 1.6) The re-send at sunrise/sunset uses an inexact
  `AlarmManager.set(RTC)`, which Doze / app standby can delay for hours (seen: moon icon at
  13:00). Consider `setAndAllowWhileIdle(RTC_WAKEUP)` or `setWindow`, and check the status line
  time ("Data received HH:MM") when it happens. Preset v58+ picks sun/moon with KWGT's own
  `ai(isday)`, so the widget no longer depends on it.

- [x] **Outline sun.** (done in 1.6) Send `weather-sunny` (outline, as in Breezy's widget) instead of
  `white-balance-sunny` for a clear day in `icon_mdi`. Preset v60 already swaps it.

## Precipitation

- [x] **Rain / snow / mix.** (done in 1.8) Send the kind of precipitation now and tomorrow
  (`precip_now_type`, `tomorrow_precip_type`: rain / snow / mix) and a matching MDI icon
  (`water-outline`, `snowflake`, `snowflake-melt`), so the widget can swap the drop.
