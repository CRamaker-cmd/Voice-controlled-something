# Decision log (ADRs)

One file per decision: **context → decision → why → consequences → when to revisit**.
Rules for changing them are in `docs/agents/decisions.md`. Statuses: `accepted`, `superseded by NNNN`, `proposed`.

| # | Decision | Status |
|---|----------|--------|
| 0001 | Native Android app, Kotlin + Jetpack Compose | accepted |
| 0002 | Android's built-in SpeechRecognizer for voice | accepted |
| 0003 | Claude API called directly from the app to estimate macros | superseded by 0004, 0005 |
| 0004 | Self-hosted backend: Python + FastAPI + SQLite (FTS5) | accepted |
| 0005 | Local-first resolution, AI only as a caching fallback | accepted |
| 0006 | Open data sources instead of scraping commercial diet apps | accepted (needs user confirmation, see open questions) |
| 0007 | Portion/unit semantics: nothing is guessed | accepted |
| 0008 | Recording = one action: no "estimate" button | accepted |
| 0009 | Diary dates, week/month definitions and average semantics | accepted (needs confirmation) |
| 0010 | Single-user, bearer-token auth, LAN/VPN deployment | accepted (needs confirmation) |
| 0011 | Test strategy: unit + integration with fakes at the HTTP boundary | accepted |
