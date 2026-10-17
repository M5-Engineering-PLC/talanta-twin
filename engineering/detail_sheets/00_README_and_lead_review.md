# Detail sheets: read this first

Date: 2026-10-17
Made by: four GPT-6 Luna workers (read-only), one for each area. Reviewed by the local lead session against the historian frames.
For: the cloud build chat, Stage 03.

## The sheets

| File | Area | Id prefix | Rows |
|---|---|---|---|
| 01_roof_facade.md | Roof and facade | RF | 41 |
| 02_bowl_seats.md | Bowl interior and seats | BS | 48 |
| 03_site_roads.md | Site, roads and entrances | SR | 51 |
| 04_people_life.md | People, crowd and life (Visualization) | PL | 43 |

Each row gives the shape, the colour (hex), the count or spacing, the size, the source, the agreement between frame and render, the status and a build note. The sheets add the fine detail under the element checklist in engineering/stage03_detail_spec_2026-10-17.md.

## Lead review: corrections that override the sheets

1. Finished state, not construction. Most frames date from the construction period (January 2026). Bare earth, unfinished roads and young planting in a frame do not describe the finished state. For the finished landscape, use these sources in this order:
   - The physical design model in the historian video: frames 04:45, 05:12, 05:16 and 27:36. MASTER_INDEX labels 04:45 as a fountain pool, but the frame shows the design model.
   - The lead renders 06 and 07.
   - The construction frames, for positions only.
   Label values from the design model "estimated (design model)".
2. Trees and planting. The design model shows avenues of palms along the paths, broad-crowned trees in clumps, and red flower beds. This settles the palm conflict in sheet 03: use palms along the forecourt paths.
3. Ngong Road. Sheet 03 sampled the site access roads, which are unfinished. Use frame 07:04 for Ngong Road. It is a finished dual carriageway with three to four lanes in each direction, a central reserve with a barrier, white lane markings, a footpath and a service strip at the side. Billboards stay blank.
4. Speakers. Frame 02:00 shows large curved white line-array speaker clusters with dark grilles. They hang from steel frames under the roof, above the upper tier. Add them to the bowl build. This closes the "speaker clusters" to-do in the Stage 03 checklist.
5. Seats and handrails. The seat colours in sheet 02 agree with frames 02:00 and 08:00. The seats are a green lower tier and a red upper tier with dark seats increasing toward the back. Handrails are grey steel. The black wrap in frame 08:00 is construction protection; do not model it.
6. Capacity. Do not change the seat spacing to reach 60,000. The capacity gate stays failed until the rows are measured (sheet 02, row BS10).
7. People. Every row in sheet 04 is a Visualization estimate, because no frame shows a match crowd. Keep crowds out of the critic score for geometry and materials.
8. Security. The sheets contain no gate positions, exits, security cameras or control rooms. Keep it that way. Model entrances as generic canopies and paving only.
9. Frames outrank renders. Where a sheet row says "render" only, keep it "estimated". Where it says "conflict", use the frame value, except where items 1 to 3 above apply.

## How to build from the sheets

- Add each new value to gis/parameter_ledger.csv with status "estimated (detail sheet <id>)", or "estimated (design model)" under correction 1.
- Work in camera order, so each pass improves what the hero cameras see:
  1. The exterior and site rows that show in C06 and the lead renders 06 and 07: RF, then SR.
  2. The bowl interior: BS.
  3. People last: PL, on the matchday camera only.
- After each group, render the affected cameras at the check settings. Put each one side by side with its reference frame and its lead render.
- In the Stage 03 checklist, record each sheet id as done, partly done or not possible.
