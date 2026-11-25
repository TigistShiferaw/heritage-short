# Experiments

## E1 – Gemini 2.5 TTS vs 3.8 Flash TTS for Amharic
- **Hypothesis:** 3.8 Flash TTS pronounces Amharic more naturally than 2.5 preview TTS.
- **Change:** Same sentence, same voice (Kore), swapped model.
- **Result:** Latency about 4 s for both (runs.jsonl). Pronunciation: [which sounded more natural, any wrong sounds].

## E2 – Does caching stop repeat model calls?
- **Hypothesis:** Rerunning a stage with no storyboard changes makes zero model calls.
- **Change:** Ran `narration.py` twice in a row; same for `keyframes.py`.
- **Result:** First run: 10 calls. Second run: 10 × "cached", no new lines in runs.jsonl. Same for references and keyframes.
- **Decision:** Hash-based caching for every model stage.

## E3 – Fallback voice consistency (s09)
- **Hypothesis:** A line from the 2.5 fallback will sound noticeably different from the 3.8 lines around it.
- **Change:** Listened to s08 → s09 → s10 in sequence with s09 made by 2.5.

## E4 – FLUX.1 schnell vs FLUX.2 [dev] for keyframes
- **Hypothesis:** Character consistency across 10 shots needs reference images and fixed seeds, which schnell on Cloudflare does not offer.
- **Change:** Switched keyframes to `@cf/black-forest-labs/flux-2-dev` (seed, size, input images). References sent at 496 px because inputs must be under 512×512.
- **Result:** 2 references and 10 keyframes succeeded first time, 11–17 s each. Consistency: [does the grandmother look like the same person across s02–s09? Any shot that drifted?]

## E5 – One grandmother reference for three ages
- **Hypothesis:** Using one reference for her youth (s02–s03) will make her look too old there.
- **Change:** None yet; observed on the contact sheet.



## E7 – Ken Burns motion vs Wan 2.2
- **Hypothesis:** Pan/zoom on a still keyframe is enough for most shots; Wan 2.2 only adds value where something must move (smoke, steam).
- **Change:** All 10 shots with Ken Burns (in, left, out, right in rotation). [s01 and s10 with Wan 2.2 on Kaggle T4.]
- **Result:** Ken Burns: 80s for all clips, no GPU. Wan 2.2:

## E8 – Music: placeholder drone vs ACE-Step score
- **Hypothesis:** A tizita-mode score with krar and masinko makes the ending land harder than the drone.
- **Change:** Same cut, swapped `outputs/music/score.wav`.


## E9 – 9:16 framing: centre crop vs blurred background
- **Hypothesis:** A centre crop of a 16:9 painting loses too much for vertical video.
- **Change:** Rendered the 9:16 film both ways (`--vertical crop` and the default blurred background).
- **Result:** A 9:16 crop of a 1280-wide clip keeps about 405 px of width (32% of the painting) and enlarges it about 2.7×, so it looks soft, and side details like the jebena and cups fall outside the frame. The blurred version keeps the whole painting sharp, with room under it for subtitles.
