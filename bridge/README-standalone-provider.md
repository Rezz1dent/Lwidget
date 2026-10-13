# Breezy → KWGT standalone bridge (experimental v11)

**This is a testing preview.** It uses Breezy Weather's still-experimental
ContentProvider v0.x instead of imitating Lwidget, so its Android package
`com.rezz1dent.breezykwgtbridge` can coexist with the real Lwidget app.

It keeps existing KWGT expressions such as `$br(breezy, temp)$`,
`$br(breezy, details)$`, `$br(breezy, today_compact)$`, and all the other
variables from the original bridge. In addition, it offers two optional
bitmap image URI variables for Breezy's separately installed Flat Icon Provider.

## Install & test on Android

1. Use GitHub Actions workflow **Breezy to KWGT mini bridge** on branch
   `feature/standalone-provider-bridge-v11`; download the
   `breezy-kwgt-provider-v11-preview` artifact and install its APK.
2. Find **Breezy KWGT Bridge • Provider** in Android system app info, then
   open **App settings** (`APPLICATION_PREFERENCES`; no launcher icon).
3. Click **Provide access to Breezy weather** and grant the runtime
   `org.breezyweather.READ_PROVIDER` permission. This is a sensitive
   permission defined by Breezy itself. If Android does not present a
   permission prompt, grant it from the new bridge's system app permissions.
4. Click **Get Breezy data and send to KWGT**. The status field should say
   **Обновлено из Breezy ContentProvider: [location]**.
5. Open your existing KWGT v10 preset. It should keep working because every
   original variable key is unchanged. Future Breezy updates should trigger
   `ACTION_UPDATE_NOTIFIER`, which refreshes the variables automatically.

**If the original legacy mini bridge remains installed:** disable Breezy's
“Send to Lwidget” gadgetbridge export while testing; both bridges write to
the same `breezy` namespace in KWGT, otherwise the broadcasts may race.

If you get **permission denied**, **provider unavailable**, or **incompatible
version**, report the exact error shown at the top of the bridge's settings.

## Optional official Breezy Flat icons in KWGT

The official Breezy [Flat Icon Provider](https://github.com/breezy-weather/flat-icon-provider)
must be installed **separately** from its upstream releases. Nothing from
that pack is included here. The graphic assets have **non-free licensing**
as described in upstream's README; please do not redistribute the images.

The separate APK provides the images locally. The standalone bridge acts as
a read-only URI adapter for Android resources in that installed package:
- `$br(breezy, icon_uri)$` — current weather image
- `$br(breezy, tomorrow_icon_uri)$` — tomorrow's weather image

A second preset, **Breezy_Flat_Icons_Experimental_v11.kwgt**, replaces the
Meteo FontIcon modules with flat Bitmap modules using those two formulas.
It is generated alongside the working **Breezy_Minimal_Meteo_v10.kwgt**.
**KWGT's access to those content URIs has not yet been tested on-device.**
If the images are blank, keep using the Meteo version and report the result.

The URI adapter reads graphics from the installed app on each request
without embedding or persisting its assets in the repository/APK/preset.
No icons are downloaded over the network.

## Provider protocol

The implementation follows the public [Breezy data sharing](https://github.com/breezy-weather/breezy-weather-data-sharing-lib)
protocol: `content://org.breezyweather.provider.weather/version`,
`locations?limit=1`, `weather` selected by location ID. Forecast JSON
is GZIP-compressed; query uses `temperatureUnit=c` and `speedUnit=kph`
with unit verification before converting values to existing KWGT fields.
Provider major version is checked, and unsupported versions fail closed.

The first saved Breezy location is currently used. The source API is
**experimental**; please do not treat this preview as a production release.

## Credits and licensing

- Breezy Weather: https://github.com/breezy-weather/breezy-weather
- ContentProvider schema: https://github.com/breezy-weather/breezy-weather-data-sharing-lib
- Optional Flat icon pack: https://github.com/breezy-weather/flat-icon-provider
- Lwidget: https://github.com/LeanBitLab/Lwidget

Upstream icon assets belong to their respective owners and are not shipped.
