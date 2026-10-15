package com.leanbitlab.breezybridge;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.util.Log;

/**
 * After a reboot or a bridge update: read Breezy's provider once.
 *
 * Breezy does not declare its own ACTION_UPDATE_NOTIFIER in <queries>, so on
 * Android 11+ it only sees the bridge after the bridge has accessed its content
 * provider. That implicit visibility does not survive a reboot or an update of the
 * bridge: Breezy then lists "no compatible packages" and drops the bridge from its
 * Update Notifier setting. Reading the provider here restores the visibility; it
 * also re-sends the weather to KWGT and re-schedules the day/night alarm, which a
 * reboot clears as well.
 */
public final class BootReceiver extends BroadcastReceiver {
    @Override public void onReceive(Context context, Intent intent) {
        String action = intent.getAction();
        if (!Intent.ACTION_BOOT_COMPLETED.equals(action) &&
            !Intent.ACTION_MY_PACKAGE_REPLACED.equals(action)) return;
        PendingResult pending = goAsync();
        Context application = context.getApplicationContext();
        new Thread(() -> {
            try {
                if (!ProviderBridge.refreshAndPublish(application)) {
                    KwgtPublisher.resendCached(application);
                }
            } catch (Exception e) {
                Log.e("BreezyProviderBridge", "Refresh after boot failed", e);
            } finally {
                pending.finish();
            }
        }, "breezy-kwgt-boot").start();
    }
}
