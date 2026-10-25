# 0010 — Single-user, bearer-token auth, LAN/VPN deployment
**Status:** accepted — **needs confirmation** (open question Q5)
**Decision:** One implicit user. If `MACROVOICE_API_TOKEN` is set, every endpoint except `/health` requires `Authorization: Bearer <token>` (constant-time compare). The Android app allows cleartext HTTP so it can talk to a LAN address; HTTPS/VPN (e.g. Tailscale, reverse proxy) is recommended whenever the server is reachable beyond the home network.
**Why:** Smallest thing that keeps a self-hosted personal server from being open. No user tables means no migration burden if we later add users.
**Consequences:** No multi-user. Token is stored in app preferences (plain SharedPreferences).
**Revisit when:** A second user or public exposure is needed.
