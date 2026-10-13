package com.leanbitlab.breezybridge;

import android.content.ContentProvider;
import android.content.ContentValues;
import android.content.res.Resources;
import android.database.Cursor;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.drawable.Drawable;
import android.net.Uri;
import android.os.ParcelFileDescriptor;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;

/**
 * OPTIONAL local-device adapter. Serves original graphics directly from the
 * independently installed official Breezy Flat Icon Provider APK.
 *
 * No images from that non-free icon pack are ever bundled, stored, cached,
 * embedded in the KWGT preset or shipped with this project.
 * See https://github.com/breezy-weather/flat-icon-provider
 *
 * KWGT BitmapModule can request our content://.../weather_rain_flat URI.
 */
public final class FlatIconContentProvider extends ContentProvider {
    public static final String AUTHORITY = "com.rezz1dent.breezykwgtbridge.icons";
    public static final String PACK = "org.breezyweather.flaticonprovider";
    private static final String TAG = "FlatIconAdapter";

    // Exact Android resource names are taken from Flat Icon Provider's
    // app/src/main/res/xml/drawable_filter.xml. Accept only known names.
    private static final String[] ALLOWED = {
        "weather_clear_day_flat",
        "weather_clear_night_flat",
        "weather_partly_cloudy_day_flat",
        "weather_partly_cloudy_night_flat",
        "weather_cloudy_flat",
        "weather_rain_flat",
        "weather_snow_flat",
        "weather_wind_flat",
        "weather_fog_day_flat",
        "weather_fog_night_flat",
        "weather_haze_flat",
        "weather_sleet_flat",
        "weather_hail_flat",
        "weather_thunderstorm_flat"
    };

    public static String drawable(int code) {
        if (code == 800) return "weather_clear_day_flat";
        if (code == 801 || code == 802) return "weather_partly_cloudy_day_flat";
        if (code == 803 || code == 804) return "weather_cloudy_flat";
        if (code >= 200 && code <= 232) return "weather_thunderstorm_flat";
        if (code >= 600 && code <= 622) {
            if (code == 611 || code == 612 || code == 613) return "weather_sleet_flat";
            return "weather_snow_flat";
        }
        if (code >= 300 && code <= 531) return "weather_rain_flat";
        if (code == 771) return "weather_wind_flat";
        if (code == 741) return "weather_fog_day_flat";
        if (code >= 700 && code <= 781) return "weather_haze_flat";
        return "weather_cloudy_flat";
    }

    public static String uri(int code) {
        return "content://" + AUTHORITY + "/" + drawable(code);
    }

    public static boolean available(android.content.Context ctx) {
        try {
            return ctx.getPackageManager().getApplicationInfo(PACK, 0).enabled;
        } catch (Exception ignored) {
            return false;
        }
    }

    @Override public boolean onCreate() { return true; }

    @Override public String getType(Uri uri) { return "image/png"; }

    @Override public ParcelFileDescriptor openFile(Uri uri, String mode)
        throws FileNotFoundException {
        if (!"r".equals(mode)) throw new FileNotFoundException("read-only");
        if (uri == null || uri.getPathSegments().size() != 1)
            throw new FileNotFoundException("invalid icon");
        final String name = uri.getLastPathSegment();
        boolean allow = false;
        for (String v : ALLOWED) if (v.equals(name)) { allow = true; break; }
        if (!allow) throw new FileNotFoundException("unrecognized icon");
        if (getContext() == null || !available(getContext()))
            throw new FileNotFoundException("Flat Icon Provider is not installed");

        try {
            Resources resources = getContext().getPackageManager().getResourcesForApplication(PACK);
            int id = resources.getIdentifier(name, "drawable", PACK);
            if (id == 0) throw new FileNotFoundException("drawable missing: " + name);
            Drawable drawable = resources.getDrawable(id, null);
            if (drawable == null) throw new FileNotFoundException("empty drawable");

            ParcelFileDescriptor[] pipe = ParcelFileDescriptor.createPipe();
            final ParcelFileDescriptor write = pipe[1];
            // Render only on request. Never write the third-party artwork to disk.
            new Thread(() -> {
                try (FileOutputStream out =
                         new FileOutputStream(write.getFileDescriptor())) {
                    Bitmap bitmap = Bitmap.createBitmap(192, 192, Bitmap.Config.ARGB_8888);
                    Canvas canvas = new Canvas(bitmap);
                    drawable.setBounds(0, 0, 192, 192);
                    drawable.draw(canvas);
                    bitmap.compress(Bitmap.CompressFormat.PNG, 100, out);
                    bitmap.recycle();
                } catch (Exception e) {
                    Log.e(TAG, "Unable to render installed flat icon", e);
                } finally {
                    try { write.close(); } catch (Exception ignored) {}
                }
            }, "flat-icon-render").start();
            return pipe[0];
        } catch (FileNotFoundException e) {
            throw e;
        } catch (Exception e) {
            throw new FileNotFoundException("Unable to load optional flat icon: " + e);
        }
    }

    @Override public Cursor query(Uri uri, String[] projection, String selection,
                                   String[] selectionArgs, String sortOrder) {
        return null;
    }
    @Override public Uri insert(Uri uri, ContentValues values) { return null; }
    @Override public int update(Uri uri, ContentValues values, String selection,
                                String[] selectionArgs) { return 0; }
    @Override public int delete(Uri uri, String selection, String[] selectionArgs) { return 0; }
}
