# 0007 — Portion/unit semantics: nothing is guessed
**Status:** accepted
**Context:** "2 loaves of AH brood" needs a weight. The product, not the app, knows what a loaf or a slice weighs.
**Decision:**
- g/kg → grams. ml/cl/dl/l → grams at **1 ml = 1 g** (approximation, flagged in the item `note`).
- Serving-like units (slice, piece, portie, bare count "2 bananas") → the product's `serving_g`.
- Package-like units (loaf, pak, bottle, blik) → the product's `package_g`.
- Culinary measures (tbsp, cup, glass, bowl, handful) and vague words ("some", "wat") have no fixed weight → AI fallback, or `unresolved`.
- If the product lacks the needed size, the item is `unresolved` with the reason; we never substitute a default.
**Why:** The project rule is to never invent data. A wrong silent default (e.g. "a slice = 35 g") corrupts totals invisibly; an unresolved item is visible and fixable.
**Consequences:** More items need a manual correction or AI than with defaults. The density approximation is the one accepted inexactness (milk 1.03, oil 0.92) — see open questions Q4.
**Revisit when:** Unresolved items due to missing sizes dominate; then consider a curated, versioned table of generic sizes *approved by the user*.
