# START HERE: Talanta twin build runbook

Date: 2026-10-17
Branch: claude/hopeful-archimedes-lo15is
Owner: Munene (lead review in his local session)

This file is the single entry point for the cloud build chat. Munene pastes one line: "Read engineering/START_HERE.md on branch claude/hopeful-archimedes-lo15is and run it." Every other document is linked from here.

## How to work with Munene

- Pull the branch first: `git pull`. Read AGENTS.md, then this file, then the documents that the current stage names.
- Do the code, Blender and render work yourself in this cloud session. Munene's laptop is weak (Intel UHD 620, 7 GB RAM) and gets hot. Never ask him to build or render locally. No GPU is available, and he cannot rent one.
- Give Munene one step at a time, then wait for "done" or for the text that he pastes. Ask him only for things that need his PC: Google Earth Pro, a real-device browser check, a look at a render, and approvals.
- Before a long job, give the expected time. After each job, report the commits, pass or fail, and the next step.
- At each gate, stop and show the evidence. Munene takes renders to his lead session for review where this file says so.
- Update the "Status" table at the end of this file when a stage is complete, and commit it.
- Commit as Munene, with no Claude attribution. Push after each stage.

## Flow

```mermaid
flowchart TD
  S[START_HERE.md] --> A[Stage A: record W1b batch 2<br/>w1b_measurements_2026-10-17.md]
  A --> G1{Gate G1: cloud Blender<br/>CPU render test}
  G1 -- pass --> B0[Stage 00: ledger and 16 cameras<br/>workorder_hyperreal_phaseA]
  G1 -- fail --> X1[Stop. Report the times to Munene]
  B0 --> B1[Stage 01: Blender blockout<br/>Workbench renders]
  B1 --> G2{Gate G2: geometry<br/>against the ledger}
  G2 -- pass --> B1b[Stage 01b: camera match on<br/>historian frames JWNowpO44rw]
  G2 -- fail --> B1
  B1b --> G3{Gate G3: 3 frames solve<br/>below 3 px}
  G3 -- pass --> B2[Stage 02: hero shot C06<br/>CPU Cycles, scored passes]
  G3 -- fail --> X3[Keep values as estimated.<br/>Report to Munene]
  X3 --> B2
  B2 --> G4{Gate G4: score 85 or more<br/>on two passes}
  G4 -- pass --> G5{Gate G5: blind test<br/>render against real frame}
  G4 -- no gain after 3 passes --> L[Lead review]
  G5 -- pass --> C3[Stage 03: four specialist builds<br/>overnight critic loop]
  G5 -- fail --> L
  L --> B2
  C3 --> W[Web track: export glTF to three.js<br/>roadmap_hero_v1 P1 to P13]
```

## Stages and files

| Stage | What to do | Read these files | Munene's part | Gate |
|---|---|---|---|---|
| Done | Sol review fixes, five quick wins, roadmap | workorder_sol_review_2026-10-17.md, roadmap_hero_v1_2026-10-17.md | none | Done in commits 565e38b to 7be3c7e |
| A | Save W1b batch 2 as CSVs in gis/measurements/, update gis/site_measurements.md | w1b_measurements_2026-10-17.md | Draw the shapes that are still open (roof inner ring, bowl plinth, two training pitches). Export the "TALANTA w1b" folder as KML and paste it here | CSVs exist, and every value has a source and an image date |
| G1 | Prove that this cloud session can render. Run `blender -b --version`. Render the default scene, then a 200,000-triangle test scene, in CPU Cycles at 960 x 540, 64 samples, with the denoiser. Record the CPU count, RAM and the time for each frame | engineering/cloud_setup.sh | none | One look-check frame in 20 minutes or less |
| 00 | Parameter ledger and 16-camera manifest | workorder_hyperreal_phaseA_2026-10-17.md (Stage 00), review_astra_hyperreal_2026-10-17.md | none | Every number in bowl.js, site.js and pitch.js has a ledger row |
| 01 | Blender blockout from the ledger. Workbench renders C01 to C05. glTF round trip behind `?blender` | Phase A work order (Stage 01) | none | G2: geometry matches the ledger within its uncertainty |
| 01b | Camera match on historian frames. Measure heights and the roof, count ribs and bays, and write detail specs | Phase A work order (Stage 01b), research/frames/JWNowpO44rw/, research/video_index/MASTER_INDEX.csv, gis/heldout_frames.csv | none | G3: at least 3 frames solve below 3 px |
| 02 | Hero shot C06, golden hour, CPU Cycles, up to 3 scored passes | Phase A work order (Stage 02), research/concepts/2026-10-17/: the lead renders 06 and 07 are the look target (internal only; the ledger outranks them) | Look at the C06 renders and take them to the lead session | G4: 85/100 on two consecutive passes. G5: blind test |
| 03 | Four specialist builds (roof and envelope, facade and bowl, landscape, people dressing) with an overnight critic loop | Astra review (pipeline stages 03 to 05) | Approve the start | Lead review of the critic scores |
| Web | Export the accepted Blender assets to three.js. Then run roadmap packages P0 to P13 | roadmap_hero_v1_2026-10-17.md | P0 device baseline. P5 measurements | The gates in the roadmap |

Hold roadmap package P1 (bowl.js polish) until gate G2 passes. After G2, the Blender blockout is the source of the bowl, and P1 work in bowl.js would be done twice. P0, P3, P5 and P7 can run at any time.

Lead renders: research/concepts/2026-10-17/06_lead_ne_to_ngong_hills.jpg and 07_lead_ssw_to_lavington.jpg. Munene chose these two as the look target for the hero shots and Stage 03. They are internal design help, derived from the historian frames. Where the ledger and a lead render disagree, follow the ledger.

## Confidence gates

Confidence is not given in advance. Each gate turns a risk into evidence. Record each result in the Status table.

| Gate | Risk that it removes | Confidence after a pass (lead's estimate) | If it fails |
|---|---|---|---|
| G1 | The cloud cannot render, or is too slow | 70% to 75% | Render at lower resolution and use fewer cameras. Report to Munene before any other change |
| G2 | The geometry is wrong | 75% to 80% | Fix the ledger or the script, and repeat |
| G3 | The finished-state details are guesses | 80% to 85% | Keep those values "estimated". The look can still pass |
| G4 | The look does not reach the target | 90% | Lead review. Change the materials or the lighting, not the measurements |
| G5 | The result looks realistic only to us | 95% or more. After G5 the result is evidence, not a forecast | Lead review |

G5 blind test: show a C06-matched render and a real frame from the historian video at the same camera, side by side, without labels. Ask Munene and two other people which one is real, and to rate the realism from 1 to 5. G5 passes when the render scores 4 or more and the viewers cannot reliably pick the real frame. Keep this test internal (AGENTS.md rule 2).

## Overnight loop (stage 03 and later)

The reference project ran its critic loop overnight. Do the same after G5:

- Run the specialist builds in sequence, and render the 16 cameras in CPU Cycles at look-check settings.
- Score each pass with the eight Astra categories. Correct the two lowest categories.
- Stop at 85/100 on two consecutive passes, after 8 passes, or after three passes that gain less than 2 points.
- Commit after each pass, with the scores in blender/renders/pass_NN/scores.csv.

## Stage 02b (lead review of stage 02, 2026-10-17)

The lead (with a GPT-6.1 Sol second opinion) approved the direction; no stage 01 redo. Pass 3 re-scored at 52/100 (materials, lighting, atmosphere and vegetation 2 each): blender/renders/stage02_pass3/scores_rescored.csv. This section amends the flow above:

- Up to 4 more C06 passes (stage02_pass4 onward). Then go to stage 03 whatever the score. G4 (85 on two passes) is judged after stage 03.
- Stop early if two passes in a row gain less than 3 points.
- Score each pass side by side with reference frames, not from memory: 12:12, 12:16, 10:28 (facade, shields, spears), 11:20, 12:40 (roof, ground, context), 07:04 (proportions). Never frames in gis/heldout_frames.csv.
- Fixes in order: (1) louvre fins over a dark recessed backing, clearer lattice; (2) shields at 85-90% of facade height with the full pattern and a slight bulge, and two crossed spears behind each, tips below the roof edge; (3) base: light concrete band, white columns, recessed shadow; (4) morning sun for C06 (about 07:30-07:45 EAT, 11-14 deg) and a raised target showing the Ngong Hills and a sky band; (5) ground regions: murram, concrete paving, asphalt with markings, green only on pitches; (6) roof: lower ribs, faint seams, panel variation; (7) trees: wooded belt, clumps and clearings; (8) sky: low-resolution CC0 HDRI with clouds, recorded in the ledger.
- Keep each render under about 5 minutes, and report its time.
- C17 waits for stage 03 (landscape specialist). For the G5 test, crop or mask the watermark on the real frame. C17 stays internal.
- After each pass, commit a side-by-side sheet of C06 and the 12:12 frame (internal only).
- Shield, spear, fin and lattice sizes are "estimated, by eye from <frame>" in the ledger.

## Rules

- Follow AGENTS.md. Frames, Google Earth imagery and the concept renders are references only. Never use them as textures.
- Measured facts outrank looks. Label each value measured, derived or estimated, in the ledger and in the app.
- Keep gates, exits, camera positions and control rooms out of any public output.
- Label crowd views "Visualization" and rain "Simulation".

## Status

| Stage | Status | Evidence |
|---|---|---|
| Sol fixes and quick wins | Done | 565e38b to 7be3c7e |
| A | Done (2026-10-17) | Seven W1b CSVs in gis/measurements/ (roof outer and inner rings, bowl plinth, north plaza, warm-up track, training pitch SE, training field SW), each with source and image date 2025-12-26 (Airbus). Scale checks not possible: no pitch markings |
| G1 | Pass (2026-10-17) | Blender 5.2.2 (bpy wheel), 4 CPUs, 15.7 GB RAM. CPU Cycles 960x540, 64 samples, OIDN: default scene 7.1 s; 297,866-triangle scene 29.0 s. blender/renders/g1/g1_times.json |
| 00 | Done (2026-10-17) | gis/parameter_ledger.csv: 172 rows (52 measured, 24 derived, 96 estimated). app/cameras/manifest.json: 16 cameras, load checks pass in three.js and Blender |
| 01 and G2 | Done, G2 pass (2026-10-17) | blender/build_blockout.py from the ledger and the normalized W1b shapes; 19 objects, 77,097 triangles. Workbench C01-C06 in 2.9-3.6 s each (blender/renders/pass_01/). G2: 14 of 14 checks pass (geometry_gate.csv). glTF round trip behind ?blender works. Open: 28 of 240 directions where the 12-point roof trace is over 4 m inside the plinth are clamped (estimated) |
| 01b and G3 | G3 not passed (2026-10-17): no pitch markings in the historian frames, and the 07:04 aerial has no identifiable ground-level W1b point, so no camera solved (no second frame, per Munene). Wall shape fixed by eye against 07:04 (near-vertical wall, 8 m shoulder), labelled estimated; heights stay estimated. G2 still passes. Before/after: blender/renders/pass_02/C02_wall_before_after.png, C06_wall_before_after.png | |
| 02, G4 and G5 | 3 passes done (2026-10-17); G4 not reached: C06 scores 47, 57, 62/100 (CPU Cycles 960x540, 64 samples, 99-105 s each). Waiting on lead review. C17 (07:04 match by eye, internal) rendered for G5 prep, 85 s | blender/renders/stage02_pass1-3/, stage02_c17/ |
| 02b | Done (2026-10-17): C06 52 (pass 3 re-scored) -> 59, 67, 68, 70/100 over passes 4-7, CPU Cycles 960x540, 64 samples, 101-116 s each. Pass 6 gained 1.6 and pass 7 1.7 points; 4 passes used. Poly Haven HDRI blocked by the network policy, so procedural clouds (lead's fallback). G4 judged after stage 03 | blender/renders/stage02_pass4-7/ (scores.csv, C06_vs_1212_internal.jpg) |
| 03 | Started (2026-10-17): Munene asked for the lead renders' level of detail inside the stadium first, so the facade and bowl build goes first | |
