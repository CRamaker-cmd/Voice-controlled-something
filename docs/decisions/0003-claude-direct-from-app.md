# 0003 — Claude API called directly from the app to estimate macros
**Status:** superseded by 0004 and 0005
**Context:** First iteration: fastest path to a working demo.
**Decision:** The app sent the transcript to the Anthropic API with a forced tool call and displayed the result.
**Why it was replaced:** Every entry cost money and latency; the API key lived on the phone; nothing was learned or stored; no server-side stats. It was "the easiest route", not the right architecture.
**Consequences:** Its useful part survives: structured output via a forced tool call, now in `backend/macrovoice/ai.py` as the *fallback* only.
