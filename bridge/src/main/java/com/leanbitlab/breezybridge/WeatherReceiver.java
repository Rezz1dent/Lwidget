package com.leanbitlab.breezybridge;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.util.Log;
import org.json.JSONObject;
import java.util.LinkedHashMap;
import java.util.Locale;
import java.util.Map;

/** Minimal Breezy Gadgetbridge to KWGT translator. Zero internet/location permissions. */
public final class WeatherReceiver extends BroadcastReceiver {
    public static final String ACTION_BREEZY =
        "nodomain.freeyourgadget.gadgetbridge.ACTION_GENERIC_WEATHER";
    public static final String EXT = "breezy";
    private static final String TAG = "BreezyKwgt";
    private static final String PREFS = "breezy_bridge";

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
            JSONObject data = new JSONObject(json);
            Map<String, String> vars = new LinkedHashMap<>();
            if (has(data, "currentTemp")) {
                vars.put("temp", degrees(data.getDouble("currentTemp")) + "°C");
            }
            if (has(data, "feelsLikeTemp")) {
                vars.put("feels", "Feels like " + degrees(data.getDouble("feelsLikeTemp")) + "°C");
            }
            if (has(data, "currentCondition")) {
                vars.put("condition", data.getString("currentCondition").trim());
            }
            if (has(data, "currentConditionCode")) {
                int code = data.getInt("currentConditionCode");
                vars.put("code", String.valueOf(code));
                vars.put("icon", weatherIcon(code));
            }
            if (has(data, "currentHumidity"))
                vars.put("humidity", data.getString("currentHumidity") + "%");
            if (has(data, "precipProbability"))
                vars.put("precip", data.getString("precipProbability") + "%");
            if (has(data, "windSpeed"))
                vars.put("wind", String.format(Locale.US, "%.0f km/h", data.getDouble("windSpeed")));
            if (has(data, "location"))
                vars.put("location", data.getString("location"));
            if (vars.isEmpty()) return false;
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

    private static boolean has(JSONObject data, String name) {
        return data.has(name) && !data.isNull(name);
    }
    private static String degrees(double kelvin) {
        int value = (int) Math.round(kelvin - 273.15);
        return (value > 0 ? "+" : "") + value;
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
