package com.leanbitlab.breezybridge;

import android.app.AlarmManager;
import android.app.PendingIntent;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.util.Log;
import org.json.JSONObject;

/**
 * Re-sends the cached weather at the next sunrise/sunset, so the day/night
 * icon switches even if Breezy does not refresh around that time.
 * Inexact but allowed while idle: no exact-alarm permission, a few minutes of delay is fine.
 */
public final class DaylightScheduler extends BroadcastReceiver {
    private static final String TAG = "BreezyKwgt";
    // Fire shortly after the hour starts, so the hourly flag has already flipped.
    private static final long DELAY_MILLIS = 60_000L;

    static void scheduleNextSwitch(Context context, JSONObject data, long nowMillis) {
        AlarmManager alarms = context.getSystemService(AlarmManager.class);
        if (alarms == null) return;
        PendingIntent intent = PendingIntent.getBroadcast(context, 0,
            new Intent(context, DaylightScheduler.class),
            PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        long next = KwgtPublisher.nextDaylightSwitch(data, nowMillis);
        if (next < 0) {
            alarms.cancel(intent);
            return;
        }
        // Allowed in Doze; a plain inexact alarm was observed hours late (moon at 13:00).
        alarms.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, next + DELAY_MILLIS, intent);
        Log.i(TAG, "Next day/night switch at " + new java.util.Date(next));
    }

    @Override public void onReceive(Context context, Intent intent) {
        KwgtPublisher.resendCached(context);
    }
}
