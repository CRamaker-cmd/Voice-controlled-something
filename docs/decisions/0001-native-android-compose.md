# 0001 — Native Android app, Kotlin + Jetpack Compose
**Status:** accepted
**Context:** The request was "Android app that you can talk to".
**Decision:** Native Android (Kotlin, Jetpack Compose, Material 3, min SDK 26).
**Why:** Best access to the platform speech recognizer and microphone; no cross-platform requirement was stated. Compose keeps the UI small and testable.
**Consequences:** No iOS. The UI is a thin client: all logic (parsing, lookup, stats) lives in the backend so a second client could be added cheaply.
**Revisit when:** iOS or a web client is requested.
