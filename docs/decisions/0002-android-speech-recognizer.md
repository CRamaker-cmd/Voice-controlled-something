# 0002 — Android's built-in SpeechRecognizer for voice
**Status:** accepted
**Context:** Need speech-to-text for rough utterances, in Dutch and English, with brand names ("Albert Heijn").
**Decision:** Use `android.speech.SpeechRecognizer` (free, on-device/Google service), language switchable between `en-US` and `nl-NL`.
**Why:** No cost, no extra backend dependency, partial results for live feedback. Alternatives (Whisper on the server, cloud STT) add cost/latency and can be swapped in later because the backend only receives text.
**Consequences:** Recognition quality for brand names depends on the Google service; the transcript is editable and the backend resolver tolerates imperfect text. Mixed-language sentences are not handled specially.
**Revisit when:** Brand names are routinely mis-transcribed (then evaluate server-side Whisper).
