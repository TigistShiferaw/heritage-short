# Ethics

## Real people: consent
- No real person's face, likeness or voice appears in the film.
- The grandmother and the children are **generic illustrated characters** generated from text descriptions. They were not prompted with, or modelled on, any photo of a real person.
- The narration uses Gemini TTS's **prebuilt voice "Kore"**. No voice was cloned.
- So no consent form is required. If a future version uses a relative's photo or voice, I will get their written consent first and record it here, including what they agreed to and how they can withdraw.

## Whose story
The story is a composite of the Ethiopian coffee ceremony as many families practise it, not a documentary about one person. Permission to include a true family detail was reported, but the exact detail and whose permission it was still need to be recorded before adding it to the storyboard.

## Cultural representation
- The coffee ceremony is sacred and social. I checked every keyframe for the details that matter: the clay jebena, sini cups, grass on the floor, frankincense, and the three rounds in the right order (abol, tona, bereka).
- Image models tend to produce generic "African" imagery. I described Ethiopian specifics in every prompt (netela with tilet border, highland home) and rejected keyframes that drifted. After viewer feedback that the jebena looked modern and inconsistent, I revised six prompts and added a shared object reference; the reference-based rerender is pending because the Cloudflare daily allocation was exhausted.
- The narration is Amharic from a TTS model. A neighbor praised the story, but no specific pronunciation check has been recorded.
- Known risk: one ceremony and one family cannot represent every Ethiopian community. The film says "our home", not "all Ethiopians".

## AI disclosure
- The film ends with a 4-second card: "Made with AI · Gemini TTS, FLUX.2". The final cut uses Gemini TTS, FLUX.2 and FFmpeg/Ken Burns; Wan 2.2 and ACE-Step were not used.
- When publishing, enable the platform's AI label and disclose in the post that the film is AI-generated.

## Data and keys
- API keys live only in `.env`, which `.gitignore` excludes. They were never committed or pasted into chats (F4 describes how a misnamed `.gitignore` was caught before the first commit).
- No personal data is sent to the models beyond the prompts in `storyboard.json`.
- Google states that content submitted through its unpaid Gemini services may be used to improve products and may be reviewed by people. Do not add sensitive or identifying family details to unpaid prompts.
- Cloudflare identifies its hosted FLUX.2 [dev] endpoint as zero-data-retention and links to Black Forest Labs' terms. Those terms describe possible use of content for service improvement/training and an opt-out; confirm which terms govern this specific Cloudflare endpoint before submitting sensitive material. The current prompts and reference images are fictional/generic.

## Licences and terms
Terms checked against the providers' published pages on 2026-11-26; this is a project record, not legal advice.

| Component | Licence / terms reviewed | Project note |
|---|---|---|
| Gemini TTS / text (Google AI Studio) | [Gemini API Additional Terms](https://ai.google.dev/gemini-api/terms) and [pricing](https://ai.google.dev/gemini-api/docs/pricing) | Generated-content ownership remains with the user under the terms; unpaid-tier data use is described above. |
| FLUX.2 [dev] via Cloudflare Workers AI | [Cloudflare model page](https://developers.cloudflare.com/workers-ai/models/flux-2-dev/) links to [Black Forest Labs' terms](https://bfl.ai/legal/terms-of-service); see also [Cloudflare pricing](https://developers.cloudflare.com/workers-ai/platform/pricing/) | Cloudflare labels the endpoint zero-data-retention. Black Forest Labs' linked terms state content may be used to improve/train services and describe an opt-out. Confirm the endpoint-specific terms and whether the intended publication remains non-commercial. |
| FFmpeg (Gyan build) | [FFmpeg legal and licensing page](https://ffmpeg.org/legal.html); installed build flags include `--enable-gpl --enable-version3` | This is a GPL-enabled build. The project uses FFmpeg as a local tool and does not redistribute its binaries. |

Wan 2.2 and ACE-Step 1.5 are optional pipeline upgrades and were not used in the current final cut; their terms are not represented as checked here.
