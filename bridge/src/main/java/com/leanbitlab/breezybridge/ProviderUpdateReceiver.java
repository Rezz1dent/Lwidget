package com.leanbitlab.breezybridge;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.util.Log;

/** Reacts to Breezy provider update notifications, then reads through its API. */
public final class ProviderUpdateReceiver extends BroadcastReceiver {
    @Override public void onReceive(Context context, Intent intent) {
        String action = intent.getAction();
        if (!"org.breezyweather.ACTION_UPDATE_NOTIFIER".equals(action) &&
            !"org.breezyweather.debug.ACTION_UPDATE_NOTIFIER".equals(action)) return;
        PendingResult pending = goAsync();
        Context application = context.getApplicationContext();
        new Thread(() -> {
            try {
                ProviderBridge.refreshAndPublish(application);
            } catch (Exception e) {
                Log.e("BreezyProviderBridge", "Refresh after notification failed", e);
            } finally {
                pending.finish();
            }
        }, "breezy-kwgt-update").start();
    }
}
