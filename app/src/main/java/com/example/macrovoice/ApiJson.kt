package com.example.macrovoice

import org.json.JSONObject

/** Pure JSON -> model mapping for the backend API (unit-tested on the JVM). */
object ApiJson {
    private fun JSONObject.dbl(key: String): Double? = if (isNull(key) || !has(key)) null else getDouble(key)
    private fun JSONObject.str(key: String): String? = if (isNull(key) || !has(key)) null else getString(key)

    private fun macros(o: JSONObject) =
        Macros(o.getDouble("kcal"), o.getDouble("protein"), o.getDouble("carbs"), o.getDouble("fat"))

    private fun item(o: JSONObject) = Item(
        id = o.getLong("id"),
        name = o.getString("name"),
        amountText = o.getString("amount_text"),
        grams = o.dbl("grams"),
        macros = if (o.getString("status") == "resolved") macros(o) else null,
        source = o.getString("source"),
        note = o.str("note"),
    )

    fun entry(o: JSONObject): Entry {
        val items = o.getJSONArray("items")
        val totals = o.getJSONObject("totals")
        return Entry(
            id = o.getLong("id"),
            loggedAt = o.getString("logged_at"),
            rawText = o.getString("raw_text"),
            items = (0 until items.length()).map { item(items.getJSONObject(it)) },
            totals = macros(totals),
            unresolvedItems = totals.getInt("unresolved_items"),
        )
    }

    fun entries(json: String): List<Entry> {
        val arr = JSONObject(json).getJSONArray("entries")
        return (0 until arr.length()).map { entry(arr.getJSONObject(it)) }
    }

    fun stats(json: String): PeriodStats {
        val o = JSONObject(json)
        val split = if (o.isNull("macro_split")) null else o.getJSONObject("macro_split")
        val days = o.getJSONArray("per_day")
        return PeriodStats(
            kind = o.getString("kind"),
            start = o.getString("start"),
            end = o.getString("end"),
            daysLogged = o.getInt("days_logged"),
            daysElapsed = o.getInt("days_elapsed"),
            totals = macros(o.getJSONObject("totals")),
            avgPerLoggedDay = if (o.isNull("avg_per_logged_day")) null else macros(o.getJSONObject("avg_per_logged_day")),
            avgPerDay = if (o.isNull("avg_per_day")) null else macros(o.getJSONObject("avg_per_day")),
            proteinPct = split?.getDouble("protein_pct"),
            carbsPct = split?.getDouble("carbs_pct"),
            fatPct = split?.getDouble("fat_pct"),
            unresolvedItems = o.getInt("unresolved_items"),
            perDay = (0 until days.length()).map {
                val d = days.getJSONObject(it)
                DayStat(d.getString("date"), d.getBoolean("logged"), macros(d))
            },
        )
    }
}
