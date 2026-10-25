package com.example.macrovoice

import android.content.Context

/** Connection settings only; all diary data lives on the server. */
class Store(context: Context) {
    private val prefs = context.getSharedPreferences("macrovoice", Context.MODE_PRIVATE)

    var serverUrl: String
        get() = prefs.getString("server_url", "") ?: ""
        set(v) = prefs.edit().putString("server_url", v.trim()).apply()

    var token: String
        get() = prefs.getString("token", "") ?: ""
        set(v) = prefs.edit().putString("token", v.trim()).apply()

    /** BCP-47 tag used for speech recognition, e.g. "en-US" or "nl-NL". */
    var language: String
        get() = prefs.getString("language", "en-US") ?: "en-US"
        set(v) = prefs.edit().putString("language", v).apply()
}
