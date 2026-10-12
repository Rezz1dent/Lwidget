package com.leanbitlab.breezybridge;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.util.Log;
import org.json.JSONArray;
import org.json.JSONObject;

import java.util.LinkedHashMap;
import java.util.Locale;
import java.util.Map;

/**
 * Tiny, permission-free Breezy Gadgetbridge -> KWGT bridge.
 * Breezy serializes temperatures in Kelvin, wind speed in km/h,
 * and "forecasts"[0] is tomorrow (today is omitted by Breezy).
 */
public final class WeatherReceiver extends BroadcastReceiver {
    public static final String ACTION_BREEZY =
        "nodomain.freeyourgadget.gadgetbridge.ACTION_GENERIC_WEATHER";
    public static final String EXT = "breezy";
    private static final String TAG = "BreezyKwgt";
    private static final String PREFS = "breezy_bridge";
    private static final String[] KEYS = {
        "temp", "feels", "condition", "code", "icon",
        "humidity", "precip", "wind", "wind_kmh", "wind_ms",
        "wind_direction", "wind_degrees", "wind_text", "location",
        "tomorrow_max", "tomorrow_min", "tomorrow_range", "tomorrow",
        "tomorrow_precip", "tomorrow_icon"
    };

    @Override public void onReceive(Context context, Intent intent) {
        if (!ACTION_BREEZY.equals(intent.getAction())) return;
        String json = intent.getStringExtra("WeatherJson");
        if (json == null || json.isEmpty()) {
            Log.w(TAG, "Received weather broadcast without WeatherJson");
            return;
        }
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .edit().putString("last_json", json).apply();
        publish(context, json);
    }

    public static boolean resendCached(Context context) {
        String json = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .getString("last_json", null);
        return json != null && publish(context, json);
    }

    public static boolean publish(Context context, String json) {
        try {
            Map<String, String> vars = variables(new JSONObject(json));
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
    static Map<String, String> variables(JSONObject data) {
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
        if (has(data, "currentCondition"))
            vars.put("condition", data.optString("currentCondition").trim());
        if (has(data, "currentConditionCode")) {
            int code = data.optInt("currentConditionCode");
            vars.put("code", Integer.toString(code));
            vars.put("icon", weatherIcon(code));
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
        }
        if (!vars.get("wind_ms").isEmpty()) {
            vars.put("wind_text",
                (vars.get("wind_direction").isEmpty() ? "" : vars.get("wind_direction") + " · ") +
                    vars.get("wind_ms"));
        }
        if (has(data, "location"))
            vars.put("location", data.optString("location"));

        // Breezy's Gadgetbridge getDailyForecasts(...) explicitly skips today.
        // The first element is TOMORROW, and max/min are supplied in Kelvin.
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
                if (has(tomorrow, "conditionCode"))
                    vars.put("tomorrow_icon", weatherIcon(tomorrow.optInt("conditionCode")));
            }
        }
        return vars;
    }

    private static boolean has(JSONObject data, String key) {
        return data.has(key) && !data.isNull(key);
    }

    private static String degreesC(double kelvin) {
        long celsius = Math.round(kelvin - 273.15);
        return (celsius > 0 ? "+" : "") + celsius + "°C";
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

    private static String weatherIcon(int code) {
        if (code == 800) return "☀️";
        if (code == 801) return "🌤️";
        if (code == 802) return "⛅";
        if (code == 803 || code == 804) return "☁️";
        if (code >= 200 && code <= 232) return "⛈️";
        if (code >= 300 && code <= 531) return "🌧️";
        if (code >= 600 && code <= 622) return "🌨️";
        if (code == 741 || code == 751) return "🌫️";
        if (code == 771) return "💨";
        return "☁️";
    }
}
