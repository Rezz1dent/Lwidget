package com.leanbitlab.lwidget.weather

import org.junit.Assert.assertEquals
import org.junit.Test

class WeatherDisplayFormatterTest {
    private val weather = BreezyGadgetbridgeData(
        currentTemp = 294,
        feelsLikeTemp = 289,
        currentCondition = "Partly cloudy",
        precipProbability = 31,
        currentHumidity = 71,
        windSpeed = 5.6f,
        pressure = 1013.25f,
        todayMaxTemp = 298,
        todayMinTemp = 283
    )

    @Test fun defaultSelectionIsReadable() {
        assertEquals(listOf("temperature", "condition"), WeatherDisplayFormatter.selectedFields(null))
        assertEquals(listOf("wind", "temperature"), WeatherDisplayFormatter.selectedFields("wind,temperature,wind,invalid"))
    }

    @Test fun formatsSelectedMetricValuesInRussian() {
        assertEquals(
            "+21°C · Осадки 31% · Влажн. 71%",
            WeatherDisplayFormatter.display(weather, listOf("temperature", "precipitation", "humidity"), true)
        )
        assertEquals(
            "Ощ. +16° · Ветер 6 км/ч · Давл. 760 мм рт.ст.",
            WeatherDisplayFormatter.display(weather, listOf("feels_like", "wind", "pressure"), true)
        )
    }

    @Test fun formatsEnglishAndDailyRange() {
        assertEquals(
            "+21°C · Precip 31% · ↑+25° ↓+10°",
            WeatherDisplayFormatter.display(weather, listOf("temperature", "precipitation", "high_low"), false)
        )
    }

    @Test fun buildsThreeLineWeatherContent() {
        assertEquals("+21°C", WeatherDisplayFormatter.currentTemperature(weather))
        assertEquals("Feels like +16°C", WeatherDisplayFormatter.feelsLike(weather))
        assertEquals("Partly cloudy", WeatherDisplayFormatter.currentDescription(weather))
        assertEquals("—", WeatherDisplayFormatter.currentTemperature(BreezyGadgetbridgeData()))
        assertEquals(null, WeatherDisplayFormatter.feelsLike(BreezyGadgetbridgeData()))
        assertEquals(null, WeatherDisplayFormatter.currentDescription(BreezyGadgetbridgeData()))
    }

    @Test fun ignoresUnavailableWeatherValues() {
        assertEquals("—", WeatherDisplayFormatter.display(BreezyGadgetbridgeData(), listOf("wind"), true))
        assertEquals("Partly cloudy", WeatherDisplayFormatter.display(weather, listOf("condition"), true))
    }
}
