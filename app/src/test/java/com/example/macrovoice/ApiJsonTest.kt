package com.example.macrovoice

import org.junit.Assert.*
import org.junit.Test

class ApiJsonTest {
    // Shapes copied from a real response of the backend (see backend/tests/test_api_integration.py).
    private val entryJson = """
        {"id":1,"logged_at":"2026-10-21T10:00:00+00:00","local_date":"2026-10-21","raw_text":"2 loaves of AH volkoren and 3 dragonfruit",
         "items":[
           {"id":1,"name":"Albert Heijn Volkoren brood","amount_text":"2 loaves","grams":1600.0,"kcal":3840.0,"protein":144.0,"carbs":640.0,"fat":48.0,"source":"db","status":"resolved","note":null,"food_id":1},
           {"id":2,"name":"dragonfruit","amount_text":"3","grams":null,"kcal":null,"protein":null,"carbs":null,"fat":null,"source":"unresolved","status":"unresolved","note":"not found in the food database","food_id":null}],
         "totals":{"kcal":3840.0,"protein":144.0,"carbs":640.0,"fat":48.0,"unresolved_items":1}}
    """.trimIndent()

    @Test fun parsesResolvedAndUnresolvedItems() {
        val e = ApiJson.entry(org.json.JSONObject(entryJson))
        assertEquals(2, e.items.size)
        assertEquals(3840.0, e.items[0].macros!!.kcal, 0.001)
        assertNull(e.items[0].note)
        assertTrue(e.items[1].unresolved)
        assertEquals("not found in the food database", e.items[1].note)
        assertEquals(1, e.unresolvedItems)
    }

    @Test fun parsesEntryList() {
        val list = ApiJson.entries("""{"date":"2026-10-21","entries":[$entryJson]}""")
        assertEquals(1, list.size)
    }

    @Test fun parsesStatsWithNullAveragesAndSplit() {
        val s = ApiJson.stats("""
            {"kind":"week","start":"2026-11-02","end":"2026-11-08","days_in_period":7,"days_elapsed":0,"days_logged":0,
             "totals":{"kcal":0.0,"protein":0.0,"carbs":0.0,"fat":0.0},"avg_per_logged_day":null,"avg_per_day":null,
             "macro_split":null,"highest_day":null,"lowest_day":null,"unresolved_items":0,
             "per_day":[{"date":"2026-11-02","logged":false,"kcal":0.0,"protein":0.0,"carbs":0.0,"fat":0.0,"unresolved_items":0}]}
        """.trimIndent())
        assertNull(s.avgPerDay); assertNull(s.avgPerLoggedDay); assertNull(s.proteinPct)
        assertEquals(1, s.perDay.size)
        assertFalse(s.perDay[0].logged)
    }
}
