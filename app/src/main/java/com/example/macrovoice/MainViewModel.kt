package com.example.macrovoice

import android.app.Application
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.launch
import java.time.LocalDate

enum class Period(val label: String, val kind: String) { DAY("Day", "day"), WEEK("Week", "week"), MONTH("Month", "month") }

class MainViewModel(app: Application) : AndroidViewModel(app) {
    val store = Store(app)

    var period by mutableStateOf(Period.DAY)
        private set
    var anchor by mutableStateOf(LocalDate.now())
        private set
    var entries by mutableStateOf<List<Entry>>(emptyList())
        private set
    var stats by mutableStateOf<PeriodStats?>(null)
        private set
    var busy by mutableStateOf(false)
        private set
    var error by mutableStateOf<String?>(null)
        private set
    var draft by mutableStateOf("")
    var listening by mutableStateOf(false)

    private fun api() = ApiClient(store.serverUrl, store.token)

    fun setError(message: String?) { error = message }

    fun selectPeriod(t: Period) { period = t; refresh() }

    fun shift(direction: Int) {
        anchor = when (period) {
            Period.DAY -> anchor.plusDays(direction.toLong())
            Period.WEEK -> anchor.plusWeeks(direction.toLong())
            Period.MONTH -> anchor.plusMonths(direction.toLong())
        }
        refresh()
    }

    fun goToday() { anchor = LocalDate.now(); refresh() }

    fun refresh() = viewModelScope.launch {
        try {
            val api = api()
            stats = api.stats(period.kind, anchor)
            entries = if (period == Period.DAY) api.entries(anchor) else emptyList()
            error = null
        } catch (e: ApiException) {
            error = e.message
        }
    }

    /** Recording is one action: the text is sent immediately and the server adds it to today. */
    fun submit(text: String) {
        val clean = text.trim()
        if (clean.isEmpty() || busy) return
        busy = true; error = null; draft = clean
        viewModelScope.launch {
            try {
                api().logEntry(clean)
                draft = ""
                anchor = LocalDate.now()
                refresh().join()
            } catch (e: ApiException) {
                error = e.message          // draft stays in the field so nothing is lost
            } finally {
                busy = false
            }
        }
    }

    fun delete(id: Long) = viewModelScope.launch {
        try { api().deleteEntry(id); refresh().join() } catch (e: ApiException) { error = e.message }
    }
}
