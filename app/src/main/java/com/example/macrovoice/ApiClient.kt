package com.example.macrovoice

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.time.LocalDate
import java.util.concurrent.TimeUnit

class ApiException(message: String) : Exception(message)

/** Talks to the MacroVoice backend. `baseUrl` e.g. http://192.168.1.20:8000 */
class ApiClient(baseUrl: String, private val token: String) {
    private val base = baseUrl.trim().trimEnd('/')
    private val http = OkHttpClient.Builder()
        .connectTimeout(10, TimeUnit.SECONDS)
        .readTimeout(90, TimeUnit.SECONDS)   // AI fallback can be slow
        .build()

    private suspend fun call(configure: Request.Builder.() -> Unit): String = withContext(Dispatchers.IO) {
        if (base.isEmpty()) throw ApiException("Set the server address in Settings")
        val builder = Request.Builder()
        if (token.isNotBlank()) builder.header("Authorization", "Bearer $token")
        builder.configure()
        try {
            http.newCall(builder.build()).execute().use { r ->
                val body = r.body?.string().orEmpty()
                if (!r.isSuccessful) {
                    val detail = runCatching { JSONObject(body).get("detail").toString() }.getOrDefault(body.take(200))
                    throw ApiException("Server said ${r.code}: $detail")
                }
                body
            }
        } catch (e: java.io.IOException) {
            throw ApiException("Cannot reach the server: ${e.message}")
        }
    }

    suspend fun logEntry(text: String): Entry {
        val body = JSONObject().put("text", text).toString().toRequestBody("application/json".toMediaType())
        return ApiJson.entry(JSONObject(call { url("$base/entries"); post(body) }))
    }

    suspend fun entries(day: LocalDate): List<Entry> = ApiJson.entries(call { url("$base/entries?date=$day") })

    suspend fun stats(kind: String, anchor: LocalDate): PeriodStats =
        ApiJson.stats(call { url("$base/stats/$kind?date=$anchor") })

    suspend fun deleteEntry(id: Long) {
        call { url("$base/entries/$id"); delete() }
    }
}
