# Efficient context building

1. `AGENTS.md` → context map → the one or two docs/ADRs relevant to the task.
2. Locate code with grep/glob on symbols; read the function and its test, not whole modules.
3. Tests document behaviour: `test_parser.py` (grammar), `test_resolver.py` (lookup/AI/caching rules), `test_api_integration.py` (end-to-end contracts), `test_stats.py` (period semantics).
4. Don't load `backend/tests/` fixtures, generated files, or the Android build files unless the task touches them.
5. Write down new durable knowledge where the next agent will look (ADR, README, this folder) — not in chat only.
