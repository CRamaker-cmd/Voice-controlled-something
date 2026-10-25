# 0009 — Diary dates, week/month definitions and average semantics
**Status:** accepted — **needs confirmation** (open questions Q2, Q3)
**Decision:**
- Each entry stores its UTC instant and its **local date** in the server timezone (`MACROVOICE_TZ`, default `Europe/Amsterdam`) at log time. Day/week/month queries use the stored local date (indexed), so past data does not move if the timezone setting changes later.
- Week = ISO week, **Monday–Sunday**. Month = calendar month.
- Two averages are always returned: `avg_per_logged_day` (total ÷ days that have entries) and `avg_per_day` (total ÷ days elapsed so far in the period, today included; full length for past periods; `null` for future periods). They answer different questions, so the API does not choose one.
- Macro split is by energy (protein/carbs 4 kcal/g, fat 9 kcal/g).
- Unresolved items are excluded from totals and counted separately (`unresolved_items`) so totals are never silently wrong.
**Why:** The user asked for day/week/month totals and averages without defining them; returning both averages avoids deciding for them.
