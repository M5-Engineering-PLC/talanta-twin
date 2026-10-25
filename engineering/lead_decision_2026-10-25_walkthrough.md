# Lead decision: the guided walkthrough landing and one source for live content (2026-10-25)

Date: 2026-10-25
Project: Talanta twin (M5)
From: the local lead session, for Munene, Sol and the cloud build chat
Status: plan approved by Munene on 2026-10-25. The GPU rental needs Munene's approval of the cost (see "Render power").
Branch: `wo/web-hero-v2`
Replaces: the reel shape in engineering/lead_decision_2026-10-25_reel_and_v2.md, R1 and R2. The R3 cost rules stay (test first, parts under 4 h, approval before a full render).
Changes: engineering/lead_decision_2026-10-25_cycles_parity.md. P3 photo mode is paused. P1, P2 and P4 continue.

## What the visitor gets

1. The landing is a guided walkthrough film in chapters. It plays muted. "Skip", "Explore in 3D" and a chapter bar are always on screen.
2. The last frame of the film is identical to a live twin camera. The film crossfades into the live twin.
3. The live twin is the place to explore: orbit, zoom, the time of day, and the modules on demand.

## Chapters

| No. | Chapter | Render source | State on 2026-10-25 |
|---|---|---|---|
| 1 | Arrival: the poster still comes alive, close to hero_artistic_04 | Cycles | Model ready |
| 2 | Orbit: the stadium from the main angles | Cycles | Model ready |
| 3 | Going in: through the concourse into the bowl | Cycles | The interior needs model work (workstream A) |
| 4 | A lap of the bowl at stand height | Cycles | Same as chapter 3 |
| 5 | Concert | Cycles, from app data | EVT-01 is not built in the app |
| 6 | Football match | Cycles, from app data | SPT-01 is not built in the app |
| 7 and later | One chapter for each finished simulation: drone show, floodlight and facade show, crowd wave, fireworks, rain, night match | Cycles, from app data | SHW-01, SHW-02, SHW-03, PPL-02 exist in the app |

Rules:
- Each chapter is 6 to 10 s and is a separate video file. A new chapter does not change the other chapters.
- The film ends on a live twin camera. Use L07 at 10:30 until the P2 bakes give other times.
- If the visitor turns on reduced motion, show the poster still and the chapter bar, and no video.
- Phones get a 720 x 1280 portrait cut from their own camera moves. Do not crop the wide film.
- Each chapter with people, vehicles, shows or events shows its label on screen ("Visualization" or "Illustrative event concept", as in engineering/scope_decision_2026-10-25.md).
- No shot, lap or interior move frames an exit, a control room or a camera position (AGENTS.md rule 8). OPS-01, PPL-04 and MOB-04 do not appear in the film.
- Reference frames from videos never go into the film (AGENTS.md rule 2).

## One source for live content

Blender and three.js are two renderers of the same model. The static world goes from Blender to three.js through the glTF export (web_hero_v2). The live content (shows, crowd, events) is code in the app. It does not exist in Blender.

The rule:
- The static world (stadium, roof, facade, grounds, trees, interior) is built in Blender only. Cycles renders it for the film. The glTF export sends it to the twin.
- The live content is written in the app only, as data. A bridge exports that data, and Blender builds the same content from it for Cycles. Do not build a show or an event by hand in Blender.
- The film shows only content that the twin has.

## Workstreams

| ID | Workstream | Who |
|---|---|---|
| A | Blender model: trees (G2), facade colour, interior (concourse, stands, tunnel) to the exterior standard, phone variant (G8) | Cloud |
| B | Live twin quality: P1 colour match and P4 crossfade (done in fea6c50, waiting for the cloud look block and references), P2 bakes and blend | Cloud and laptop |
| C | Data bridge: the app writes show and crowd data as JSON; a Blender importer builds the same content | Laptop (exporter), cloud (importer) |
| D | New events in the app: EVT-01 concert, SPT-01 football match | Laptop |
| E | The film: shot list and render order for each chapter, and the landing player | Cloud (renders), laptop (player) |

### C. Data bridge details

- Start with the content that exists: SHW-03 drone show, SHW-01 floodlight show, SHW-02 facade and roof show, PPL-02 crowd reactions.
- The app exports a timeline file for each show: the frame rate, then for each frame the positions, colours and intensities. For the crowd, export the seat list and the action for each seat and time, not every vertex.
- The file format is versioned JSON, with the app module ID and the claim label in it. Large arrays go in a binary side file.
- The importer uses geometry nodes or instancing in Blender. It must render the same timing as the app.
- Acceptance: a frame of the app and the Cycles frame at the same time and camera show the same drone shape and the same lit seats.

## Order

1. Now (cloud): finish the running queue (scroll_test_02, R3 lever tests, G2, P1 look and references, G8). Then write blender/landing_reel/RENDER_ORDER.md for chapters 1 and 2, for a GPU and for the 4-core CPU.
2. Next (cloud): the interior model for chapters 3 and 4, then the P2 bakes.
3. Next (laptop): the data bridge exporter and the landing player with chapters.
4. Then (laptop): EVT-01 and SPT-01 in the app, then their chapters.
5. Later: one new chapter for each finished simulation.

## Render power

The 4-core cloud machine takes 704 s for each 1080p frame (blender/renders/scroll_test_01). Six chapters of 8 s at 24 fps are about 1,150 frames, about 225 h. The lit sunset look is about 1.7 times slower. This is not possible inside the 30 h limit.

Option 1, recommended: rent a GPU machine for Cycles.

| Item | Estimate | Source |
|---|---|---|
| Speed | An RTX 4090 with OptiX renders the BMW27 scene about 14 times faster than a 16-core Ryzen 9 7950X. Our machine has 4 cores, so expect 25 to 50 times faster. | OpenBenchmarking result 2509258-NE-GPUV4409013 |
| Time for each frame | 15 to 60 s, including scene sync and the compositor. Measure it. | Estimate |
| Time for chapters 1 to 6 | about 5 to 19 h | Estimate |
| Price, RTX 4090 | about 0.34 to 0.89 USD for each hour (RunPod), 0.15 to 0.31 USD (Vast.ai marketplace) | Price trackers, October 2026 |
| Cost for chapters 1 to 6 | about 5 to 20 USD for one pass. Plan for 100 USD with tests and new renders. | Estimate |

Conditions:
- Use a data-centre machine (RunPod Secure Cloud or similar), not a marketplace host. The model and the repository are private.
- Use a read-only deploy key for the repository. Delete the machine and its disk after each render.
- Munene sets up the account and the payment. No agent enters payment details.
- First run one test: 24 frames of chapter 1. Measure the time, the GPU memory and the cost before the full render.
- Check that the scene fits in the GPU memory (24 GB on an RTX 4090, 32 GB on an RTX 5090).

Option 2: Eevee on a rented GPU. It is faster and cheaper, but the light is visibly flatter. Use it only for draft cuts.

Option 3: the 4-core CPU only. Shorter chapters and lower settings, inside 30 h. The quality target is lower.

## Open decisions for Munene

1. Approve the GPU rental (option 1) and the 100 USD limit, and set up the account.
2. Approve the chapter 1 and 2 render order when the cloud delivers it.
