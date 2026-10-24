package com.example.macrovoice

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONArray
import org.json.JSONObject
import java.util.concurrent.TimeUnit

/** Turns a rough spoken description into per-item macros using the Claude API. */
class MacroEstimator(private val apiKey: String) {

    private val client = OkHttpClient.Builder()
        .readTimeout(60, TimeUnit.SECONDS)
        .build()

    suspend fun estimate(spoken: String): List<FoodItem> = withContext(Dispatchers.IO) {
        val body = JSONObject().apply {
            put("model", MODEL)
            put("max_tokens", 1500)
            put("system", SYSTEM)
            put("tools", JSONArray().put(TOOL))
            put("tool_choice", JSONObject().put("type", "tool").put("name", "log_meal"))
            put("messages", JSONArray().put(JSONObject().put("role", "user").put("content", spoken)))
        }
        val req = Request.Builder()
            .url("https://api.anthropic.com/v1/messages")
            .header("x-api-key", apiKey)
            .header("anthropic-version", "2023-06-01")
            .post(body.toString().toRequestBody("application/json".toMediaType()))
            .build()

        client.newCall(req).execute().use { resp ->
            val text = resp.body?.string().orEmpty()
            if (!resp.isSuccessful) {
                val msg = runCatching { JSONObject(text).getJSONObject("error").getString("message") }
                    .getOrDefault(text.take(200))
                error("API error ${resp.code}: $msg")
            }
            val content = JSONObject(text).getJSONArray("content")
            val input = (0 until content.length())
                .map { content.getJSONObject(it) }
                .first { it.getString("type") == "tool_use" }
                .getJSONObject("input")
            val items = input.getJSONArray("items")
            (0 until items.length()).map { i ->
                val o = items.getJSONObject(i)
                FoodItem(
                    name = o.getString("name"),
                    amount = o.getString("amount"),
                    kcal = o.getDouble("kcal"),
                    protein = o.getDouble("protein_g"),
                    carbs = o.getDouble("carbs_g"),
                    fat = o.getDouble("fat_g"),
                )
            }
        }
    }

    companion object {
        private const val MODEL = "claude-haiku-5-5"

        private val SYSTEM = """
            You are a nutrition estimator inside a voice food-logging app. The user lives in the
            Netherlands and describes what they ate roughly, often by Dutch supermarket brand
            (Albert Heijn, AH Basic, Jumbo, Lidl, etc.). The text comes from speech recognition, so
            fix obvious mis-hearings. Split the meal into separate food items, estimate a realistic
            portion in grams/ml for each (use typical package or serving sizes when the user gives
            counts like "2 loaves" or "a bowl"), and give macros for the whole portion eaten, not per
            100 g. Use your knowledge of the brand's actual products when you know them, otherwise a
            typical equivalent. Always answer by calling log_meal.
        """.trimIndent()

        private val TOOL = JSONObject("""
            {
              "name": "log_meal",
              "description": "Record the estimated macros for each food item eaten.",
              "input_schema": {
                "type": "object",
                "properties": {
                  "items": {
                    "type": "array",
                    "items": {
                      "type": "object",
                      "properties": {
                        "name": {"type": "string", "description": "Food name incl. brand if known"},
                        "amount": {"type": "string", "description": "Assumed portion, e.g. '2 loaves, ~1600 g'"},
                        "kcal": {"type": "number"},
                        "protein_g": {"type": "number"},
                        "carbs_g": {"type": "number"},
                        "fat_g": {"type": "number"}
                      },
                      "required": ["name", "amount", "kcal", "protein_g", "carbs_g", "fat_g"]
                    }
                  }
                },
                "required": ["items"]
              }
            }
        """.trimIndent())
    }
}
