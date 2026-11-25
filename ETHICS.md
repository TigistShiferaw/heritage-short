# Ethics

## Real people: consent
- No real person's face, likeness or voice appears in the film.
- The grandmother and the children are **generic illustrated characters** generated from text descriptions. They were not prompted with, or modelled on, any photo of a real person.
- The narration uses Gemini TTS's **prebuilt voice "Kore"**. No voice was cloned.
- So no consent form is required. If a future version uses a relative's photo or voice, I will get their written consent first and record it here, including what they agreed to and how they can withdraw.

## Whose story
The story is a composite of the Ethiopian coffee ceremony as many families practise it, not a documentary about one person. [If you added a real family detail: whose it is, and that they agreed to it being shared.]

## Cultural representation
- The coffee ceremony is sacred and social. I checked every keyframe for the details that matter: the clay jebena, sini cups, grass on the floor, frankincense, and the three rounds in the right order (abol, tona, bereka).
- Image models tend to produce generic "African" imagery. I described Ethiopian specifics in every prompt (netela with tilet border, highland home) and rejected keyframes that drifted. [Note any keyframe you regenerated and why.]
- The narration is Amharic from a TTS model. [Who checked the pronunciation, and what they said.]
- Known risk: one ceremony and one family cannot represent every Ethiopian community. The film says "our home", not "all Ethiopians".

## AI disclosure
- The film ends with a 4-second card: "Made with AI · Gemini TTS, FLUX, Wan 2.2, ACE-Step". The card lists only tools used in the final cut; if Wan 2.2 or ACE-Step are not used, `end_card.text` in `storyboard.json` is edited before the final render.
- The public post also says the film is AI-generated.

## Data and keys
- API keys live only in `.env`, which `.gitignore` excludes. They were never committed or pasted into chats (F4 describes how a misnamed `.gitignore` was caught before the first commit).
- No personal data is sent to the models beyond the prompts in `storyboard.json`.

## Licences and terms
| Component | Licence / terms | Checked |
|---|---|---|
| Gemini TTS (Google AI Studio) | Gemini API terms of service | [ ] |
| FLUX.2 [dev] via Cloudflare Workers AI | Model licence on the Cloudflare / Black Forest Labs page | [ ] |
| Wan 2.2 | Licence on its model card | [ ] |
| ACE-Step 1.5 | Licence in its GitHub repo | [ ] |
| FFmpeg (Gyan build) | GPL | [ ] |
