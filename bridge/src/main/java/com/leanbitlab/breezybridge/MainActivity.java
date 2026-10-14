package com.leanbitlab.breezybridge;

import android.app.Activity;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.SharedPreferences;
import android.content.res.Configuration;
import android.content.res.TypedArray;
import android.graphics.Color;
import android.os.Build;
import android.os.Bundle;
import android.text.format.DateFormat;
import android.text.Editable;
import android.text.TextWatcher;
import android.util.TypedValue;
import android.view.View;
import android.view.WindowInsets;
import android.view.WindowInsetsController;
import android.widget.AdapterView;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.Spinner;
import android.widget.TextView;
import android.widget.Toast;

import org.json.JSONObject;
import java.util.Collections;
import java.util.Locale;
import java.util.Map;

/**
 * Hidden settings screen and searchable reference for all KWGT variables.
 * Tap any variable to copy $br(breezy, variable)$.
 */
public final class MainActivity extends Activity {
    private static final int MAIN = Color.rgb(35, 47, 65);
    private static final int MUTED = Color.rgb(94, 112, 131);
    private static final int ACCENT = Color.rgb(39, 105, 166);

    /** Interface language of this screen, independent of the system language. */
    private static final String LANGUAGE_KEY = "ui_language";
    private static final String[] LANGUAGES = {"en", "ru"};
    private static final String[] LANGUAGE_NAMES = {"English", "Русский"};

    private static final class Entry {
        final int groupRes, descriptionRes;
        final String name;
        Entry(int groupRes, String name, int descriptionRes) {
            this.groupRes = groupRes;
            this.name = name;
            this.descriptionRes = descriptionRes;
        }
    }

    // Keep variable names in sync with KwgtPublisher.KEYS.
    private static final Entry[] CATALOG = {
        new Entry(R.string.group_now, "temp", R.string.var_temp),
        new Entry(R.string.group_now, "feels", R.string.var_feels),
        new Entry(R.string.group_now, "like", R.string.var_like),
        new Entry(R.string.group_now, "condition", R.string.var_condition),
        new Entry(R.string.group_now, "code", R.string.var_code),
        new Entry(R.string.group_now, "icon", R.string.var_icon),
        new Entry(R.string.group_now, "icon_flat", R.string.var_icon_flat),
        new Entry(R.string.group_now, "icon_glyph", R.string.var_icon_glyph),
        new Entry(R.string.group_now, "is_day", R.string.var_is_day),
        new Entry(R.string.group_now, "humidity", R.string.var_humidity),
        new Entry(R.string.group_now, "precip", R.string.var_precip),
        new Entry(R.string.group_now, "details", R.string.var_details),
        new Entry(R.string.group_wind, "wind", R.string.var_wind),
        new Entry(R.string.group_wind, "wind_kmh", R.string.var_wind_kmh),
        new Entry(R.string.group_wind, "wind_ms", R.string.var_wind_ms),
        new Entry(R.string.group_wind, "wind_direction", R.string.var_wind_direction),
        new Entry(R.string.group_wind, "wind_degrees", R.string.var_wind_degrees),
        new Entry(R.string.group_wind, "wind_arrow", R.string.var_wind_arrow),
        new Entry(R.string.group_wind, "wind_text", R.string.var_wind_text),
        new Entry(R.string.group_today, "today_max", R.string.var_today_max),
        new Entry(R.string.group_today, "today_min", R.string.var_today_min),
        new Entry(R.string.group_today, "today_range", R.string.var_today_range),
        new Entry(R.string.group_today, "today_compact", R.string.var_today_compact),
        new Entry(R.string.group_tomorrow, "tomorrow_max", R.string.var_tomorrow_max),
        new Entry(R.string.group_tomorrow, "tomorrow_min", R.string.var_tomorrow_min),
        new Entry(R.string.group_tomorrow, "tomorrow_range", R.string.var_tomorrow_range),
        new Entry(R.string.group_tomorrow, "tomorrow", R.string.var_tomorrow),
        new Entry(R.string.group_tomorrow, "tomorrow_compact", R.string.var_tomorrow_compact),
        new Entry(R.string.group_tomorrow, "tomorrow_precip", R.string.var_tomorrow_precip),
        new Entry(R.string.group_tomorrow, "tomorrow_icon", R.string.var_tomorrow_icon),
        new Entry(R.string.group_tomorrow, "tomorrow_icon_flat", R.string.var_tomorrow_icon_flat),
        new Entry(R.string.group_tomorrow, "tomorrow_icon_glyph", R.string.var_tomorrow_icon_glyph),
        new Entry(R.string.group_other, "location", R.string.var_location)
    };

    private LinearLayout entriesContainer;
    private EditText search;
    private TextView status;
    private Button grant;
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

    @Override protected void attachBaseContext(Context base) {
        String language = base.getSharedPreferences(KwgtPublisher.PREFS, Context.MODE_PRIVATE)
            .getString(LANGUAGE_KEY, LANGUAGES[0]);
        Configuration config = new Configuration(base.getResources().getConfiguration());
        config.setLocale(Locale.forLanguageTag(language));
        super.attachBaseContext(base.createConfigurationContext(config));
    }

    @Override public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        ScrollView scroll = new ScrollView(this);
        setupSystemBars(scroll);
        LinearLayout main = new LinearLayout(this);
        main.setOrientation(LinearLayout.VERTICAL);
        main.setPadding(dp(18), dp(20), dp(18), dp(32));
        scroll.addView(main);

        TextView title = text(getString(R.string.app_name), 23, MAIN);
        title.setTypeface(null, android.graphics.Typeface.BOLD);
        main.addView(title);
        TextView caption = text(getString(R.string.intro_caption), 14, MUTED);
        caption.setPadding(0, dp(6), 0, dp(12));
        main.addView(caption);

        status = text("", 14, ACCENT);
        main.addView(status);

        grant = new Button(this);
        grant.setText(R.string.grant_button);
        grant.setOnClickListener(v -> {
            String needed = ProviderBridge.permissionToRequest(this);
            if (needed == null) {
                Toast.makeText(this, ProviderBridge.status(this), Toast.LENGTH_LONG).show();
            } else {
                requestPermissions(new String[]{needed}, 42);
            }
        });
        main.addView(grant);

        Button resend = new Button(this);
        resend.setText(R.string.resend_button);
        resend.setOnClickListener(v -> {
            resend.setEnabled(false);
            new Thread(() -> {
                boolean ok = ProviderBridge.refreshAndPublish(getApplicationContext());
                runOnUiThread(() -> {
                    resend.setEnabled(true);
                    loadLatest();
                    drawList();
                    Toast.makeText(this,
                        ok ? R.string.send_success : R.string.send_failure,
                        Toast.LENGTH_LONG).show();
                });
            }, "breezy-kwgt-manual").start();
        });
        main.addView(resend);

        addSettings(main);

        TextView hint = text(getString(R.string.catalog_hint), 14, MAIN);
        hint.setPadding(0, dp(16), 0, dp(10));
        main.addView(hint);

        search = new EditText(this);
        search.setSingleLine(true);
        search.setTextSize(15);
        search.setHint(R.string.search_hint);
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

    @Override public void onRequestPermissionsResult(int requestCode,
                                                      String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        loadLatest();
        if (requestCode == 42 && grantResults.length > 0 &&
            grantResults[0] == android.content.pm.PackageManager.PERMISSION_GRANTED) {
            new Thread(() -> {
                ProviderBridge.refreshAndPublish(getApplicationContext());
                runOnUiThread(() -> { loadLatest(); drawList(); });
            }, "breezy-kwgt-first-refresh").start();
        }
    }

    private void addSettings(LinearLayout main) {
        SharedPreferences prefs = getSharedPreferences(KwgtPublisher.PREFS, Context.MODE_PRIVATE);

        String[] styleNames = {
            getString(R.string.style_filled),
            getString(R.string.style_outline),
            getString(R.string.style_breezy)
        };
        addChoice(main, R.string.label_icon_style, styleNames,
            indexOf(KwgtPublisher.STYLES, KwgtPublisher.iconStyle(this)), index -> {
                prefs.edit().putString(KwgtPublisher.STYLE_KEY, KwgtPublisher.STYLES[index]).apply();
                new Thread(() -> {
                    KwgtPublisher.resendCached(getApplicationContext());
                    runOnUiThread(() -> { loadLatest(); drawList(); });
                }, "breezy-kwgt-style").start();
            });

        addChoice(main, R.string.label_language, LANGUAGE_NAMES,
            indexOf(LANGUAGES, prefs.getString(LANGUAGE_KEY, LANGUAGES[0])), index -> {
                prefs.edit().putString(LANGUAGE_KEY, LANGUAGES[index]).apply();
                recreate();
            });
    }

    private interface OnChoice {
        void chosen(int index);
    }

    /** Label + dropdown; the callback runs only when the user picks another value. */
    private void addChoice(LinearLayout main, int labelRes, String[] names, int selected,
                           OnChoice onChoice) {
        TextView label = text(getString(labelRes), 14, MUTED);
        label.setPadding(0, dp(14), 0, 0);
        main.addView(label);
        Spinner spinner = new Spinner(this);
        ArrayAdapter<String> adapter =
            new ArrayAdapter<>(this, android.R.layout.simple_spinner_item, names);
        adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
        spinner.setAdapter(adapter);
        spinner.setSelection(selected, false);
        spinner.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener() {
            private int current = selected;
            @Override public void onItemSelected(AdapterView<?> parent, View view, int position, long id) {
                if (position == current) return;
                current = position;
                onChoice.chosen(position);
            }
            @Override public void onNothingSelected(AdapterView<?> parent) {}
        });
        main.addView(spinner);
    }

    private static int indexOf(String[] values, String value) {
        for (int i = 0; i < values.length; i++) {
            if (values[i].equals(value)) return i;
        }
        return 0;
    }

    /**
     * Android 15+ draws the activity behind the status and navigation bars:
     * pad the content by their insets and use dark bar icons on the light background.
     */
    private void setupSystemBars(View content) {
        int background;
        TypedArray attrs = obtainStyledAttributes(new int[]{android.R.attr.colorBackground});
        try {
            background = attrs.getColor(0, Color.WHITE);
        } finally {
            attrs.recycle();
        }
        content.setBackgroundColor(background);
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.VANILLA_ICE_CREAM) {
            getWindow().setStatusBarColor(background);
            getWindow().setNavigationBarColor(background);
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            int light = WindowInsetsController.APPEARANCE_LIGHT_STATUS_BARS |
                WindowInsetsController.APPEARANCE_LIGHT_NAVIGATION_BARS;
            getWindow().getDecorView().getWindowInsetsController()
                .setSystemBarsAppearance(light, light);
            content.setOnApplyWindowInsetsListener((v, insets) -> {
                android.graphics.Insets bars = insets.getInsets(
                    WindowInsets.Type.systemBars() | WindowInsets.Type.displayCutout());
                v.setPadding(bars.left, bars.top, bars.right, bars.bottom);
                return insets;
            });
        } else {
            getWindow().getDecorView().setSystemUiVisibility(
                View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR | View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR);
        }
    }

    private void loadLatest() {
        SharedPreferences prefs = getSharedPreferences(KwgtPublisher.PREFS, Context.MODE_PRIVATE);
        String json = prefs.getString(KwgtPublisher.CACHE_KEY, null);
        latestValues = Collections.emptyMap();
        if (json != null) {
            try {
                Map<String, String> values =
                    KwgtPublisher.variables(new JSONObject(json), System.currentTimeMillis(),
                        KwgtPublisher.iconStyle(this));
                if (values != null) latestValues = values;
            } catch (Exception ignored) {}
        }
        if (grant != null) {
            boolean granted = ProviderBridge.isGranted(this);
            grant.setEnabled(!granted);
            grant.setText(granted ? R.string.grant_done : R.string.grant_button);
        }
        if (status != null) {
            long time = prefs.getLong(KwgtPublisher.CACHE_TIME_KEY, 0);
            String when = time == 0 ? "" : DateFormat.getTimeFormat(this).format(new java.util.Date(time));
            String cache = latestValues.isEmpty()
                ? getString(R.string.cache_empty)
                : getString(R.string.cache_received, when, latestValues.size()).replace("  ", " ");
            status.setText(ProviderBridge.status(this) + "\n" + cache);
        }
    }

    private void drawList() {
        entriesContainer.removeAllViews();
        String filter = search.getText().toString().trim().toLowerCase(Locale.ROOT);
        String lastGroup = "";
        for (Entry e : CATALOG) {
            String group = getString(e.groupRes);
            String description = getString(e.descriptionRes);
            if (!filter.isEmpty() &&
                !(e.name + " " + description + " " + group)
                    .toLowerCase(Locale.ROOT).contains(filter)) continue;
            if (!group.equals(lastGroup)) {
                TextView heading = text(group, 17, ACCENT);
                heading.setTypeface(null, android.graphics.Typeface.BOLD);
                heading.setPadding(0, dp(18), 0, dp(8));
                entriesContainer.addView(heading);
                lastGroup = group;
            }

            LinearLayout row = new LinearLayout(this);
            row.setOrientation(LinearLayout.VERTICAL);
            row.setPadding(dp(10), dp(10), dp(10), dp(12));
            String formula = "$br(breezy, " + e.name + ")$";

            TextView name = text(e.name + "    ↗", 17, MAIN);
            name.setTypeface(android.graphics.Typeface.MONOSPACE, android.graphics.Typeface.BOLD);
            row.addView(name);
            TextView desc = text(description, 14, MUTED);
            desc.setPadding(0, dp(2), 0, dp(3));
            row.addView(desc);

            String value = latestValues.get(e.name);
            TextView sample = text(
                value == null || value.isEmpty()
                    ? getString(R.string.sample_empty)
                    : getString(R.string.sample_current, value),
                13, ACCENT);
            row.addView(sample);
            row.setOnClickListener(v -> {
                ClipboardManager manager =
                    (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
                if (manager != null) {
                    manager.setPrimaryClip(ClipData.newPlainText("KWGT " + e.name, formula));
                    Toast.makeText(this,
                        getString(R.string.copy_success, formula), Toast.LENGTH_SHORT).show();
                }
            });
            entriesContainer.addView(row);
            View divider = new View(this);
            divider.setBackgroundColor(0x1F536B87);
            entriesContainer.addView(divider, new LinearLayout.LayoutParams(-1, dp(1)));
        }
    }
}
