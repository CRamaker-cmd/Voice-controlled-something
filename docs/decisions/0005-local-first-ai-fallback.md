# 0005 — Local-first resolution, AI only as a caching fallback
**Status:** accepted
**Context:** The user asked whether this is doable without AI, and noted that storing nutrition data ourselves is cheaper and faster than asking an AI each time.
**Decision:** Pipeline per spoken item: **rule-based parse → local DB lookup → (optional) AI → cache**. The AI is called only when the DB has no match, the amount is vague ("some pasta") or the measure has no fixed weight ("2 tbsp"). A successful AI answer is converted to per-100 g values and stored as a food with `source='ai'`, so the next mention is local and free. If no AI is configured or it fails, the item is saved as `unresolved` (visible, excluded from totals, fixable via `PUT /items/{id}`).
**Why:** Yes, it is doable without AI for everything that is in the database and expressed in grams/known package sizes. AI is still the best tool for the long tail and vague phrasing, and caching turns each AI call into a one-time cost.
**Consequences:** Match ranking prefers `manual` > `off`/`usda` > `ai`. A user-added manual food always wins. Parsing is deliberately simple (splits on , ; & and/en/plus) — phrases like "mac and cheese" get split and may be unresolved; fixing the parser is cheaper than hiding that.
**Revisit when:** Many unresolved items appear in real use (look at `entry_items.status='unresolved'`).
