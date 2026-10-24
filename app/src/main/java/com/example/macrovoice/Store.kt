package com.example.macrovoice

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject

/** Tiny persistence layer: meals as a JSON string in SharedPreferences. */
class Store(context: Context) {
    private val prefs = context.getSharedPreferences("macrovoice", Context.MODE_PRIVATE)

    var apiKey: String
        get() = prefs.getString("api_key", "") ?: ""
        set(v) = prefs.edit().putString("api_key", v.trim()).apply()

    /** BCP-47 tag used for speech recognition, e.g. "en-US" or "nl-NL". */
    var language: String
        get() = prefs.getString("language", "en-US") ?: "en-US"
        set(v) = prefs.edit().putString("language", v).apply()

    fun meals(): List<Meal> {
        val arr = JSONArray(prefs.getString("meals", "[]"))
        return (0 until arr.length()).map { i ->
            val o = arr.getJSONObject(i)
            val items = o.getJSONArray("items")
            Meal(
                id = o.getLong("id"),
                timeMillis = o.getLong("time"),
                spoken = o.getString("spoken"),
                items = (0 until items.length()).map { j ->
                    val f = items.getJSONObject(j)
                    FoodItem(
                        f.getString("name"), f.getString("amount"),
                        f.getDouble("kcal"), f.getDouble("protein"),
                        f.getDouble("carbs"), f.getDouble("fat"),
                    )
                },
            )
        }
    }

    fun save(meals: List<Meal>) {
        val arr = JSONArray()
        meals.forEach { m ->
            arr.put(JSONObject().apply {
                put("id", m.id)
                put("time", m.timeMillis)
                put("spoken", m.spoken)
                put("items", JSONArray().also { ia ->
                    m.items.forEach { f ->
                        ia.put(JSONObject().apply {
                            put("name", f.name); put("amount", f.amount)
                            put("kcal", f.kcal); put("protein", f.protein)
                            put("carbs", f.carbs); put("fat", f.fat)
                        })
                    }
                })
            })
        }
        prefs.edit().putString("meals", arr.toString()).apply()
    }
}
