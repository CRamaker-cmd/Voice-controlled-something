from datetime import date

import pytest

from macrovoice.stats import build_stats, period_bounds


def add(conn, day, kcal, p=0, c=0, f=0, status="resolved"):
    with conn:
        eid = conn.execute("INSERT INTO entries (logged_at, local_date, raw_text) VALUES (?,?,?) RETURNING id",
                           (f"{day}T10:00:00+00:00", day, "x")).fetchone()[0]
        conn.execute("INSERT INTO entry_items (entry_id, position, name, amount_text, kcal, protein, carbs, fat, source, status)"
                     " VALUES (?,?,?,?,?,?,?,?,?,?)", (eid, 0, "i", "1", kcal, p, c, f, "manual", status))


def test_bounds():
    assert period_bounds("day", date(2026, 10, 21)) == (date(2026, 10, 21),) * 2
    assert period_bounds("week", date(2026, 10, 21)) == (date(2026, 10, 19), date(2026, 10, 25))
    assert period_bounds("week", date(2026, 10, 25)) == (date(2026, 10, 19), date(2026, 10, 25))  # Sunday
    assert period_bounds("month", date(2026, 2, 10)) == (date(2026, 2, 1), date(2026, 2, 28))
    with pytest.raises(ValueError):
        period_bounds("year", date(2026, 1, 1))


def test_week_totals_averages_and_extremes(conn):
    add(conn, "2026-10-19", 2000, 100, 200, 60)
    add(conn, "2026-10-19", 500, 20, 50, 10)
    add(conn, "2026-10-21", 1500, 80, 150, 50)
    s = build_stats(conn, "week", date(2026, 10, 21), today=date(2026, 10, 21))
    assert s["totals"] == {"kcal": 4000.0, "protein": 200.0, "carbs": 400.0, "fat": 120.0}
    assert (s["days_logged"], s["days_elapsed"], s["days_in_period"]) == (2, 3, 7)
    assert s["avg_per_logged_day"]["kcal"] == 2000.0           # 4000 / 2 logged days
    assert s["avg_per_day"]["kcal"] == pytest.approx(1333.3)    # 4000 / 3 elapsed days (Mon-Wed)
    assert s["highest_day"]["date"] == "2026-10-19" and s["lowest_day"]["date"] == "2026-10-21"
    assert [p["logged"] for p in s["per_day"]] == [True, False, True, False, False, False, False]
    assert s["macro_split"] == {"protein_pct": 23.0, "carbs_pct": 46.0, "fat_pct": 31.0}  # 800/1600/1080 kcal of 3480


def test_unresolved_items_are_counted_but_not_summed(conn):
    add(conn, "2026-10-21", 100)
    add(conn, "2026-10-21", None, status="unresolved")
    s = build_stats(conn, "day", date(2026, 10, 21), today=date(2026, 10, 21))
    assert s["totals"]["kcal"] == 100 and s["unresolved_items"] == 1


def test_empty_period_and_future_period(conn):
    s = build_stats(conn, "month", date(2026, 10, 1), today=date(2026, 10, 21))
    assert s["days_logged"] == 0 and s["avg_per_logged_day"] is None and s["macro_split"] is None
    assert s["highest_day"] is None and s["avg_per_day"]["kcal"] == 0.0 and s["days_elapsed"] == 21
    future = build_stats(conn, "week", date(2026, 11, 2), today=date(2026, 10, 21))
    assert future["days_elapsed"] == 0 and future["avg_per_day"] is None


def test_past_period_divides_by_full_length(conn):
    add(conn, "2026-09-10", 3000)
    s = build_stats(conn, "month", date(2026, 9, 15), today=date(2026, 10, 21))
    assert s["days_elapsed"] == 30 and s["avg_per_day"]["kcal"] == 100.0
