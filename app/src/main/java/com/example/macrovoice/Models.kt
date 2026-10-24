package com.example.macrovoice

data class FoodItem(
    val name: String,
    val amount: String,
    val kcal: Double,
    val protein: Double,
    val carbs: Double,
    val fat: Double,
)

data class Meal(
    val id: Long,
    val timeMillis: Long,
    val spoken: String,
    val items: List<FoodItem>,
) {
    val kcal get() = items.sumOf { it.kcal }
    val protein get() = items.sumOf { it.protein }
    val carbs get() = items.sumOf { it.carbs }
    val fat get() = items.sumOf { it.fat }
}
