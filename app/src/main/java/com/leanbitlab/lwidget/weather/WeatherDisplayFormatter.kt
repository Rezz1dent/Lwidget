package com.leanbitlab.lwidget.weather

import kotlin.math.roundToInt

/**
 * Weather data is sent by Breezy in Gadgetbridge format:
 * temperatures in Kelvin, wind in km/h, pressure in hPa.
 * Keep this formatter free of Android dependencies so its output can be unit-tested.
 */
object WeatherDisplayFormatter {
    const val PREF_KEY = "weather_display_fields"
    val OPTIONS = listOf(
        "temperature", "condition", "feels_like", "precipitation",
        "humidity", "wind", "pressure", "high_low"
    )
    private val DEFAULT = listOf("temperature", "condition")

    fun selectedFields(value: String?): List<String> =
        value?.split(',')?.map(String::trim)?.filter { it in OPTIONS }?.distinct()
            ?.takeIf { it.isNotEmpty() } ?: DEFAULT

    fun display(data: BreezyGadgetbridgeData, selection: List<String>, russian: Boolean): String {
        val parts = selection.mapNotNull { field ->
            when (field) {
                "temperature" -> data.currentTemp?.let { "${degrees(it)}C" }
                "condition" -> data.currentCondition?.trim()?.takeIf { it.isNotEmpty() }
                "feels_like" -> data.feelsLikeTemp?.let {
                    "${if (russian) "Ощ." else "Feels"} ${degrees(it)}"
                }
                "precipitation" -> data.precipProbability?.let {
                    "${if (russian) "Осадки" else "Precip"} ${it}%"
                }
                "humidity" -> data.currentHumidity?.let {
                    "${if (russian) "Влажн." else "Humidity"} ${it}%"
                }
                "wind" -> data.windSpeed?.let {
                    "${if (russian) "Ветер" else "Wind"} ${it.roundToInt()} ${if (russian) "км/ч" else "km/h"}"
                }
                "pressure" -> data.pressure?.let {
                    if (russian) "Давл. ${(it * 0.750061683f).roundToInt()} мм рт.ст."
                    else "Pressure ${it.roundToInt()} hPa"
                }
                "high_low" -> {
                    val high = data.todayMaxTemp?.let(::degrees)
                    val low = data.todayMinTemp?.let(::degrees)
                    if (high == null && low == null) null
                    else listOfNotNull(high?.let { "↑$it" }, low?.let { "↓$it" }).joinToString(" ")
                }
                else -> null
            }
        }
        return parts.joinToString(" · ").ifBlank { "—" }
    }

    fun currentTemperature(data: BreezyGadgetbridgeData): String =
        data.currentTemp?.let { "${degrees(it)}C" } ?: "—"

    fun feelsLike(data: BreezyGadgetbridgeData): String? =
        data.feelsLikeTemp?.let { "Feels like ${degrees(it)}C" }

    fun currentDescription(data: BreezyGadgetbridgeData): String? =
        data.currentCondition?.trim()?.takeIf { it.isNotEmpty() }

    private fun degrees(kelvin: Int): String {
        val celsius = (kelvin - 273.15).roundToInt()
        return "${if (celsius > 0) "+" else ""}${celsius}°"
    }
}
