# Open questions for the owner

Anything in an ADR marked "needs confirmation" is listed here. Agents: read `docs/agents/no-assumptions.md` before changing behaviour in these areas; ask, don't guess.

| # | Question | Current behaviour (placeholder, not a decision) |
|---|----------|------------------------------------------------|
| Q1 | Which sources should the worker ingest? Is Open Food Facts + USDA enough, or do you want NEVO (Dutch generic foods) or retailer-site scraping (legal/ToS implications)? | OFF + USDA only (ADR 0006) |
| Q2 | Which timezone, and is a week Monday–Sunday? | `Europe/Amsterdam`, Monday–Sunday |
| Q3 | Which average do you want to see by default: per *logged* day or per *calendar* day? | Both returned; app shows both |
| Q4 | Are you OK with 1 ml = 1 g for liquids, or should density come from the product? | 1 ml = 1 g, flagged on the item |
| Q5 | Will the server be reachable outside your home network? One user or several? | One user, optional bearer token, cleartext HTTP allowed in the app |
| Q6 | Do you want calorie/macro *goals* (progress vs target)? | Not built |
| Q7 | Should the app confirm low-confidence transcripts instead of logging immediately? | Always logs immediately (ADR 0008) |
| Q8 | Fibre, sugar, salt, micronutrients? | Only kcal, protein, carbs, fat |
