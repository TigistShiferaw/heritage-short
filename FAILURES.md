# Failures

## F1 – Gemini 2.5 Flash retired (25 Nov 2026)
- **What broke:** Smoke test text call returned 404: "gemini-2.5-flash is no longer available to new users", although it still appears in the models list.
- **What I tried:** Read the error, which named the replacement. Listed all available models via the API (`outputs/available_models.txt`).
- **Fix:** Set `GEMINI_TEXT_MODEL=gemini-3.8-flash` and `GEMINI_TTS_MODEL=gemini-3.8-flash-tts` in `.env`. Model names live in `.env`, so changes need no code edits.
- **Lesson:** Being listed does not mean usable; the smoke test caught it early.

## F2 – Gemini 3.8 Flash 503 "high demand" (25 Nov 2026, 07:45)
- **What broke:** Text call returned 503 UNAVAILABLE; TTS and Cloudflare worked.
- **What I tried:** Added `post_with_retry()` with exponential backoff on 429/5xx. All 5 attempts still failed (184 s).
- **Fix:** Fallback chain 3.8 → 3.7 → 3.5 Flash, and no sleep after the final attempt.
- **Result:** 25 Nov 08:03: 3.8 and 3.7 returned 503, 3.5 Flash succeeded in 10.3 s.
- **Lesson:** Free-tier models fail intermittently; retries alone are not enough, you need a fallback.

## F3 – Retry helper called itself (25 Nov 2026)
- **What broke:** TypeError "multiple values for keyword argument 'timeout'".
- **Cause:** Find-and-replace of `requests.post` also changed the line inside `post_with_retry`, so it recursed.
- **Fix:** Restored `requests.post` inside the helper; it is now the only place it is used.
- **Lesson:** Review find-and-replace results instead of replacing blindly.

## F4 – .gitignore not applied (25 Nov 2026)
- **What broke:** `git status` showed the whole `.venv` folder staged for the first commit, and `.env` with my keys was at risk.
- **Cause:** The file was named `gitignore`, without the leading dot.
- **Fix:** `git rm -r --cached .`, recreated the file with `Set-Content -Path .gitignore -Encoding ascii`, checked `git status` before committing. Nothing leaked.
- **Lesson:** Always read `git status` before the first commit.

## F5 – TTS fallback clips cached under the wrong model (25 Nov 2026)
- **What broke:** The free-tier 429 hit on s08–s10. The fallback to 2.5 TTS rescued s08 and s09, but they were cached as if made by 3.8, so a rerun would never replace them and the film would mix two voices.
- **Fix:** Cache each clip under the model actually used, so a rerun retries fallback clips with the primary model. Added a 7-second pause between TTS calls (`TTS_PAUSE_S`).
- **Result:** On the rerun s08 was regenerated in the 3.8 voice; the other shots stayed cached.
- **Lesson:** A cache key must describe what was really produced, not what was requested.

## F6 – Gemini 3.8 TTS daily quota (25 Nov 2026, about 09:00)
- **What broke:** Every retry of s09 returned 429 "exceeded your current quota", even a minute apart.
- **Diagnosis:** Failures a minute apart point to a daily limit, not per-minute. [Confirm with the limit shown in AI Studio → Usage / Rate limits.]
- **Fix:** Kept s09 in the 2.5 fallback voice for the radio cut so work could continue, and reran `narration.py` after the quota reset. [Record whether s09 is now in the 3.8 voice.]
- **Lesson:** Generate narration early, and log the full error text to see which quota was hit.

## F7 – FFmpeg not found by the motion stage (25 Nov 2026, about 11:50)
- **What broke:** `motion_kenburns.py` crashed with `FileNotFoundError: [WinError 2]` when calling ffmpeg.
- **What I tried:** `where.exe ffmpeg` found nothing, so I installed it with `winget install Gyan.FFmpeg`. It still failed: the terminal had the old PATH, and I had written the variable as the string `"FFMPEG"` instead of `FFMPEG`.
- **Fix:** Scripts find FFmpeg through the `FFMPEG` env variable, then PATH, then `imageio-ffmpeg`. Fixed the quoted string and reloaded PATH.
- **Result:** All 10 clips rendered; rough cut built at 80.0 s.
- **Lesson:** Installers that change PATH need a new shell. Resolve external tools in one helper.

## F8 – 9:16 render failed on pixel aspect ratio (25 Nov 2026)
- **What broke:** While testing `assemble.py` with stand-in clips, the 16:9 film rendered but the 9:16 one failed: "Input link parameters (size 270x480, SAR 1:1) do not match the corresponding output link (SAR 1280:1281)". FFmpeg wrote a 0-byte file.
- **Cause:** Scaling with `scale=-2` rounds the width to an even number, which leaves a tiny non-square pixel aspect ratio, and `concat` refuses to join it with the square-pixel end card.
- **Fix:** Added `setsar=1` after every scale, crop and overlay in the 9:16 branch. Both formats then rendered at exactly 80.0 s.
- **Lesson:** Test every output format, not just the first; normalise SAR before `concat`.

## F9 – Scratching noise at narration starts (26 Nov 2026)
- **What broke:** The final mix had a short scratch at the start of every narration clip.
- **Cause:** Gemini TTS `inlineData` contained a WAV container, but `narration.py` treated the container bytes as raw PCM and wrote them into another WAV. The embedded RIFF/WAVE header and trailing metadata were therefore played as audio.
- **Fix:** Decode the returned WAV and write only its 24 kHz, 16-bit, mono PCM samples. Detect and repair affected cached clips in place, without regenerating them. Keep 20 ms fades at clip edges to prevent boundary clicks.
- **Result:** Repaired all cached narration clips and rebuilt both final aspect ratios; the storyboard check and FFmpeg decode checks passed.
- **Lesson:** Verify the actual encoding/container of model audio responses before wrapping or mixing them.

## F10 – Cloudflare free allocation blocked prop-reference rerender (26 Nov 2026)
- **What broke:** The request to generate a dedicated jebena reference returned HTTP 429 after the daily free neuron allocation was exhausted.
- **What I tried:** Retried with exponential backoff; the quota error persisted. Used a crop of the existing s10 keyframe as a local reference instead, so no additional API request is needed to create the reference asset.
- **Status:** The storyboard and keyframe stage now pass that reference to all six jebena shots, but the final keyframes have not yet been rerendered with it.
- **Next step:** Rerun `python pipeline\\run_all.py` after the quota resets and review the contact sheet.
- **Lesson:** Backoff does not solve a daily allocation limit; keep a local reference-based fallback and resume when quota resets.

