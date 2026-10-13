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
6. In KWGT, use `$br(breezy, temp)$`, `$br(breezy, today_compact)$`, etc. The bridge exposes 30 variables, all searchable in its settings screen; tap any variable to copy its formula.

### Notes

- The app deliberately has **no launcher icon**. Its icon still appears in Android's app settings and on its APK.
- English is the default interface language; Russian is supported.
- The provider API is experimental (major version 0); a future Breezy release may require an adapter update.
- Data comes from whichever forecast service Breezy Weather itself uses. This bridge does **not** support other weather apps directly.
