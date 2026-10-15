# Breezy Bridge — TODO

## Settings screen

- [x] **Language switch in the top-right corner.** (done in 1.5) Replace the "Language" dropdown at the bottom
  with a small rectangle on the same row as the "Breezy Bridge" title, aligned right, showing the
  current language ("EN"). Tapping it opens a short dropdown with "EN / RU". English stays the
  default.

- [ ] **Quieter language switch.** The "EN ▾" box should not stand out: grey text and grey
  border (like the secondary text), not the blue accent color.

- [ ] **Complete setup instructions on the settings screen** (both English and Russian strings).
  Replace the short intro ("grant access, then refresh the forecast") with numbered steps:
  1. Allow access to Breezy Weather (button below).
  2. In Breezy Weather: Settings → Widgets & live wallpapers → "Send weather data to Breezy
     Weather Update Notifier" → enable Breezy Bridge.
  3. Turn off battery restrictions for Breezy Bridge (and Breezy Weather) in the system settings,
     so updates are not blocked in the background; ideally a button that opens that screen.
  4. Refresh the weather in Breezy Weather (or tap "Read Breezy data and send to KWGT").
  If Breezy does not list the bridge in step 2: tap "Read Breezy data and send to KWGT", close
  Breezy completely and reopen its settings.

- [ ] **Day/night switch can be late.** The re-send at sunrise/sunset uses an inexact
  `AlarmManager.set(RTC)`, which Doze / app standby can delay for hours (seen: moon icon at
  13:00). Consider `setAndAllowWhileIdle(RTC_WAKEUP)` or `setWindow`, and check the status line
  time ("Data received HH:MM") when it happens. Preset v58+ picks sun/moon with KWGT's own
  `ai(isday)`, so the widget no longer depends on it.
