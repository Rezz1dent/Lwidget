package com.leanbitlab.breezybridge;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.util.Log;

/**
 * Breezy announces an updated forecast; the payload deliberately contains no
 * weather data. Query ContentProvider on a background thread after the event.
 */
public final class ContentUpdateReceiver extends BroadcastReceiver {
    private static final String TAG = "BreezyProviderBridge";

    @Override public void onReceive(Context context, Intent intent) {
        String action = intent.getAction();
        if (!"org.breezyweather.ACTION_UPDATE_NOTIFIER".equals(action)
            && !"org.breezyweather.debug.ACTION_UPDATE_NOTIFIER".equals(action))
            return;
        final PendingResult pending = goAsync();
        final Context app = context.getApplicationContext();
        new Thread(() -> {
            try {
                if (ProviderWeather.hasPermission(app)) ProviderWeather.refresh(app);
            } catch (Exception e) {
                Log.e(TAG, "Could not refresh after weather update", e);
            } finally {
                pending.finish();
            }
        }, "breezy-provider-update").start();
    }
}
