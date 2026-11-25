# Failures

## F1 – Gemini 2.5 Flash retired (25 Nov 2026)
- **What broke:** Smoke test text call returned 404: "gemini-2.5-flash is no longer available to new users", even though it still appears in the models list.
- **What I tried:** Read the error message; it named the replacement. Listed all available models via the API (saved in outputs/available_models.txt).
- **Fix:** Set GEMINI_TEXT_MODEL=gemini-3.8-flash and GEMINI_TTS_MODEL=gemini-3.8-flash-tts in .env. Model names live in .env so changes need no code edits.
- **Lesson:** A model being listed does not mean it is usable; the smoke test caught this early.

## F2 – Gemini 3.8 Flash 503 "high demand" (25 Nov 2026, 07:45)
- **What broke:** Text call returned 503 UNAVAILABLE; TTS and Cloudflare worked.
- **What I tried:** Added post_with_retry() with exponential backoff on 429/5xx. All 5 attempts still failed (184 s).
- **Fix:** Added a fallback chain 3.8 → 3.7 → 3.5 Flash, and removed the wasted sleep after the final attempt.
- **Lesson:** Free-tier models fail intermittently; retries alone are not enough, you need a fallback.

## F3 – Retry helper called itself (25 Nov 2026)
- **What broke:** TypeError "multiple values for keyword argument 'timeout'".
- **Cause:** Find-and-replace of requests.post also changed the line inside post_with_retry, so it recursed.
- **Fix:** Restored requests.post inside the helper; it is now the only place requests.post is used.
- **Lesson:** Review find-and-replace results instead of replacing blindly.
