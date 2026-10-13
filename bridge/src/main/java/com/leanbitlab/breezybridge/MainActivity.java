package com.leanbitlab.breezybridge;

import android.app.Activity;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.graphics.Color;
import android.os.Bundle;
import android.text.Editable;
import android.text.TextWatcher;
import android.util.TypedValue;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import org.json.JSONObject;
import java.util.Collections;
import java.util.Locale;
import java.util.Map;

/**
 * Documentation browser for EVERY variable emitted by WeatherReceiver.
 * Tap any entry to copy a ready-made $br(breezy, variable)$ formula.
 */
public final class MainActivity extends Activity {
    private static final int MAIN = Color.rgb(35, 47, 65);
    private static final int MUTED = Color.rgb(94, 112, 131);
    private static final int ACCENT = Color.rgb(39, 105, 166);

    private static final class Entry {
        final String group, name, description;
        Entry(String group, String name, String description) {
            this.group = group;
            this.name = name;
            this.description = description;
        }
    }

    // Keep names in sync with WeatherReceiver.KEYS (also verified in CI).
    private static final Entry[] CATALOG = {
        new Entry("Сейчас", "temp", "Текущая температура, ° (например, 8°)"),
        new Entry("Сейчас", "feels", "Ощущается как, с надписью Feels like"),
        new Entry("Сейчас", "like", "Ощущается как, только температура в градусах"),
        new Entry("Сейчас", "condition", "Текст текущей погоды из Breezy"),
        new Entry("Сейчас", "code", "Числовой погодный код (OpenWeather-подобный)"),
        new Entry("Сейчас", "icon", "Погодный символ Emoji"),
        new Entry("Сейчас", "icon_flat", "Название векторной иконки в шрифте Meteo"),
        new Entry("Сейчас", "humidity", "Относительная влажность, %"),
        new Entry("Сейчас", "precip", "Вероятность осадков сейчас, %"),
        new Entry("Сейчас", "details", "Общая строка: Like, стрелка ветра, м/с и влажность"),
        new Entry("Ветер", "wind", "Скорость ветра в km/h (английская подпись)"),
        new Entry("Ветер", "wind_kmh", "Скорость ветра в км/ч"),
        new Entry("Ветер", "wind_ms", "Скорость ветра в м/с"),
        new Entry("Ветер", "wind_direction", "Откуда дует ветер: С, СВ, В, ЮВ, Ю, ЮЗ, З, СЗ"),
        new Entry("Ветер", "wind_degrees", "Откуда дует ветер, азимут 0–359°"),
        new Entry("Ветер", "wind_arrow", "Стрелка направления, КУДА дует воздух"),
        new Entry("Ветер", "wind_text", "Сторона света (откуда) + скорость в м/с"),
        new Entry("Сегодня", "today_max", "Максимальная температура за сегодня, °"),
        new Entry("Сегодня", "today_min", "Минимальная температура за сегодня, °"),
        new Entry("Сегодня", "today_range", "Сегодня: максимум/минимум, например 10/7°"),
        new Entry("Сегодня", "today_compact", "Готовая строка Today: 10/7°"),
        new Entry("Завтра", "tomorrow_max", "Завтрашняя максимальная температура, °"),
        new Entry("Завтра", "tomorrow_min", "Завтрашняя минимальная температура, °"),
        new Entry("Завтра", "tomorrow_range", "Завтра: максимум ↑ и минимум ↓, °"),
        new Entry("Завтра", "tomorrow", "Готовая строка «Завтра ↑… ↓…»"),
        new Entry("Завтра", "tomorrow_compact", "Готовая строка Tomorrow: 8/4°"),
        new Entry("Завтра", "tomorrow_precip", "Вероятность осадков завтра, %"),
        new Entry("Завтра", "tomorrow_icon", "Завтрашняя погода — символ Emoji"),
        new Entry("Завтра", "tomorrow_icon_flat", "Иконка погоды завтра: название в наборе Meteo"),
        new Entry("Другое", "location", "Название населённого пункта из Breezy")
    };

    private LinearLayout entriesContainer;
    private EditText search;
    private TextView status;
    private Map<String, String> latestValues = Collections.emptyMap();

    private int dp(float n) {
        return (int) TypedValue.applyDimension(
            TypedValue.COMPLEX_UNIT_DIP, n, getResources().getDisplayMetrics());
    }

    private TextView text(String value, float sp, int color) {
        TextView t = new TextView(this);
        t.setText(value);
        t.setTextSize(sp);
        t.setTextColor(color);
        return t;
    }

    @Override public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        ScrollView scroll = new ScrollView(this);
        LinearLayout main = new LinearLayout(this);
        main.setOrientation(LinearLayout.VERTICAL);
        main.setPadding(dp(18), dp(20), dp(18), dp(32));
        scroll.addView(main);

        TextView title = text("Breezy → KWGT Bridge", 23, MAIN);
        title.setTypeface(null, android.graphics.Typeface.BOLD);
        main.addView(title);
        TextView caption = text(
            "Передача погоды без интернета и геолокации.\n" +
            "В Breezy включи передачу в Lwidget и обнови прогноз.",
            14, MUTED);
        caption.setPadding(0, dp(6), 0, dp(12));
        main.addView(caption);

        status = text("", 14, ACCENT);
        main.addView(status);

        Button resend = new Button(this);
        resend.setText("Передать последние данные в KWGT");
        resend.setOnClickListener(v -> {
            boolean ok = WeatherReceiver.resendCached(this);
            loadLatest();
            drawList();
            Toast.makeText(this,
                ok ? "Отправлено в KWGT" : "Данных нет — обнови прогноз в Breezy",
                Toast.LENGTH_LONG).show();
        });
        main.addView(resend);

        TextView hint = text(
            "Справочник переменных\nНажми на любую строку, чтобы скопировать " +
            "формулу для вставки в KWGT. Справа показано последнее значение.",
            14, MAIN);
        hint.setPadding(0, dp(16), 0, dp(10));
        main.addView(hint);

        search = new EditText(this);
        search.setSingleLine(true);
        search.setTextSize(15);
        search.setHint("Поиск переменной или показателя");
        main.addView(search);
        entriesContainer = new LinearLayout(this);
        entriesContainer.setOrientation(LinearLayout.VERTICAL);
        main.addView(entriesContainer);

        search.addTextChangedListener(new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence s, int start, int count, int after) {}
            @Override public void onTextChanged(CharSequence s, int start, int before, int count) {
                drawList();
            }
            @Override public void afterTextChanged(Editable s) {}
        });
        setContentView(scroll);
        loadLatest();
        drawList();
    }

    @Override protected void onResume() {
        super.onResume();
        if (entriesContainer != null) {
            loadLatest();
            drawList();
        }
    }

    private void loadLatest() {
        String json = getSharedPreferences("breezy_bridge", Context.MODE_PRIVATE)
            .getString("last_json", null);
        latestValues = Collections.emptyMap();
        if (json != null) {
            try {
                Map<String, String> values = WeatherReceiver.variables(new JSONObject(json));
                if (values != null) latestValues = values;
            } catch (Exception ignored) {}
        }
        if (status != null) {
            status.setText(latestValues.isEmpty()
                ? "Пока нет данных от Breezy"
                : "Данные получены • переменных: " + latestValues.size());
        }
    }

    private void drawList() {
        entriesContainer.removeAllViews();
        String filter = search.getText().toString().trim().toLowerCase(Locale.ROOT);
        String lastGroup = "";
        for (Entry e : CATALOG) {
            if (!filter.isEmpty() &&
                !(e.name + " " + e.description + " " + e.group)
                    .toLowerCase(Locale.ROOT).contains(filter)) continue;
            if (!e.group.equals(lastGroup)) {
                TextView heading = text(e.group, 17, ACCENT);
                heading.setTypeface(null, android.graphics.Typeface.BOLD);
                heading.setPadding(0, dp(18), 0, dp(8));
                entriesContainer.addView(heading);
                lastGroup = e.group;
            }
            LinearLayout row = new LinearLayout(this);
            row.setOrientation(LinearLayout.VERTICAL);
            row.setPadding(dp(10), dp(10), dp(10), dp(12));

            String formula = "$br(breezy, " + e.name + ")$";
            TextView name = text(e.name + "    ↗", 17, MAIN);
            name.setTypeface(android.graphics.Typeface.MONOSPACE, android.graphics.Typeface.BOLD);
            row.addView(name);
            TextView desc = text(e.description, 14, MUTED);
            desc.setPadding(0, dp(2), 0, dp(3));
            row.addView(desc);

            String value = latestValues.get(e.name);
            TextView sample = text(
                value == null || value.isEmpty() ? "Последнее значение: —" :
                    "Сейчас: " + value, 13, ACCENT);
            row.addView(sample);
            row.setOnClickListener(v -> {
                ClipboardManager manager =
                    (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
                if (manager != null) {
                    manager.setPrimaryClip(ClipData.newPlainText("KWGT " + e.name, formula));
                    Toast.makeText(this, "Скопировано: " + formula, Toast.LENGTH_SHORT).show();
                }
            });
            entriesContainer.addView(row);
            View divider = new View(this);
            divider.setBackgroundColor(0x1F536B87);
            entriesContainer.addView(divider, new LinearLayout.LayoutParams(-1, dp(1)));
        }
    }
}
