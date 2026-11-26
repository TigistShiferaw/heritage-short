# Costs and performance

The run log records **$0.00 in provider charges** for the calls below. This is the logged charge, not an invoice; check the Google AI Studio and Cloudflare dashboards before claiming the account's final billed total.

## Calls recorded in `runs.jsonl`

| Stage | Provider / model | Successful | Failed | Notes |
|---|---|---:|---:|---|
| Smoke test | Gemini text (3.5 / 3.7 / 3.8 Flash) | 1 | 5 | 3.8 and 3.7 returned intermittent HTTP 503; 3.5 succeeded. |
| Smoke test | Cloudflare FLUX.1 schnell | 4 | 0 | Four-step smoke generations. |
| Smoke test | Gemini TTS (3.8 Flash / 2.5 Flash preview) | 4 | 0 | Three 3.8 calls and one fallback call. |
| Narration | Gemini 3.8 Flash TTS | 10 | 4 | Four primary attempts returned HTTP 429 quota errors. |
| Narration | Gemini 2.5 Flash preview TTS | 4 | 0 | Fallback succeeded for all four fallback attempts. |
| Keyframes | Cloudflare FLUX.2 [dev] | 16 | 0 | Ten initial frames and six prompt-only revisions. |
| Character references | Cloudflare FLUX.2 [dev] | 2 | 0 | Grandmother and children references. |
| Shared jebena reference | Cloudflare FLUX.2 [dev] | 0 | 1 | Request failed with the daily allocation exhausted; the local crop did not use an API call. |
| Motion | FFmpeg / Ken Burns | 10 clips | — | Local render; per-stage latency is not recorded. |
| Score / hero motion | ACE-Step / Wan 2.2 | 0 | 0 | Neither was used in the delivered cut. |
| Assembly | FFmpeg | 15 | 0 | Five mixes and five renders of each aspect ratio. |

Cloudflare Workers AI documents a free allocation of 10,000 Neurons per day, then $0.011 per 1,000 Neurons on a paid plan. The reference request failed at this daily limit. No paid upgrade or paid inference was authorized.

## List-price equivalent estimate

Cloudflare's [current FLUX.2 [dev] pricing](https://developers.cloudflare.com/workers-ai/platform/pricing/) is $0.00021 per 512×512 input tile per step and $0.00041 per 512×512 output tile per step. Using the logged 25 steps, 1360×768 outputs (estimated as six 512×512 tiles), 17 input-reference uses (one tile each), and two 1024×1024 reference outputs (four tiles each), the **estimated image-generation equivalent is about $1.16**:

- Keyframe outputs: 16 × 6 × 25 × $0.00041 = $0.984
- Input references: 17 × 1 × 25 × $0.00021 = $0.089
- Character-reference outputs: 2 × 4 × 25 × $0.00041 = $0.082

This is a rate-based estimate, not the amount billed or confirmed Neuron usage. It assumes tile counts from the requested dimensions; confirm against the Cloudflare dashboard if exact billed usage is needed.

Google calls used the unpaid tier and were logged at $0.00. A paid-tier equivalent for the TTS/text calls is **not calculated**: the log has text character counts, but not the billable audio/token usage needed for a reliable estimate. Pricing depends on the exact model and billing tier; see [Google's Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing).

## Latency

| Stage / output | Successful-call latency |
|---|---:|
| Gemini 3.8 Flash TTS | 4.98 s average (10 calls) |
| Gemini 2.5 Flash preview TTS fallback | 4.69 s average (4 calls) |
| FLUX.2 [dev] keyframes, 1360×768 at 25 steps | 14.59 s average (16 calls; range 11.36–20.76 s) |
| Character references, 1024×1024 at 25 steps | 11.29 s average (2 calls) |
| Latest 16:9 assembly | 158.84 s |
| Latest 9:16 assembly | 169.82 s |

The five logged assembly runs averaged 124.81 s for 16:9 and 151.37 s for 9:16. Motion-render and full-pipeline durations are not currently logged.

## Lessons

- Caching saves quota: after the six revised prompts, only those keyframes needed regeneration.
- Keep a TTS fallback; the primary model returned quota errors during narration generation.
- The Cloudflare daily allocation blocked the shared-prop rerender. The current final exports therefore use the prompt-revised frames, not frames conditioned on the shared jebena reference.
- Local FFmpeg stages can be rerun without provider inference charges, but their compute time is still real and is not included in the API estimate.
