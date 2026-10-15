package com.leanbitlab.breezybridge;

import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.database.Cursor;
import android.net.Uri;
import android.util.Log;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.util.Calendar;
import java.util.Date;
import java.util.Locale;
import java.util.TimeZone;
import java.text.SimpleDateFormat;
import java.util.zip.GZIPInputStream;

/**
 * Experimental Breezy Weather ContentProvider -> the existing KWGT variable contract.
 * Based on the published Breezy data-sharing sample/schema (provider API 0.x).
 * Hourly data is requested only for its "isDaylight" flags (day/night icons).
 */
public final class ProviderBridge {
    private static final String TAG = "BreezyProviderBridge";
    private static final String[] PACKAGES = {"org.breezyweather", "org.breezyweather.debug"};
    private ProviderBridge() {}

    private static String authority(String pkg) {
        return pkg + ".provider.weather";
    }

    public static String permissionToRequest(Context context) {
        for (String pkg : PACKAGES) {
            if (context.getPackageManager().resolveContentProvider(authority(pkg), 0) != null) {
                String perm = pkg + ".READ_PROVIDER";
                if (context.checkSelfPermission(perm) != PackageManager.PERMISSION_GRANTED) {
                    return perm;
                }
                return null;
            }
        }
        return null;
    }

    public static String status(Context context) {
        for (String pkg : PACKAGES) {
            if (context.getPackageManager().resolveContentProvider(authority(pkg), 0) != null) {
                String permission = pkg + ".READ_PROVIDER";
                return context.checkSelfPermission(permission) == PackageManager.PERMISSION_GRANTED
                    ? context.getString(R.string.status_granted, pkg)
                    : context.getString(R.string.status_required);
            }
        }
        return context.getString(R.string.status_not_found);
    }

    public static boolean isGranted(Context context) {
        return approvedPackage(context) != null;
    }

    private static String approvedPackage(Context context) {
        for (String pkg : PACKAGES) {
            if (context.getPackageManager().resolveContentProvider(authority(pkg), 0) != null &&
                context.checkSelfPermission(pkg + ".READ_PROVIDER") == PackageManager.PERMISSION_GRANTED) {
                return pkg;
            }
        }
        return null;
    }

    public static boolean refreshAndPublish(Context context) {
        String pkg = approvedPackage(context);
        if (pkg == null) {
            Log.w(TAG, status(context));
            return false;
        }
        try {
            Uri base = Uri.parse("content://" + authority(pkg));
            Uri versionUri = base.buildUpon().appendPath("version").build();
            try (Cursor cursor = context.getContentResolver().query(versionUri, null, null, null, null)) {
                if (cursor == null || !cursor.moveToFirst()) return false;
                int major = cursor.getInt(cursor.getColumnIndexOrThrow("major"));
                if (major != 0) {
                    Log.w(TAG, "Unsupported Breezy provider major version " + major);
                    return false;
                }
            }

            Uri locationsUri = base.buildUpon().appendPath("locations")
                .appendQueryParameter("limit", "1").build();
            String id;
            try (Cursor cursor = context.getContentResolver().query(locationsUri, null, null, null, null)) {
                if (cursor == null || !cursor.moveToFirst()) {
                    Log.w(TAG, "Breezy has no locations");
                    return false;
                }
                id = cursor.getString(cursor.getColumnIndexOrThrow("id"));
            }
            if (id == null || id.isEmpty()) return false;

            Uri weatherUri = base.buildUpon().appendPath("weather")
                .appendQueryParameter("temperatureUnit", "c")
                .appendQueryParameter("speedUnit", "kph")
                .appendQueryParameter("precipitationUnit", "mm")
                .appendQueryParameter("withDaily", "true")
                .appendQueryParameter("withHourly", "true")
                .appendQueryParameter("withMinutely", "false")
                .appendQueryParameter("withAlerts", "false")
                .appendQueryParameter("withNormals", "false")
                .build();
            try (Cursor cursor = context.getContentResolver().query(
                    weatherUri, null, "id=" + id, null, null)) {
                if (cursor == null || !cursor.moveToFirst()) return false;
                int weatherIndex = cursor.getColumnIndexOrThrow("weather");
                if (cursor.isNull(weatherIndex)) return false;
                byte[] gzipped = cursor.getBlob(weatherIndex);
                if (gzipped == null || gzipped.length == 0) return false;

                JSONObject weather = gunzipJson(gzipped);
                String location = getColumn(cursor, "custom_name");
                if (location.isEmpty()) location = getColumn(cursor, "city");
                String zone = getColumn(cursor, "timezone");
                JSONObject legacy = toLegacy(weather, location, zone);
                if (legacy == null) return false;

                String converted = legacy.toString();
                context.getSharedPreferences(KwgtPublisher.PREFS, Context.MODE_PRIVATE)
                    .edit().putString(KwgtPublisher.CACHE_KEY, converted)
                    .putLong(KwgtPublisher.CACHE_TIME_KEY, System.currentTimeMillis()).apply();
                return KwgtPublisher.publish(context, converted);
            }
        } catch (Exception e) {
            Log.e(TAG, "Provider read failed (permission, API, or data schema)", e);
            return false;
        }
    }

    private static String getColumn(Cursor cursor, String name) {
        int index = cursor.getColumnIndex(name);
        return index < 0 || cursor.isNull(index) ? "" : cursor.getString(index);
    }

    private static JSONObject gunzipJson(byte[] compressed) throws Exception {
        try (InputStream in = new GZIPInputStream(new java.io.ByteArrayInputStream(compressed));
             ByteArrayOutputStream out = new ByteArrayOutputStream()) {
            byte[] buf = new byte[8192];
            int n;
            int size = 0;
            while ((n = in.read(buf)) != -1) {
                size += n;
                if (size > 8 * 1024 * 1024) throw new IllegalArgumentException("Weather JSON too large");
                out.write(buf, 0, n);
            }
            return new JSONObject(out.toString("UTF-8"));
        }
    }

    private static JSONObject toLegacy(JSONObject weather, String location, String timezone) throws Exception {
        JSONObject current = weather.optJSONObject("current");
        JSONArray days = weather.optJSONArray("daily");
        if (current == null && (days == null || days.length() == 0)) return null;

        JSONObject result = new JSONObject();
        result.put("location", location);
        if (current != null) {
            putTemperature(result, "currentTemp", current.optJSONObject("temperature"), "temperature");
            JSONObject temps = current.optJSONObject("temperature");
            double apparent = value(temps == null ? null : temps.optJSONObject("sourceFeelsLike"));
            if (Double.isNaN(apparent)) apparent = value(temps == null ? null : temps.optJSONObject("computedApparent"));
            if (!Double.isNaN(apparent)) {
                String unit = unit(temps == null ? null : temps.optJSONObject("sourceFeelsLike"));
                if (unit.isEmpty()) unit = unit(temps == null ? null : temps.optJSONObject("computedApparent"));
                double kelvin = toKelvin(apparent, unit);
                if (!Double.isNaN(kelvin)) result.put("feelsLikeTemp", kelvin);
            }
            String description = current.optString("weatherText", "");
            if (!description.isEmpty()) result.put("currentCondition", description);
            String weatherCode = current.optString("weatherCode", "");
            int code = legacyCode(weatherCode);
            if (code != -1) {
                result.put("currentConditionCode", code);
                result.put("currentWeatherCode", weatherCode);
            }
            JSONObject humidity = current.optJSONObject("relativeHumidity");
            if (humidity != null && !Double.isNaN(value(humidity)))
                result.put("currentHumidity", Math.round(value(humidity)));
            JSONObject wind = current.optJSONObject("wind");
            if (wind != null) {
                JSONObject speed = wind.optJSONObject("speed");
                double kmh = toKmh(speed);
                if (!Double.isNaN(kmh)) result.put("windSpeed", kmh);
                double bearing = wind.optDouble("degree", Double.NaN);
                if (!Double.isNaN(bearing) && bearing >= 0) result.put("windDirection", Math.round(bearing));
            }
        }

        JSONArray daylight = daylight(weather.optJSONArray("hourly"));
        if (daylight != null) result.put("daylight", daylight);
        JSONArray precipitation = hourlyPrecipitation(weather.optJSONArray("hourly"));
        if (precipitation != null) result.put("precipitation", precipitation);

        TimeZone zone = TimeZone.getTimeZone(timezone.isEmpty() ? "UTC" : timezone);
        SimpleDateFormat fmt = new SimpleDateFormat("yyyy-MM-dd", Locale.US);
        fmt.setTimeZone(zone);
        String today = fmt.format(new Date());
        Calendar tomorrowDate = Calendar.getInstance(zone);
        tomorrowDate.add(Calendar.DAY_OF_MONTH, 1);
        String tomorrow = fmt.format(tomorrowDate.getTime());

        JSONObject todayDay = null;
        JSONObject tomorrowDay = null;
        if (days != null) {
            for (int i = 0; i < days.length(); i++) {
                JSONObject day = days.optJSONObject(i);
                if (day == null) continue;
                long date = day.optLong("date", -1);
                if (date < 0) continue;
                String label = fmt.format(new Date(date));
                if (today.equals(label)) todayDay = day;
                if (tomorrow.equals(label)) tomorrowDay = day;
            }
        }

        if (todayDay != null) {
            double high = dayTemperature(todayDay, "day");
            double low = dayTemperature(todayDay, "night");
            if (!Double.isNaN(high)) result.put("todayMaxTemp", high);
            if (!Double.isNaN(low)) result.put("todayMinTemp", low);
        }
        if (tomorrowDay != null) {
            JSONArray forecasts = new JSONArray();
            JSONObject entry = new JSONObject();
            double high = dayTemperature(tomorrowDay, "day");
            double low = dayTemperature(tomorrowDay, "night");
            if (!Double.isNaN(high)) entry.put("maxTemp", high);
            if (!Double.isNaN(low)) entry.put("minTemp", low);
            JSONObject halfDay = tomorrowDay.optJSONObject("day");
            if (halfDay == null) halfDay = tomorrowDay.optJSONObject("night");
            if (halfDay != null) {
                String weatherCode = halfDay.optString("weatherCode", "");
                int code = legacyCode(weatherCode);
                if (code >= 0) {
                    entry.put("conditionCode", code);
                    entry.put("weatherCode", weatherCode);
                }
                JSONObject chance = halfDay.optJSONObject("precipitationProbability");
                JSONObject total = chance == null ? null : chance.optJSONObject("total");
                if (total != null && !Double.isNaN(value(total))) {
                    entry.put("precipProbability", Math.round(value(total)));
                }
            }
            double mm = halfDayPrecipitation(tomorrowDay, "day", "total")
                + halfDayPrecipitation(tomorrowDay, "night", "total");
            if (!Double.isNaN(mm)) entry.put("precipMm", mm);
            entry.put("precipRain", halfDayPrecipitation(tomorrowDay, "day", "rain")
                + halfDayPrecipitation(tomorrowDay, "night", "rain")
                + halfDayPrecipitation(tomorrowDay, "day", "thunderstorm")
                + halfDayPrecipitation(tomorrowDay, "night", "thunderstorm"));
            entry.put("precipSnow", halfDayPrecipitation(tomorrowDay, "day", "snow")
                + halfDayPrecipitation(tomorrowDay, "night", "snow"));
            entry.put("precipIce", halfDayPrecipitation(tomorrowDay, "day", "ice")
                + halfDayPrecipitation(tomorrowDay, "night", "ice"));
            forecasts.put(entry);
            result.put("forecasts", forecasts);
        }
        return result;
    }

    /** [[hourStartMillis, 0|1], ...] from Breezy's hourly isDaylight, sorted by time. */
    private static JSONArray daylight(JSONArray hourly) {
        if (hourly == null) return null;
        java.util.List<long[]> hours = new java.util.ArrayList<>();
        for (int i = 0; i < hourly.length(); i++) {
            JSONObject hour = hourly.optJSONObject(i);
            if (hour == null || !hour.has("isDaylight") || hour.isNull("isDaylight")) continue;
            long date = hour.optLong("date", -1);
            if (date < 0) continue;
            hours.add(new long[]{date, hour.optBoolean("isDaylight", true) ? 1 : 0});
        }
        if (hours.isEmpty()) return null;
        hours.sort((a, b) -> Long.compare(a[0], b[0]));
        JSONArray result = new JSONArray();
        for (long[] hour : hours) {
            result.put(new JSONArray().put(hour[0]).put((int) hour[1]));
        }
        return result;
    }

    /**
     * [[hourStartMillis, totalMm, rainMm, snowMm, iceMm], ...] from Breezy's hourly precipitation,
     * sorted by time. Rain includes thunderstorm; snow is in mm of water. Kinds Breezy's source
     * does not split are 0.
     */
    private static JSONArray hourlyPrecipitation(JSONArray hourly) throws org.json.JSONException {
        if (hourly == null) return null;
        java.util.List<double[]> hours = new java.util.ArrayList<>();
        for (int i = 0; i < hourly.length(); i++) {
            JSONObject hour = hourly.optJSONObject(i);
            JSONObject precipitation = hour == null ? null : hour.optJSONObject("precipitation");
            JSONObject total = precipitation == null ? null : precipitation.optJSONObject("total");
            double mm = value(total);
            long date = hour == null ? -1 : hour.optLong("date", -1);
            if (Double.isNaN(mm) || date < 0 || !"mm".equals(unit(total))) continue;
            hours.add(new double[]{date, mm,
                millimeters(precipitation, "rain") + millimeters(precipitation, "thunderstorm"),
                millimeters(precipitation, "snow"), millimeters(precipitation, "ice")});
        }
        if (hours.isEmpty()) return null;
        hours.sort((a, b) -> Double.compare(a[0], b[0]));
        JSONArray result = new JSONArray();
        for (double[] hour : hours) {
            result.put(new JSONArray().put((long) hour[0]).put(hour[1]).put(hour[2])
                .put(hour[3]).put(hour[4]));
        }
        return result;
    }

    /** One kind of a half day's precipitation in mm ("total", "rain", "snow", ...); 0 when absent. */
    private static double halfDayPrecipitation(JSONObject daily, String part, String kind) {
        JSONObject half = daily.optJSONObject(part);
        return millimeters(half == null ? null : half.optJSONObject("precipitation"), kind);
    }

    /** precipitation.<kind> in mm; 0 when absent or in another unit. */
    private static double millimeters(JSONObject precipitation, String kind) {
        JSONObject measurement = precipitation == null ? null : precipitation.optJSONObject(kind);
        double mm = value(measurement);
        return Double.isNaN(mm) || !"mm".equals(unit(measurement)) ? 0 : mm;
    }

    private static double dayTemperature(JSONObject daily, String part) {
        JSONObject half = daily.optJSONObject(part);
        JSONObject temp = half == null ? null : half.optJSONObject("temperature");
        JSONObject measurement = temp == null ? null : temp.optJSONObject("temperature");
        return toKelvin(value(measurement), unit(measurement));
    }

    private static void putTemperature(JSONObject target, String key,
                                       JSONObject container, String child) throws Exception {
        JSONObject source = container == null ? null : container.optJSONObject(child);
        double kelvin = toKelvin(value(source), unit(source));
        if (!Double.isNaN(kelvin)) target.put(key, kelvin);
    }

    private static double value(JSONObject measurement) {
        return measurement == null ? Double.NaN : measurement.optDouble("value", Double.NaN);
    }

    private static String unit(JSONObject measurement) {
        return measurement == null ? "" : measurement.optString("unit", "").toLowerCase(Locale.ROOT);
    }

    private static double toKelvin(double number, String unit) {
        if (Double.isNaN(number)) return Double.NaN;
        switch (unit) {
            case "c": return number + 273.15;
            case "f": return (number - 32) / 1.8 + 273.15;
            case "k": return number;
            default: return Double.NaN;
        }
    }

    private static double toKmh(JSONObject speed) {
        double n = value(speed);
        if (Double.isNaN(n)) return Double.NaN;
        switch (unit(speed)) {
            case "kph": return n;
            case "mps": return n * 3.6;
            case "mph": return n * 1.609344;
            case "kn": return n * 1.852;
            case "ftps": return n * 1.09728;
            default: return Double.NaN;
        }
    }

    /** Map Breezy's canonical condition IDs to the existing OpenWeather-like icon contract. */
    private static int legacyCode(String code) {
        switch (code) {
            case "clear": return 800;
            case "partly_cloudy": return 801;
            case "cloudy": return 804;
            case "rain": return 500;
            case "snow": return 601;
            case "wind": return 771;
            case "fog": return 741;
            case "haze": return 721;
            case "sleet": return 611;
            case "hail": return 602;
            case "thunder": return 211;
            case "thunderstorm": return 201;
            default: return -1;
        }
    }
}
