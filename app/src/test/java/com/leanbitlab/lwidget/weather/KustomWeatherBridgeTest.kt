package com.leanbitlab.lwidget.weather

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Test

class KustomWeatherBridgeTest {
    @Test fun convertsBreezyValuesForKwgt() {
        val variables = KustomWeatherBridge.toVariables(
            BreezyGadgetbridgeData(
                currentTemp = 294,
                feelsLikeTemp = 289,
                currentCondition = "Средняя изморозь",
                currentConditionCode = 741,
                currentHumidity = 71,
                precipProbability = 31
            )
        )
        assertEquals("+21°C", variables["temp"])
        assertEquals("Feels like +16°C", variables["feels"])
        assertEquals("Средняя изморозь", variables["condition"])
        assertEquals("741", variables["code"])
        assertEquals("🌫️", variables["icon"])
        assertEquals("71%", variables["humidity"])
        assertEquals("31%", variables["precip"])
    }

    @Test fun doesNotInventMissingMeasurements() {
        val variables = KustomWeatherBridge.toVariables(BreezyGadgetbridgeData())
        assertFalse(variables.containsKey("temp"))
        assertFalse(variables.containsKey("feels"))
        assertFalse(variables.containsKey("condition"))
    }
}
