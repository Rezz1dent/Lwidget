package com.leanbitlab.breezybridge;

import android.app.Activity;
import android.os.Bundle;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

public final class MainActivity extends Activity {
    @Override public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        LinearLayout view = new LinearLayout(this);
        view.setOrientation(LinearLayout.VERTICAL);
        view.setPadding(24, 40, 24, 24);
        TextView description = new TextView(this);
        description.setTextSize(18);
        description.setText("Breezy → KWGT Bridge\n\n"
            + "1. Open Breezy Weather → Widgets and Live Wallpaper / Data Sharing.\n"
            + "2. Enable Gadgetbridge data sharing for Lwidget.\n"
            + "3. Refresh the weather in Breezy.\n"
            + "4. KWGT should display $br(breezy, temp)$ and related variables.\n\n"
            + "This bridge replaces Lwidget and needs no network or location permissions.");
        view.addView(description);
        Button resend = new Button(this);
        resend.setText("Resend last weather to KWGT");
        resend.setOnClickListener(v -> {
            boolean ok = WeatherReceiver.resendCached(this);
            Toast.makeText(this,
                ok ? "Cached weather sent to KWGT" :
                    "No Breezy data yet — refresh Breezy Weather",
                Toast.LENGTH_LONG).show();
        });
        view.addView(resend);
        setContentView(view);
    }
}
