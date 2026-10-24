# MacroVoice

Android app: say what you ate, roughly ("2 loaves of Albert Heijn volkoren and a Jumbo pindakaas"),
and it estimates calories, protein, carbs and fat.

- Speech-to-text: Android's built-in `SpeechRecognizer` (English or Dutch, set in Settings).
- Estimation: Claude via the Anthropic Messages API (forced tool call → structured JSON).
- Storage: on-device only; the daily log lives in SharedPreferences.

## Run
1. Open this folder in Android Studio (it will create the Gradle wrapper and sync).
2. Run on a device/emulator with Google speech services.
3. In Settings, paste your Anthropic API key (console.anthropic.com).

The key is stored on-device and sent only to api.anthropic.com. Estimates are rough — the
model guesses portion sizes and product macros; edit the transcript and re-run if it misheard.
