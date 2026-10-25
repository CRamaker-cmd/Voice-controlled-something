# 0008 — Recording = one action, no "estimate" button
**Status:** accepted
**Context:** The user wants to just record: it should start processing immediately and add an entry.
**Decision:** The app submits the transcript to `POST /entries` as soon as speech recognition finishes (and on "send" for typed text). The call is synchronous and returns the completed entry. There is no preview/confirm step; corrections happen afterwards (delete the entry, or `PUT /items/{id}`).
**Why:** Lowest friction. Since results are cached and mostly local, latency is low; only AI fallback is slow.
**Consequences:** A mis-heard transcript creates a wrong entry that must be deleted. Mitigated by showing the transcript and matched product names on each entry. Entries default to *now* (today) unless `logged_at` is given.
**Revisit when:** Mis-transcription is frequent (consider an undo toast or confirm-on-low-confidence).
