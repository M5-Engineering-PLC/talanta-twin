# Finished drone 01: the final design from the drone viewpoints

This folder shows the D01, D02 and D03 drone cameras in the **finished** state: the final design with lawns, planted plazas, palms, pitches and forecourt. These are not the **asbuilt** construction-site ground that the drone checks use.

- The asbuilt state stays only as the test against the 2026 construction footage (ground_fix_01, context_fix_01, followup_01).
- The finished state is the look for the landing stills, the web bundle and anything public.

No reference frames are used here; these are renders only.

## Renders (1080p, Cycles, 128 samples, look layer on, `step_FE`)

- **Light:** `daylight_landing` (10:30, the L07 light), so the drone views read as the same final scene as the landing stills.
- **Exposure:** -1.2 EV, the preset value, for all three cameras.
  - It is forced with a pre-script, because D02 carries a -1.1 EV camera offset for its dark frame day (followup_01).
  - That offset belongs to the frame match, not to the final look.

| Render | Camera | Time |
|---|---|---|
| D01_daylight_landing_hero.png | D01 (refined), from the north over Ngong Road | 8.2 min |
| D02_daylight_landing_hero.png | D02, from the south over the forest, looking north to the city | 9.2 min |
| D03_daylight_landing_hero.png | D03 (refined), high and close, from the north-west | 12.3 min |

## What reads (by eye)

- Final grass everywhere the design has it:
  - the forecourt lawns and planted beds;
  - the training pitch and track;
  - the south-west lawn pitch with its loop road (the traced as-built layout, finished with pitch lines);
  - the north-east warm-up track.
- Pillowed roof, shields, lattice and louvres as in passes A and B.

## Gaps

1. **People and cars are generic low-poly masses (Visualization).**
   - The plaza crowd in D01 reads as coloured sticks at this distance.
   - They are not a crowd count or a safety simulation.
   - They could be hidden for these views, or given better figures.
2. **Clustered tree crowns read as big soft blobs when close** (D02 and D03 foreground). They were tuned for landing distance in pass D.
3. **The finished layout outside the south-west is the mockup design,** not a surveyed plan (ground_fix_01, gap 4).
4. **D01 left middle distance:** a pale bare-earth patch beyond the training pitch. That is terrain the finished layout does not cover.
5. **D03 foreground:** the long grey-roofed shed and the coach bays at the bottom edge are the existing context blocks, untextured.
