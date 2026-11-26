# Experiments

## E1 – Gemini 2.5 TTS vs 3.8 Flash TTS for Amharic
- **Hypothesis:** 3.8 Flash TTS pronounces Amharic more naturally than 2.5 preview TTS.
- **Change:** Same sentence, same voice (Kore), swapped model.
- **Result:** Both models produced speech; the latency is recorded in `runs.jsonl`. No documented side-by-side pronunciation assessment exists, so the quality hypothesis remains unproven.

## E2 – Does caching stop repeat model calls?
- **Hypothesis:** Rerunning a stage with no storyboard changes makes zero model calls.
- **Change:** Ran `narration.py` twice in a row; same for `keyframes.py`.
- **Result:** First run: 10 calls. Second run: 10 × "cached", no new lines in runs.jsonl. Same for references and keyframes.
- **Decision:** Hash-based caching for every model stage.

## E3 – Fallback voice consistency (s09)
- **Hypothesis:** A line from the 2.5 fallback will sound noticeably different from the 3.8 lines around it.
- **Change:** Listened to s08 → s09 → s10 in sequence with s09 made by 2.5.
- **Result:** No listening notes were recorded; s09 was later regenerated with the primary model. This comparison is incomplete.

## E4 – FLUX.1 schnell vs FLUX.2 [dev] for keyframes
- **Hypothesis:** Character consistency across 10 shots needs reference images and fixed seeds, which schnell on Cloudflare does not offer.
- **Change:** Switched keyframes to `@cf/black-forest-labs/flux-2-dev` (seed, size, input images). References sent at 496 px because inputs must be under 512×512.
- **Result:** Two character references and ten initial keyframes succeeded. A later viewer reported that the jebena varied between shots; repeated text prompts improved its traditional shape but did not make it identical, motivating the shared prop reference experiment (E11). No FLUX.1-vs-FLUX.2 image quality comparison was run.

## E5 – One grandmother reference for three ages
- **Hypothesis:** Using one reference for her youth (s02–s03) will make her look too old there.
- **Change:** Reviewed the contact sheet; no age-specific reference was generated.
- **Result:** The grandmother in s02 appears older than the intended age of about 20. This compromise remains.

## E6 – Gemini TTS quota and fallback
- **Hypothesis:** The primary free-tier TTS model may not complete all ten narration calls in one run.
- **Change:** Generated narration with the 3.8 model and configured the 2.5 preview fallback when quota errors occurred.
- **Result:** `runs.jsonl` records four failed 3.8 TTS calls and four successful fallback calls; later retries produced primary-model clips for s08 and s09.
- **Decision:** Keep the fallback chain and cache clips by the model actually used.


## E7 – Ken Burns motion vs Wan 2.2
- **Hypothesis:** Pan/zoom on a still keyframe is enough for most shots; Wan 2.2 only adds value where something must move (smoke, steam).
- **Change:** Rendered all ten shots with Ken Burns. No Wan 2.2 clips were generated.
- **Result:** The local motion pipeline produced all ten clips without GPU use, but Wan was not tested, so the visual-quality comparison remains unproven.
- **Decision:** Keep Ken Burns as the reliable fallback; do not claim a Wan comparison.

## E8 – Music: placeholder drone vs ACE-Step score
- **Hypothesis:** A tizita-mode score with krar and masinko makes the ending land harder than the drone.
- **Change:** No ACE-Step score was generated or placed at `outputs/music/score.wav`; the final used the placeholder drone.
- **Result:** No comparison was performed. The original-score requirement remains outstanding.
- **Next step:** Generate/select an original score, then compare it against the placeholder and record the result.


## E9 – 9:16 framing: centre crop vs blurred background
- **Hypothesis:** A centre crop of a 16:9 painting loses too much for vertical video.
- **Change:** Rendered the 9:16 film both ways (`--vertical crop` and the default blurred background).
- **Result:** A 9:16 crop of a 1280-wide clip keeps about 405 px of width (32% of the painting) and enlarges it about 2.7×, so it looks soft, and side details like the jebena and cups fall outside the frame. The blurred version keeps the whole painting sharp, with room under it for subtitles.

## E10 – Decode Gemini TTS audio before wrapping it
- **Hypothesis:** The narration scratch came from abrupt clip edges and could be removed with fades alone.
- **Change:** Inspected the cached TTS payload after the fades did not resolve the reported sound.
- **Result:** The audio data began with a RIFF/WAVE header; it was a WAV file being treated as raw PCM and wrapped in a second WAV. Decoding the inner 24 kHz, 16-bit mono audio removed the header and trailing metadata from playback. Cached clips were repaired without new API calls, and both final formats were rebuilt.
- **Decision:** Decode TTS audio containers before writing canonical WAVs; retain short fades only for boundary clicks.

## E11 – Shared jebena image reference
- **Hypothesis:** Passing the same jebena image reference to every shot that shows the pot will improve prop consistency beyond repeating a text description.
- **Change:** Added a `props` section to the storyboard contract and support for prop image references in keyframe generation. Cropped a reference from s10 and added it to the six relevant shots.
- **Result:** The first prompt-only revision made all six pots traditional black clay, but their shapes still vary. The reference-based rerender is pending: Cloudflare returned HTTP 429 for the reference-generation request after its daily free allocation was exhausted.
- **Next step:** Rerun `python pipeline\\run_all.py` after the Cloudflare quota resets, then inspect the contact sheet and record whether the object is consistent.
