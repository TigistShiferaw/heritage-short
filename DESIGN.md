# Design

## Audience and intent (written 25 Nov 2026, before any generation)
- **Who:** My family and Ethiopians living abroad, aged roughly 18–40, who grew up with the coffee ceremony but now live far from their grandparents.
- **Where:** Family Telegram group (horizontal 16:9) and TikTok/Instagram Reels (vertical 9:16), mostly on phones, often with the sound off at first, so English subtitles are burned in.
- **What they should feel at the end:** Belonging and a gentle longing; the urge to call their grandmother.
- **What they should understand:** The coffee ceremony is more than a drink: it is how families stay connected across distance and generations.

## Story
- **Logline:** Through the three rounds of one coffee ceremony (abol, tona, bereka), a grandmother's life moves from a crowded village home to a quiet house, and her cup keeps calling her scattered family back.
- **Structure:** Three acts, one per cup. Abol = her youth (s01–s03). Tona = family life (s04–s05). The family leaves (s06–s07). Bereka = blessing across distance (s08–s10).
- **Motif:** The black clay jebena and the rising smoke appear in every act and tie the generations together.
- **Narrator:** A grandchild, speaking in Amharic, looking back.
- **Characters:** Illustrated, generic characters, not modelled on any real person's face or voice (see ETHICS.md).
- **Real family detail:** [One true detail from your family, e.g. a phrase your grandmother says during the ceremony, and which shot it appears in.]

## Shot list
| Shot | Seconds | Cup / act | English line |
|---|---|---|---|
| s01 | 7 | Opening | In our home, every story begins with coffee. |
| s02 | 7 | Abol | When my grandmother was young, she roasted coffee over the fire in her village. |
| s03 | 8 | Abol | The smell of coffee called all the neighbours. This is abol, the first cup. |
| s04 | 7 | Tona | Then her children came. They grew up around the same jebena. |
| s05 | 8 | Tona | Tona, the second cup, was a time of laughter and stories. |
| s06 | 7 | Leaving | One day her children went far away. The house fell silent. |
| s07 | 7 | Leaving | But she never stopped making coffee. |
| s08 | 8 | Bereka | Today her grandchildren join her by phone. |
| s09 | 8 | Bereka | Bereka, the third cup, is the cup of blessing. |
| s10 | 9 | Closing | Even when we are far away, her cup is always waiting for us. |
| End card | 4 | | Made with AI · Gemini TTS, FLUX, Wan 2.2, ACE-Step |

Total: 80 seconds.

## Why every shot exists
Each shot's reason is stored in `storyboard.json` under `reason`, so the design and the pipeline share one source of truth. The validator rejects a shot without a reason.

## Visual design
- **Style:** Warm hand-painted gouache, soft film grain, amber firelight and morning light, terracotta, ochre and deep green. Chosen because it feels like a family storybook, and because an illustrated look forgives small model errors better than photorealism.
- **Consistency:** One reference image per character (`outputs/characters/`), passed to FLUX.2 [dev] as an input image in every shot that character appears in. Fixed seeds per shot.
- **Cultural details checked in every keyframe:** the black clay jebena, small handleless sini cups, green grass on the floor, frankincense smoke, the white netela with a tilet border.
- **Motion:** A slow Ken Burns move per shot (push in, pan left, pull out, pan right, in rotation) so the paintings feel alive without the cost and artefacts of video generation. Optional Wan 2.2 clips replace the shots where something must really move (smoke, steam).
- **Two formats from one keyframe:** The 16:9 film uses the full frame. The 9:16 film shows the same full frame in the middle of a blurred, darkened copy of itself, instead of a centre crop that would keep only a third of each painting (see EXPERIMENTS.md E9).
- **Known compromise:** One grandmother reference serves all three ages, so she may look older than intended in s02–s03 (E5).

## Sound design
- **Narration:** Gemini TTS, prebuilt voice **Kore**, Amharic. Each line starts 0.5 s after its shot begins.
- **Score:** Krar and masinko with soft kebero, tizita mode, 72 bpm, gentle build then calm resolution. Music cues per shot: intro, build, warm, quiet, swell, resolve. [If ACE-Step was not used: placeholder drone, and why.]
- **Mix:** Music is lowered by 14 dB under the voice with 0.25 s ramps, fades in over 1.5 s and out over the last 3 s. Final loudness −14 LUFS for social platforms.
- **Subtitles:** English, white bold with a dark outline, burned in. On 9:16 they sit higher so the TikTok/Reels buttons do not cover them.
- **End card:** 4 s, Amharic title and the AI disclosure, fades in.

## Checkpoints
1. **Radio cut** (`outputs/radio_cut.mp4`, 80 s): narration over a black screen to test story and pacing before any image.
2. **Contact sheet** (`outputs/keyframes/contact_sheet.jpg`): all 10 keyframes reviewed before motion.
3. **Rough cut** (`outputs/rough_cut.mp4`, 80 s): Ken Burns clips with narration.
4. **Final** (`outputs/final/`): subtitles, end card, score, both formats.

## User test 1: radio cut
- **Date / format:** [e.g. 25 Nov, shared on Telegram]
- **People (at least 3 from the audience):** [P1 – who, P2 – who, P3 – who]
- **What they said:** [quotes or notes]
- **What I changed because of it:** [specific edits, or "nothing, because ..."]

## User test 2: rough or final cut
- **Date / format:**
- **People:**
- **What they said:**
- **What I changed:**
