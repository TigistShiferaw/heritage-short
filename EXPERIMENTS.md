# Experiments

## E1 – Gemini 2.5 TTS vs 3.8 Flash TTS for Amharic
- **Hypothesis:** 3.8 Flash TTS pronounces Amharic more naturally than 2.5 preview TTS.
- **Change:** Same sentence, same voice (Kore), swapped model.
- **Result:** Latency about 4 s for both (runs.jsonl). Pronunciation: [which sounded more natural, any wrong sounds].
- **Decision:** Use 3.8 Flash TTS as primary, 2.5 as fallback, because [...].

## E2 – Does caching stop repeat model calls?
- **Hypothesis:** Rerunning narration with no storyboard changes makes zero model calls.
- **Change:** Ran pipeline/narration.py twice in a row.
- **Result:** First run: 10 calls. Second run: 10 × "cached", 0 regenerated, no new lines in runs.jsonl.
- **Decision:** Keep hash-based caching (hash of text + voice + model) for every stage.

## E3 – Fallback voice consistency (s09)
- **Hypothesis:** A line from the 2.5 fallback will sound noticeably different from the 3.8 lines around it.
- **Change:** s09 made with 2.5 TTS after the 3.8 quota ran out. Listened to s08 → s09 → s10 in sequence.
- **Result:** [Did you notice a voice change? Big or small?]
- **Decision:** [e.g. rerun s09 with 3.8 after the quota resets / acceptable as is].
