package com.leanbitlab.breezybridge;

import android.app.Activity;
import android.os.Bundle;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;
import android.util.TypedValue;

public final class MainActivity extends Activity {
    @Override public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        int pad = (int) TypedValue.applyDimension(
            TypedValue.COMPLEX_UNIT_DIP, 20, getResources().getDisplayMetrics());
        ScrollView scroll = new ScrollView(this);
        LinearLayout view = new LinearLayout(this);
        view.setOrientation(LinearLayout.VERTICAL);
        view.setPadding(pad, pad, pad, pad);
        scroll.addView(view);

        TextView description = new TextView(this);
        description.setTextSize(16);
        description.setText("Breezy → KWGT Bridge\n\n"
            + "Без иконки в меню приложений. Настройки открываются из Android → Приложения → Breezy → KWGT Bridge → Открыть настройки в приложении.\n\n"
            + "В Breezy включи передачу данных в Lwidget и обнови прогноз.\n\n"
            + "Переменные KWGT (используй, например, $br(breezy, wind_text)$):\n"
            + "• temp, feels, condition, icon\n"
            + "• wind, wind_kmh, wind_ms\n"
            + "• wind_direction, wind_degrees, wind_text\n"
            + "• tomorrow_max, tomorrow_min\n"
            + "• tomorrow_range, tomorrow\n"
            + "• tomorrow_precip, tomorrow_icon\n"
            + "• humidity, precip, location\n\n"
            + "Данные об отсутствии прогноза не заменяются придуманными значениями.");
        view.addView(description);

        Button resend = new Button(this);
        resend.setText("Повторно отправить последнюю погоду в KWGT");
        resend.setOnClickListener(v -> {
            boolean ok = WeatherReceiver.resendCached(this);
            Toast.makeText(this,
                ok ? "Данные отправлены в KWGT" :
                    "Данных пока нет — обнови прогноз Breezy",
                Toast.LENGTH_LONG).show();
        });
        view.addView(resend);
        setContentView(scroll);
    }
}
