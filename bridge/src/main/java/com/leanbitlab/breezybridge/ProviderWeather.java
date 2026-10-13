package com.leanbitlab.breezybridge;

import android.content.Context;
import android.content.pm.PackageManager;
import android.database.Cursor;
import android.net.Uri;
import android.util.Log;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.nio.charset.StandardCharsets;
import java.util.Calendar;
import java.util.TimeZone;
import java.util.zip.GZIPInputStream;

/**
 * Standalone, permission-gated Breezy ContentProvider -> legacy KWGT bridge adapter.
 *
 * Uses the public v0.x provider protocol documented in:
 * https://github.com/breezy-weather/breezy-weather-data-sharing-lib
 *
 * No library code/assets are bundled. The API is experimental: fail explicitly
 * on an incompatible major provider version and never substitute fake weather.
 *
 * Rather than duplicate the 30 output variables, translate Breezy's official
 * unit-aware, GZIP-compressed JSON to the existing validated Gadgetbridge-shaped
 * JSON. WeatherReceiver publishes the exact same br(breezy, ...) keys as v10.
 */
public final class ProviderWeather {
    private static final String TAG = "BreezyProviderBridge";
    private static final String[] PACKAGES = {
        "org.breezyweather", "org.breezyweather.debug"
    };
    private static final long LIMIT_BYTES = 2_000_000L;

    private ProviderWeather() {}

    public static String detectedPackage(Context context) {
        for (String name : PACKAGES) {
            try {
                if (context.getPackageManager().getApplicationInfo(name, 0).enabled)
                    return name;
            } catch (PackageManager.NameNotFoundException ignored) {}
        }
        return null;
    }

    public static String requiredPermission(Context context) {
        String name = detectedPackage(context);
        return name == null ? null : name + ".READ_PROVIDER";
    }

    public static boolean hasPermission(Context context) {
        String permission = requiredPermission(context);
        return permission != null
            && context.checkSelfPermission(permission) == PackageManager.PERMISSION_GRANTED;
    }

    public static String refresh(Context context) {
        final String name = detectedPackage(context);
        if (name == null) return status(context, "Breezy Weather не найден");
        if (!hasPermission(context)) {
            return status(context, "Нет разрешения на чтение погоды Breezy");
        }
        final String prefix = "content://" + name + ".provider.weather/";
        try {
            // Provider version: major 0 is the only currently supported protocol.
            try (Cursor cursor = context.getContentResolver().query(
                    Uri.parse(prefix + "version"), null, null, null, null)) {
                if (cursor == null || !cursor.moveToFirst())
                    return status(context, "ContentProvider Breezy недоступен");
                int major = cursor.getInt(cursor.getColumnIndexOrThrow("major"));
                int minor = cursor.getInt(cursor.getColumnIndexOrThrow("minor"));
                if (major != 0)
                    return status(context, "Неподдерживаемая версия Breezy API: " + major + "." + minor);
            }

            String locationId;
            try (Cursor locations = context.getContentResolver().query(
                    Uri.parse(prefix + "locations?limit=1"), null, null, null, null)) {
                if (locations == null || !locations.moveToFirst())
                    return status(context, "В Breezy нет сохранённых мест");
                locationId = locations.getString(locations.getColumnIndexOrThrow("id"));
            }

            Uri uri = Uri.parse(prefix + "weather").buildUpon()
                .appendQueryParameter("withDaily", "true")
                .appendQueryParameter("withHourly", "false")
                .appendQueryParameter("withMinutely", "false")
                .appendQueryParameter("withAlerts", "false")
                .appendQueryParameter("withNormals", "false")
                .appendQueryParameter("temperatureUnit", "c")
                .appendQueryParameter("speedUnit", "kph")
                .build();

            try (Cursor weather = context.getContentResolver().query(
                    uri, null, "id=" + locationId, null, null)) {
                if (weather == null || !weather.moveToFirst())
                    return status(context, "Нет погодных данных для первого города");
                String city = stringColumn(weather, "custom_name");
                if (city.isEmpty()) city = stringColumn(weather, "city");
                String zone = stringColumn(weather, "timezone");
                byte[] packed = weather.getBlob(weather.getColumnIndexOrThrow("weather"));
                if (packed == null || packed.length == 0)
                    return status(context, "Погода не загружена в Breezy");
                JSONObject official = new JSONObject(unzip(packed));
                JSONObject legacy = adapt(official, city, zone);
                if (!WeatherReceiver.publish(context, legacy.toString()))
                    return status(context, "Ошибка передачи переменных в KWGT");
                String msg = "Обновлено из Breezy ContentProvider: " + city;
                Log.i(TAG, msg);
                return status(context, msg);
            }
        } catch (SecurityException e) {
            Log.e(TAG, "Permission denied", e);
            return status(context, "Нет доступа к Breezy: проверь разрешение");
        } catch (Exception e) {
            Log.e(TAG, "Content provider read failed", e);
            return status(context, "Ошибка API Breezy: " + e.getClass().getSimpleName()
                + (e.getMessage() == null ? "" : " (" + e.getMessage() + ")"));
        }
    }

    private static String status(Context ctx, String msg) {
        ctx.getSharedPreferences("provider_bridge", Context.MODE_PRIVATE)
            .edit().putString("last_status", msg).apply();
        return msg;
    }

    private static String stringColumn(Cursor cursor, String name) {
        int i = cursor.getColumnIndex(name);
        return i < 0 || cursor.isNull(i) ? "" : cursor.getString(i);
    }

    private static String unzip(byte[] packed) throws Exception {
        if (packed.length > LIMIT_BYTES) throw new Exception("Weather payload too large");
        try (GZIPInputStream gz = new GZIPInputStream(new ByteArrayInputStream(packed));
             ByteArrayOutputStream out = new ByteArrayOutputStream()) {
            byte[] buffer = new byte[8192];
            int n;
            while ((n = gz.read(buffer)) != -1) {
                if (out.size() + n > LIMIT_BYTES)
                    throw new Exception("Uncompressed payload too large");
                out.write(buffer, 0, n);
            }
            return out.toString(StandardCharsets.UTF_8.name());
        }
    }

    /** Published for contract test fixtures; provider weather values use C and kph. */
    static JSONObject adapt(JSONObject official, String city, String timezone) throws Exception {
        JSONObject out = new JSONObject();
        if (!city.isEmpty()) out.put("location", city);
        JSONObject current = official.optJSONObject("current");
        if (current != null) {
            JSONObject temperature = current.optJSONObject("temperature");
            Double currentC = tempC(temperature, "temperature");
            Double feelsC = tempC(temperature, "sourceFeelsLike");
            if (feelsC == null) feelsC = tempC(temperature, "computedApparent");
            if (currentC != null) out.put("currentTemp", currentC + 273.15d);
            if (feelsC != null) out.put("feelsLikeTemp", feelsC + 273.15d);
            String text = current.optString("weatherText", "");
            if (!text.isEmpty()) out.put("currentCondition", text);
            out.put("currentConditionCode", openWeatherCode(current.optString("weatherCode", "")));

            JSONObject humidity = current.optJSONObject("relativeHumidity");
            Double h = unit(humidity);
            if (h != null && (humidity.optString("unit", "%").equals("%")
                || humidity.optString("unit", "percent").equals("percent")))
                out.put("currentHumidity", Math.round(h));

            JSONObject wind = current.optJSONObject("wind");
            if (wind != null) {
                // speedUnit=kph is explicitly requested from Breezy.
                JSONObject speed = wind.optJSONObject("speed");
                Double kmh = unit(speed);
                if (kmh != null && (speed.optString("unit", "kph").equalsIgnoreCase("kph")
                        || speed.optString("unit", "km/h").equalsIgnoreCase("km/h")))
                    out.put("windSpeed", kmh);
                double degree = wind.optDouble("degree", -1);
                if (degree >= 0 && Double.isFinite(degree))
                    out.put("windDirection", Math.round(degree));
            }
        }

        JSONArray forecasts = new JSONArray();
        JSONArray daily = official.optJSONArray("daily");
        if (daily != null) {
            TimeZone zone = TimeZone.getTimeZone(timezone.isEmpty() ? TimeZone.getDefault().getID() : timezone);
            long now = System.currentTimeMillis();
            int today = dayIndex(now, zone);
            int tomorrow = dayIndex(now + 86_400_000L, zone);
            for (int i = 0; i < daily.length(); i++) {
                JSONObject day = daily.optJSONObject(i);
                if (day == null) continue;
                long timestamp = day.optLong("date", 0);
                if (timestamp < 1_000_000_000_000L && timestamp > 0) timestamp *= 1000L;
                int dateId = dayIndex(timestamp, zone);
                if (dateId == today) {
                    Double hi = dayC(day, "day");
                    Double lo = dayC(day, "night");
                    if (hi != null) out.put("todayMaxTemp", hi + 273.15d);
                    if (lo != null) out.put("todayMinTemp", lo + 273.15d);
                }
                if (dateId == tomorrow) {
                    JSONObject forecast = new JSONObject();
                    Double hi = dayC(day, "day");
                    Double lo = dayC(day, "night");
                    if (hi != null) forecast.put("maxTemp", hi + 273.15d);
                    if (lo != null) forecast.put("minTemp", lo + 273.15d);
                    JSONObject half = day.optJSONObject("day");
                    if (half == null) half = day.optJSONObject("night");
                    if (half != null) {
                        forecast.put("conditionCode", openWeatherCode(half.optString("weatherCode", "")));
                        JSONObject probability = half.optJSONObject("precipitationProbability");
                        Double p = probability == null ? null : unit(probability.optJSONObject("total"));
                        if (p != null) forecast.put("precipProbability", Math.round(p));
                    }
                    forecasts.put(forecast);
                }
            }
        }
        if (forecasts.length() > 0) out.put("forecasts", forecasts);
        return out;
    }

    private static Double unit(JSONObject u) {
        if (u == null || u.isNull("value")) return null;
        double n = u.optDouble("value", Double.NaN);
        return Double.isFinite(n) ? n : null;
    }

    private static Double tempC(JSONObject temp, String key) {
        if (temp == null) return null;
        JSONObject u = temp.optJSONObject(key);
        if (u == null || !u.optString("unit", "").equalsIgnoreCase("c")) return null;
        return unit(u);
    }

    private static Double dayC(JSONObject day, String half) {
        JSONObject item = day.optJSONObject(half);
        return tempC(item == null ? null : item.optJSONObject("temperature"), "temperature");
    }

    private static int dayIndex(long millis, TimeZone zone) {
        Calendar c = Calendar.getInstance(zone);
        c.setTimeInMillis(millis);
        return c.get(Calendar.YEAR) * 1000 + c.get(Calendar.DAY_OF_YEAR);
    }

    private static int openWeatherCode(String str) {
        switch (str.toLowerCase(java.util.Locale.ROOT)) {
            case "clear": return 800;
            case "partly_cloudy": return 801;
            case "cloudy": return 804;
            case "rain": return 501;
            case "snow": return 601;
            case "wind": return 771;
            case "fog": return 741;
            case "haze": return 721;
            case "sleet": return 611;
            case "hail": return 616;
            case "thunder": case "thunderstorm": return 211;
            default: return 804;
        }
    }
}
