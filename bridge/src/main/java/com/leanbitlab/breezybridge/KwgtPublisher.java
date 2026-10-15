package com.leanbitlab.breezybridge;

import android.content.Context;
import android.content.Intent;
import android.util.Log;
import org.json.JSONArray;
import org.json.JSONObject;

import java.util.LinkedHashMap;
import java.util.Locale;
import java.util.Map;

/**
 * Converts the cached weather snapshot into KWGT variables and sends them to KWGT.
 * The snapshot uses the legacy Gadgetbridge layout produced by ProviderBridge:
 * temperatures in Kelvin, wind speed in km/h, "forecasts"[0] is tomorrow.
 */
public final class KwgtPublisher {
    public static final String EXT = "breezy";
    private static final String TAG = "BreezyKwgt";
    static final String PREFS = "breezy_bridge";
    static final String CACHE_KEY = "last_json";
    static final String CACHE_TIME_KEY = "last_time";
    static final String[] KEYS = {
        "temp", "feels", "condition", "code", "icon",
        "humidity", "precip", "wind", "wind_kmh", "wind_ms",
        "wind_direction", "wind_degrees", "wind_text", "location",
        "tomorrow_max", "tomorrow_min", "tomorrow_range", "tomorrow",
        "tomorrow_precip", "tomorrow_precip_mm", "tomorrow_icon",
        "like", "details", "wind_arrow", "today_max", "today_min",
        "today_range", "today_compact", "tomorrow_compact",
        "icon_flat", "tomorrow_icon_flat", "is_day", "precip_now",
        "icon_mdi", "tomorrow_icon_mdi"
    };

    private KwgtPublisher() {}

    /** Re-sends the cached snapshot, e.g. when day turns into night. */
    public static boolean resendCached(Context context) {
        String json = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .getString(CACHE_KEY, null);
        return json != null && publish(context, json);
    }

    public static boolean publish(Context context, String json) {
        try {
            JSONObject data = new JSONObject(json);
            long now = System.currentTimeMillis();
            Map<String, String> vars = variables(data, now);
            if (vars == null) return false;

            Intent kwgt = new Intent("org.kustom.action.SEND_VAR");
            kwgt.setPackage("org.kustom.widget");
            kwgt.putExtra("org.kustom.action.EXT_NAME", EXT);
            kwgt.putExtra("org.kustom.action.VAR_NAME_ARRAY",
                vars.keySet().toArray(new String[0]));
            kwgt.putExtra("org.kustom.action.VAR_VALUE_ARRAY",
                vars.values().toArray(new String[0]));
            context.sendBroadcast(kwgt);
            Log.i(TAG, "Sent " + vars.size() + " Breezy variables to KWGT");
            DaylightScheduler.scheduleNextSwitch(context, data, now);
            return true;
        } catch (Exception e) {
            Log.e(TAG, "Unable to forward Breezy weather", e);
            return false;
        }
    }

    /**
     * Always send empty values for missing optional fields. Otherwise KWGT
     * may keep yesterday's values when a provider temporarily omits a forecast.
     */
    static Map<String, String> variables(JSONObject data, long nowMillis) {
        if (data == null ||
            (!has(data, "currentTemp") && !has(data, "currentCondition") &&
             !has(data, "forecasts"))) {
            return null;
        }

        Map<String, String> vars = new LinkedHashMap<>();
        for (String key : KEYS) vars.put(key, "");

        if (has(data, "currentTemp"))
            vars.put("temp", degreesC(data.optDouble("currentTemp")));
        if (has(data, "feelsLikeTemp"))
            vars.put("feels", "Feels like " + degreesC(data.optDouble("feelsLikeTemp")));
        if (has(data, "feelsLikeTemp"))
            vars.put("like", degreesC(data.optDouble("feelsLikeTemp")));
        if (has(data, "currentCondition"))
            vars.put("condition", data.optString("currentCondition").trim());
        boolean day = isDaylight(data, nowMillis);
        vars.put("is_day", day ? "1" : "0");
        vars.put("precip_now", precipitationNow(data, nowMillis));
        if (has(data, "currentConditionCode")) {
            int code = data.optInt("currentConditionCode");
            vars.put("code", Integer.toString(code));
            vars.put("icon", weatherIcon(code, day));
            vars.put("icon_flat", weatherFlatIcon(code, day));
            vars.put("icon_mdi", mdiIcon(data.optString("currentWeatherCode", ""), code, day));
        }
        if (has(data, "currentHumidity"))
            vars.put("humidity", data.optString("currentHumidity") + "%");
        if (has(data, "precipProbability"))
            vars.put("precip", data.optString("precipProbability") + "%");

        if (has(data, "windSpeed")) {
            double kmh = data.optDouble("windSpeed");
            vars.put("wind", String.format(Locale.US, "%.0f km/h", kmh));
            vars.put("wind_kmh", String.format(Locale.forLanguageTag("ru-RU"), "%.0f км/ч", kmh));
            vars.put("wind_ms", speedMs(kmh));
        }
        if (has(data, "windDirection")) {
            int degrees = data.optInt("windDirection");
            vars.put("wind_direction", compass(degrees));
            vars.put("wind_degrees", normalizeDegrees(degrees) + "°");
            vars.put("wind_arrow", windFlowArrow(degrees));
        }
        if (!vars.get("wind_ms").isEmpty()) {
            vars.put("wind_text",
                (vars.get("wind_direction").isEmpty() ? "" : vars.get("wind_direction") + " · ") +
                    vars.get("wind_ms"));
        }
        StringBuilder details = new StringBuilder();
        if (!vars.get("like").isEmpty())
            details.append("Like ").append(vars.get("like"));
        if (!vars.get("wind_ms").isEmpty()) {
            if (details.length() > 0) details.append("  ");
            details.append(vars.get("wind_arrow")).append(vars.get("wind_arrow").isEmpty() ? "" : " ");
            details.append(vars.get("wind_ms").replace(" м/с", "м/с"));
        }
        if (!vars.get("humidity").isEmpty()) {
            if (details.length() > 0) details.append("  ");
            details.append("💧").append(vars.get("humidity"));
        }
        vars.put("details", details.toString());

        if (has(data, "todayMaxTemp"))
            vars.put("today_max", degreesC(data.optDouble("todayMaxTemp")));
        if (has(data, "todayMinTemp"))
            vars.put("today_min", degreesC(data.optDouble("todayMinTemp")));
        String todayRange = shortRange(data, "todayMaxTemp", "todayMinTemp");
        if (!todayRange.isEmpty()) {
            vars.put("today_range", todayRange);
            vars.put("today_compact", "Today: " + todayRange);
        }

        if (has(data, "location"))
            vars.put("location", data.optString("location"));

        // ProviderBridge stores only tomorrow here; max/min are in Kelvin.
        JSONArray forecasts = data.optJSONArray("forecasts");
        if (forecasts != null && forecasts.length() > 0) {
            JSONObject tomorrow = forecasts.optJSONObject(0);
            if (tomorrow != null) {
                String maximum = has(tomorrow, "maxTemp") ?
                    degreesC(tomorrow.optDouble("maxTemp")) : "";
                String minimum = has(tomorrow, "minTemp") ?
                    degreesC(tomorrow.optDouble("minTemp")) : "";
                vars.put("tomorrow_max", maximum);
                vars.put("tomorrow_min", minimum);
                if (!maximum.isEmpty() || !minimum.isEmpty()) {
                    String range = maximum.isEmpty() ? "↓" + minimum :
                        minimum.isEmpty() ? "↑" + maximum :
                            "↑" + maximum + "  ↓" + minimum;
                    vars.put("tomorrow_range", range);
                    vars.put("tomorrow", "Завтра " + range);
                }
                if (has(tomorrow, "precipProbability"))
                    vars.put("tomorrow_precip", tomorrow.optString("precipProbability") + "%");
                vars.put("tomorrow_precip_mm", millimeters(tomorrow.optDouble("precipMm", Double.NaN)));
                String compactRange = shortRange(tomorrow, "maxTemp", "minTemp");
                if (!compactRange.isEmpty())
                    vars.put("tomorrow_compact", "Tomorrow: " + compactRange);
                if (has(tomorrow, "conditionCode")) {
                    vars.put("tomorrow_icon", weatherIcon(tomorrow.optInt("conditionCode"), true));
                    vars.put("tomorrow_icon_flat", weatherFlatIcon(tomorrow.optInt("conditionCode"), true));
                    vars.put("tomorrow_icon_mdi", mdiIcon(tomorrow.optString("weatherCode", ""),
                        tomorrow.optInt("conditionCode"), true));
                }
            }
        }
        return vars;
    }

    private static boolean has(JSONObject data, String key) {
        return data.has(key) && !data.isNull(key);
    }

    private static String degreesC(double kelvin) {
        long celsius = Math.round(kelvin - 273.15);
        return celsius + "°";
    }

    private static String speedMs(double kmh) {
        return String.format(Locale.forLanguageTag("ru-RU"), "%.1f м/с", kmh / 3.6);
    }

    private static int normalizeDegrees(int degrees) {
        return Math.floorMod(degrees, 360);
    }

    // Meteorological bearing: direction from which wind blows.
    private static String compass(int degrees) {
        String[] directions = {"С", "СВ", "В", "ЮВ", "Ю", "ЮЗ", "З", "СЗ"};
        return directions[((normalizeDegrees(degrees) + 22) / 45) % 8];
    }

    /**
     * Only generate ranges from actually present values. The compact format
     * saves precious space in KWGT: 8/2° or -2/-6°, no leading plus signs.
     */
    private static String shortRange(JSONObject obj, String highKey, String lowKey) {
        if (!has(obj, highKey) && !has(obj, lowKey)) return "";
        String hi = has(obj, highKey) ?
            Long.toString(Math.round(obj.optDouble(highKey) - 273.15)) : "—";
        String lo = has(obj, lowKey) ?
            Long.toString(Math.round(obj.optDouble(lowKey) - 273.15)) : "—";
        return hi + "/" + lo + "°";
    }

    /** Meteorological bearings indicate the direction FROM which wind comes.
     * The arrow instead points where the air actually BLOWS (downwind).
     */
    private static String windFlowArrow(int bearing) {
        String[] arrows = {"↑", "↗", "→", "↘", "↓", "↙", "←", "↖"};
        int downwindBearing = normalizeDegrees(bearing + 180);
        return arrows[((downwindBearing + 22) / 45) % 8];
    }

    /**
     * Breezy's hourly "isDaylight" flags, stored by ProviderBridge as
     * "daylight": [[hourStartMillis, 0|1], ...] sorted by time.
     * Without data (old cache, provider without hourly) it is treated as day.
     */
    /**
     * Precipitation of the current hour from Breezy's hourly forecast, e.g. "0,6" (mm, one
     * decimal, Russian format like the wind); "" when it is dry (< 0.1 mm) or unknown.
     */
    static String precipitationNow(JSONObject data, long nowMillis) {
        JSONArray hours = data.optJSONArray("precipitation");
        if (hours == null) return "";
        double mm = Double.NaN;
        for (int i = 0; i < hours.length(); i++) {
            JSONArray hour = hours.optJSONArray(i);
            if (hour == null) continue;
            long start = hour.optLong(0, Long.MAX_VALUE);
            if (start > nowMillis) break;
            mm = nowMillis - start < 3_600_000L ? hour.optDouble(1, Double.NaN) : Double.NaN;
        }
        return millimeters(mm);
    }

    /** "4,2" (one decimal, Russian format); "" when dry (< 0.05 mm) or unknown. */
    static String millimeters(double mm) {
        if (Double.isNaN(mm) || mm < 0.05) return "";
        return String.format(Locale.forLanguageTag("ru-RU"), "%.1f", mm);
    }

    static boolean isDaylight(JSONObject data, long nowMillis) {
        JSONArray hours = data.optJSONArray("daylight");
        if (hours == null) return true;
        Boolean state = null;
        for (int i = 0; i < hours.length(); i++) {
            JSONArray hour = hours.optJSONArray(i);
            if (hour == null) continue;
            if (hour.optLong(0, Long.MAX_VALUE) > nowMillis) break;
            state = hour.optInt(1, 1) == 1;
        }
        return state == null || state;
    }

    /** Start of the next hour whose daylight flag differs from now, or -1. */
    static long nextDaylightSwitch(JSONObject data, long nowMillis) {
        JSONArray hours = data.optJSONArray("daylight");
        if (hours == null) return -1;
        boolean current = isDaylight(data, nowMillis);
        for (int i = 0; i < hours.length(); i++) {
            JSONArray hour = hours.optJSONArray(i);
            if (hour == null) continue;
            long start = hour.optLong(0, -1);
            if (start > nowMillis && (hour.optInt(1, 1) == 1) != current) return start;
        }
        return -1;
    }

    /**
     * Glyph names from the Meteo icon font bundled with the preset (meteo.json).
     * Night: clear -> moon2, partly cloudy -> cloud4 (moon behind a cloud);
     * the other conditions have no day/night variants in the font.
     * Note: cloud3 in this font is a thundercloud, so it is not used for clouds.
     */
    static String weatherFlatIcon(int code, boolean day) {
        if (code == 800) return day ? "sun3" : "moon2";
        if (code == 801 || code == 802) return day ? "cloudy3" : "cloud4";
        if (code == 803 || code == 804) return "cloud5";
        if (code >= 200 && code <= 232) return "lightning5";
        if (code >= 300 && code <= 321) return "rainy3";
        if (code >= 500 && code <= 531) return "rainy4";
        if (code >= 600 && code <= 622) return "snowy4";
        if (code >= 701 && code <= 781) return code == 771 ? "windy" : "fog";
        return "cloud5";
    }

    static String weatherIcon(int code, boolean day) {
        if (code == 800) return day ? "☀️" : "🌙";
        if (code == 801) return day ? "🌤️" : "☁️";
        if (code == 802) return day ? "⛅" : "☁️";
        if (code == 803 || code == 804) return "☁️";
        if (code >= 200 && code <= 232) return "⛈️";
        if (code >= 300 && code <= 531) return "🌧️";
        if (code >= 600 && code <= 622) return "🌨️";
        if (code >= 701 && code <= 781) return code == 771 ? "💨" : "🌫️";
        return "☁️";
    }

    /**
     * Material Design Icons name, as in Breezy Weather's own widgets
     * (KWGT icon set: Iconify, "mdi"). Breezy's condition ID is preferred;
     * caches written before 1.3 only have the legacy code.
     */
    static String mdiIcon(String breezyCode, int legacyCode, boolean day) {
        String condition = breezyCode.isEmpty() ? breezyCondition(legacyCode) : breezyCode;
        switch (condition) {
            case "clear": return day ? "weather-sunny" : "weather-night";
            case "partly_cloudy": return day ? "weather-partly-cloudy" : "weather-night-partly-cloudy";
            case "rain": return "weather-pouring";
            case "snow": return "weather-snowy";
            case "sleet": return "weather-snowy-rainy";
            case "hail": return "weather-hail";
            case "thunder": return "weather-lightning";
            case "thunderstorm": return "weather-lightning-rainy";
            case "fog": return "weather-fog";
            case "haze": return "blur";
            case "wind": return "weather-windy";
            default: return "weather-cloudy";
        }
    }

    private static String breezyCondition(int code) {
        if (code == 800) return "clear";
        if (code == 801 || code == 802) return "partly_cloudy";
        if (code >= 200 && code <= 232) return code == 201 ? "thunderstorm" : "thunder";
        if (code >= 300 && code <= 531) return "rain";
        if (code == 602) return "hail";
        if (code == 611) return "sleet";
        if (code >= 600 && code <= 622) return "snow";
        if (code == 721) return "haze";
        if (code == 771) return "wind";
        if (code >= 701 && code <= 781) return "fog";
        return "cloudy";
    }
}
