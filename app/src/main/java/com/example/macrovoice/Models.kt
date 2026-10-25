package com.example.macrovoice

data class Macros(val kcal: Double, val protein: Double, val carbs: Double, val fat: Double)

data class Item(
    val id: Long,
    val name: String,
    val amountText: String,
    val grams: Double?,
    val macros: Macros?,        // null while unresolved
    val source: String,         // db | ai | manual | unresolved
    val note: String?,
) {
    val unresolved get() = macros == null
}

data class Entry(
    val id: Long,
    val loggedAt: String,
    val rawText: String,
    val items: List<Item>,
    val totals: Macros,
    val unresolvedItems: Int,
)

data class DayStat(val date: String, val logged: Boolean, val macros: Macros)

data class PeriodStats(
    val kind: String,
    val start: String,
    val end: String,
    val daysLogged: Int,
    val daysElapsed: Int,
    val totals: Macros,
    val avgPerLoggedDay: Macros?,
    val avgPerDay: Macros?,
    val proteinPct: Double?,
    val carbsPct: Double?,
    val fatPct: Double?,
    val unresolvedItems: Int,
    val perDay: List<DayStat>,
)
