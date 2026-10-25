# 0006 — Open data sources instead of scraping commercial diet apps
**Status:** accepted — **needs user confirmation** (see `docs/open-questions.md` Q1)
**Context:** The user asked for a worker that "scrapes all the famous diet platforms" and mentioned free APIs/repositories.
**Decision:** The worker ingests from open, legitimate sources: **Open Food Facts** (ODbL; contains Albert Heijn/Jumbo/etc. products with per-100 g macros, serving and package sizes; API + official bulk dump) and **USDA FoodData Central** (public domain; generic foods). A `Source` is just an iterator of `FoodRecord`, so adding another is one small module.
**Why:** Commercial apps (MyFitnessPal, Cronometer, Lose It, …) forbid scraping in their terms, are behind logins/anti-bot measures, and their databases are partly user-generated and inconsistent. Open Food Facts already covers the stated use case (Dutch supermarket brands) with a licence that allows this use.
**Not done:** NEVO (Dutch RIVM generic foods database) — excellent for Dutch generic foods but I have not verified its download format/licence; Albert Heijn's own site — scraping retailer sites needs a deliberate decision.
**Consequences:** Attribution: Open Food Facts requires crediting (ODbL) — noted in the README. Rate limits are respected in code (`delay_s`, custom User-Agent). Data is sanity-filtered (`pipeline.sane`); incomplete products are skipped, never filled in.
**Revisit when:** Coverage of the foods actually eaten is poor, then decide with the user on NEVO or other sources.
