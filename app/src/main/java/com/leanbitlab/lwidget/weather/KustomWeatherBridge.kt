package com.leanbitlab.lwidget.weather

import android.content.Context
import android.content.Intent

/**
 * Forward Breezy's Gadgetbridge data to Kustom (KWGT) using its documented
 * org.kustom.action.SEND_VAR API. Lwidget remains the Breezy receiver.
 *
 * KWGT variables use `$br(breezy, temp)$`, `$br(breezy, feels)$`, etc.
 */
object KustomWeatherBridge {
    const val EXT_NAME = "breezy"
    const val ACTION = "org.kustom.action.SEND_VAR"
    private const val EXTRA_SOURCE = "org.kustom.action.EXT_NAME"
    private const val EXTRA_NAMES = "org.kustom.action.VAR_NAME_ARRAY"
    private const val EXTRA_VALUES = "org.kustom.action.VAR_VALUE_ARRAY"

    fun toVariables(data: BreezyGadgetbridgeData): Map<String, String> {
        val result = linkedMapOf<String, String>()
        data.currentTemp?.let {
            result["temp"] = WeatherDisplayFormatter.currentTemperature(data)
        }
        data.feelsLikeTemp?.let {
            result["feels"] = WeatherDisplayFormatter.feelsLike(data) ?: ""
        }
        data.currentCondition?.takeIf { it.isNotBlank() }?.let {
            result["condition"] = it.trim()
        }
        data.currentConditionCode?.let {
            result["code"] = it.toString()
            result["icon"] = weatherSymbol(it)
        }
        data.currentHumidity?.let { result["humidity"] = "${it}%" }
        data.precipProbability?.let { result["precip"] = "${it}%" }
        data.windSpeed?.let { result["wind"] = "${it.toInt()} km/h" }
        data.location?.let { result["location"] = it }
        return result
    }

    fun send(context: Context, data: BreezyGadgetbridgeData) {
        val variables = toVariables(data)
        if (variables.isEmpty()) return
        val intent = Intent(ACTION).apply {
            `package` = "org.kustom.widget"
            putExtra(EXTRA_SOURCE, EXT_NAME)
            putExtra(EXTRA_NAMES, variables.keys.toTypedArray())
            putExtra(EXTRA_VALUES, variables.values.toTypedArray())
        }
        context.sendBroadcast(intent)
    }

    private fun weatherSymbol(code: Int): String = when (code) {
        800 -> "☀️"
        801 -> "🌤️"
        802 -> "⛅"
        803, 804 -> "☁️"
        in 200..232 -> "⛈️"
        in 300..531 -> "🌧️"
        in 600..622 -> "🌨️"
        741, 751 -> "🌫️"
        771 -> "💨"
        else -> "☁️"
    }
}
