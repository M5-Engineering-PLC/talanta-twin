# Render order: walkthrough chapters 1 and 2 (for Munene's approval)

Date: 2026-10-26. Status: version C approved by Munene 2026-10-26, without a full repeat pass. C1 and C2 passed 2026-10-26. C3 to C6 are on hold (Munene, 2026-10-26) until the interior, the seat re-check and the P2 bakes are done and the render pack is rebuilt.
Decisions: engineering/lead_decision_2026-10-25_walkthrough.md (chapters, GPU option), engineering/lead_decision_2026-10-25_reel_and_v2.md (R3 cost rules).
Camera paths: blender/landing_reel/chapters.json, blender/landing_reel/paths.py; preview: blender/landing_reel/chapters_1_2_preview.jpg.
Renderer: blender/scroll_test/render_scroll_frames.py `chapter=<id>` on blender/out/frozen_FK.blend (or the render pack, branch assets/render_pack).
Kaggle result: engineering/kaggle_gpu_test_2026-10-25.md (058f9ce).
Claim on screen for both chapters: "Visualization: people, vehicles and lighting are illustrative".

## Shot list

| Chapter | Length | Frames (24 fps) | Camera move | Light |
|---|---|---|---|---|
| 1 Arrival | 8 s | 192 | Starts on the L07 poster frame (frame 0 is the L07 camera; checked, matrix difference 1.5e-7), then a slow push along the view line: 12 % closer, 6 m lower, a 14 deg drift east round the L07 target, ease out | 10:30 day (daylight_artistic) |
| 2 Orbit | 10 s | 240 | From the east (over the east approach), 110 deg round the stadium through the south-east, from 130 m to the L07 height and from 540 m to the L07 radius, ease in and out; ends exactly on L07 and holds 12 frames (0.5 s) for the crossfade into the live twin | 10:30 day |

- Lens: the L07 focal length throughout (38 mm, vertical FOV 29.84 deg).
- The film ends on L07 at 10:30 (the live twin camera). No dusk shot in chapters 1 and 2.
- Rule 8: the nearest camera point is 426 m from the pitch centre (about 300 m from the facade); both chapters frame the whole stadium, with no door, gate or exit at close range.
- Portrait cut (phones), 720 x 1280: its own render of the same paths, the same vertical FOV, the lens shifted to the 9:16 window the app uses for L07 on phones (app/src/ui/landing.js, crop x 820 to 1427, shift_x 0.151). The last portrait frame is the phone L07 view. It is not a crop of the wide film.

## Measured costs (R3 step 2, 4-core cloud CPU, L07 day, 1080p)

From blender/renders/scroll_test_01 (24 frames), blender/renders/scroll_test_02 (24 lit frames) and the lever tests in blender/renders/reel_levers/ (3 to 5 frames of the same orbit):

| Setting | s per frame | Look |
|---|---|---|
| Stills quality: 128 samples, haze volume and its pass layer, persistent data | 704 | reference |
| Same, persistent data off | 682 to 691 | same; persistent data saves nothing measurable (the cost is path tracing, not scene sync) |
| Haze volume off (compositor mist haze only), 128 samples | 372 | in this day view, mean difference to the haze version 1.5 of 255; the far land and sky are very slightly clearer |
| Haze off, 48 samples, OpenImageDenoise | 224 | clean; grass a little smoother from the denoiser |
| Haze off, 32 samples | 153 | as 48, slightly softer fine texture; 24-frame flicker: see below |
| Portrait 720 x 1280, haze off, 48 samples | 92 | |
| Lit dusk (L06 sunset_artistic, 128 samples, haze) | 1,050 | 1.5 times the day frame |

Flicker over 24 frames: 128 samples with haze (scroll_test_01) and the lit dusk run (scroll_test_02) show no frame that stands out. 32 samples, haze off (24 frames, 2026-10-26, blender/out/reel_levers/h0_s32_24): no frame stands out; the mean brightness steps between neighbouring frames are 0.15 of 255 (median) and 0.32 (largest), against 0.13 and 0.28 for the 128-sample haze run (scroll_test_01). The frame times in this run (about 270 s) are not a cost figure: other renders shared the CPU; 153 s (measured alone) stays. Version C (stills quality, 128 samples) does not depend on this test; it applies to version B only.

File sizes (H.264, measured on the 24-frame day orbit, which moves 1.25 deg a frame, faster than chapters 1 and 2): 1080p CRF 26 with a 2 s GOP is 0.92 MB per second; the 720 x 1280 portrait 0.34 MB per second. So, at most: chapter 1 about 7 MB (portrait 2.7 MB), chapter 2 about 9 MB (portrait 3.4 MB).

Parallel rendering (R3 step 3): yes. A second cloud session in the TALANTA environment runs at the same time on its own machine (probe 2026-10-25: 4 cores, 15 GB, Blender 5.2.3, 29 GB disk). The frames do not depend on each other, so N sessions divide the wall time by N; the CPU hours stay the same. Each session needs the render pack (assets/render_pack, 175 MB in 2 parts).

Interpolation (R3 step 4): not used. All versions below render every frame at 24 fps.

## Version C: Kaggle GPU (recommended)

| Item | Value |
|---|---|
| Machine | Kaggle notebook, GPU T4 x2 (2 x Tesla T4, 16 GB each), OptiX, Blender 5.2.2; free, 30 GPU hours a week |
| Input | the private dataset talanta-render-pack (render pack 7e19362); the notebook stays private |
| Settings | stills quality: 128 samples, haze volume and its pass layer, persistent data, OpenImageDenoise; 1920 x 1080 and the 720 x 1280 portrait |
| Seconds per frame | wide 54.4 s (GPU test, 2026-10-25), 53.2 s (C1); portrait 30.1 s (C2; the pixel-count estimate was 24.2 s) |
| Frames | 432 wide plus 432 portrait |
| Render time of one pass | wide 432 x 54.4 s = 6.53 h; portrait 432 x 24.2 s = 2.90 h (to measure) |
| Cost per run | about 355 s more: the first frame of each Blender process takes about 229 s (OptiX kernels, 175 s more than a frame), plus an estimated 180 s for the Blender download and the pack copy |
| Notebook | blender/kaggle/talanta_chapter_render.ipynb; the first code cell sets CHAPTER, CUT (wide or portrait), FRAME_START, FRAME_END, SAMPLES and HAZE; it writes the inline gpu_pre.py of the test notebook |
| How | one Blender process for each run, many frames for each run, each run less than 4 h; "Save Version", then "Save & Run All (Commit)", private; the run continues in the background and the frames stay as the version's output (frames/<run>/ with scroll_log.json and run_record.json with a sha256 for each frame) |

Runs (GPU hours, with 355 s for each run):

| Run | Chapter, cut | Frames | GPU hours |
|---|---|---|---|
| C1 test | ch1 wide | 0 to 23 | 0.43 (measured: 1,534.7 s) |
| C2 test | ch1 portrait | 0 to 23 | 0.29 (measured: 224.3 s + 23 x 30.1 s, plus setup) |
| C3 | ch1 wide | 24 to 191 | 2.58 (at 53.2 s) |
| C4 | ch2 wide | 0 to 239 | 3.65 (at 53.2 s) |
| C5 | ch1 portrait | 24 to 191 | 1.50 (at 30.1 s) |
| C6 | ch2 portrait | 0 to 239 | 2.11 (at 30.1 s) |
| First pass | | 864 frames, 6 runs | 10.56 |
| Repeats | only the frames that the review rejects | as needed | 4.00 at most |
| Budget for the week | | | 14.56 at most (limit 20 h; 30 h a week) |

- The 24-frame tests (C1, C2) are frames 0 to 23 of the film; they are not rendered again in the first pass.
- After C1 and C2: stop, measure the seconds per frame and update this table. If the wide frame takes more than 56 s, C4 is more than 3.8 h: split it into 0 to 119 and 120 to 239 (0.10 h more).
- The first draft had a full repeat pass (9.82 h, total 19.84 h). The approval removed it.
- Stop the session after each run. An idle session uses GPU hours.

Render pack and the G2 trees: pack 7e19362 does not need a rebuild.
- The G2 defect (dark, faceted trees) was in the web export only: the canopy set lost its UVs in the exported mesh, and the other tree sets got the colour of the darkest node of their material. The fix (740638e) changes blender/web_hero/export_web.py and the glTF bundle. It does not change the Blender scene.
- The Cycles scene uses the tree materials and UVs of frozen_FK.blend. That file has not changed since 2026-10-24 14:51 UTC; the pack (built 2026-10-25 15:34) has the same scene, with relative image paths. Its frame 0 is pixel-identical to scroll_test_01 frame 0.
- The pack's render_scroll_frames.py, chapters.json and paths.py are the same files as on wo/web-hero-v2 (checked byte for byte 2026-10-26), so `chapter=` works from the pack.

Frames: Munene downloads the output of each run. Then the frames go to the orphan branch assets/landing_reel_frames (not to wo/web-hero-v2), then the encodes (H.264 CRF 26, 2 s GOP; 1080p and 720 x 1280).

## Version A: rented RTX 4090 (paid fallback)

| Item | Value |
|---|---|
| Settings | stills quality: 128 samples, haze volume and pass layer, OptiX, OpenImageDenoise on the GPU; 1920 x 1080 and the 720 x 1280 portrait |
| Seconds per frame (estimate) | 1080p: 10 to 25 s; portrait: 5 to 12 s. Basis: Blender Open Data puts an RTX 4090 with OptiX at about 120 to 160 times a 4-core 2.1 GHz Xeon on path tracing, so the 704 s path-traced part becomes 5 to 6 s; plus 3 to 8 s a frame for the compositor, the denoiser and the PNG write, and margin for the volume. To be measured in the test below |
| Frames | 432 wide plus 432 portrait |
| GPU time | about 1.8 to 4.2 h for both chapters and both cuts, plus about 5 min of scene load per run |
| Memory | the scene takes about 4.5 GB on the CPU; it fits in 24 GB |
| Cost | 0.34 to 0.89 USD an hour (RunPod secure cloud): about 1 to 4 USD for one pass |
| Test first | 24 frames of chapter 1 (frames 0 to 23), wide; measure the seconds per frame, GPU memory and cost; stop and report |
| How | the render pack (assets/render_pack); RENDER_PACK.md; set the Cycles device to GPU (OptiX) with a TALANTA_PRE file; data-centre machine, read-only deploy key, delete the machine and disk after the render (walkthrough decision, conditions). Munene sets up the account; no agent enters payment details |

## Version B: the 4-core cloud CPU, 30 h or less (fallback without a GPU)

| Item | Value |
|---|---|
| Settings | haze volume off (compositor haze kept), 32 samples, OpenImageDenoise, persistent data; 1920 x 1080 and the 720 x 1280 portrait |
| Seconds per frame | 153 s wide (measured); portrait about 63 s (measured 92 s at 48 samples, scaled to 32) |
| CPU time | wide 432 x 153 s = 18.4 h; portrait 432 x 63 s = 7.6 h; total 26.0 h (limit 30 h) |
| Parts under 4 h | 9 parts (at most 94 wide frames a part): wide ch1 frames 0-63, 64-127, 128-191 (2.7 h each), ch2 0-79, 80-159, 160-239 (3.4 h each); portrait ch1 0-191 (3.4 h), ch2 0-119 and 120-239 (2.1 h each) |
| Wall time | 26 h in one session; about 13 h with two sessions in parallel |
| Fallback if 32 samples flickers | 48 samples with 6 s chapters (144 + 192 frames = 336): wide 20.9 h + portrait 8.6 h = 29.5 h, or 48 samples at 8 + 10 s with the portrait at 32 samples: 26.9 + 7.6 = 34.5 h (over the limit) |
| Quality against version A | no volumetric haze (the compositor haze stays), 32 samples instead of 128: in the measured day frame the difference is small (mean 1.4 of 255 against 128 samples without haze); fine texture (grass, far trees) is a little softer |

After each part: the frames go to the orphan branch `assets/landing_reel_frames` (not to wo/web-hero-v2), then the encodes (H.264 CRF 26, 2 s GOP; 1080p and 720 x 1280).

## Approval and run gates (Munene, 2026-10-26)

- Approved: version C. No full repeat pass. A repeat run renders only the frames that the review rejects.
- GPU budget for the week: the first pass (about 10.0 h) plus 4 h of repeats at most.
- C1 first: 24 wide frames of chapter 1 (frames 0 to 23). Then stop and report the seconds per frame, the GPU memory and the frame check (run_record.json: gpu_memory_max_mib, frame_check).
- C2 next: the 24-frame portrait test, also with a stop and a report.
- When C1 and C2 pass, C3 to C6 run without a new approval, if each run is less than 4 h and the week stays under 20 GPU h.
- Set TEST_S_PER_FRAME in the notebook to the test result of that cut (C1 for wide, C2 for portrait). Stop if a frame is more than 10 % slower than the test (run_record.json: slow_frames).
- Each run: Munene starts it on Kaggle ("Save Version", "Save & Run All (Commit)", private), downloads the output and sends run_record.json and scroll_log.json for the report. The frames then go to assets/landing_reel_frames.
- The cloud session cannot start or see a Kaggle run. It continues with the interior model (item 2 of the lead order 2026-10-26).

## Test results

| Run | Result | Seconds per frame | First frame | GPU memory (max) | Frame check | Slow frames | Run time |
|---|---|---|---|---|---|---|---|
| C1 (ch1 wide 0 to 23) | passed 2026-10-26 | 53.2 s | 228.7 s | 1.8 GB of 15 GB on each T4 | pass | none | 1,534.7 s (0.43 h) |
| C2 (ch1 portrait 0 to 23) | passed 2026-10-26 | 30.1 s (estimate 24.2 s) | 224.3 s | 1.7 GB of 15 GB | pass (luma step 0.3) | none | about 0.29 h |

- C1 is 2 % faster than the GPU test (54.4 s). C4 stays one run (3.65 h, less than 4 h); no split.
- TEST_S_PER_FRAME for the wide runs (C3, C4) is 53.2.
- C2: the portrait frame is 24 % slower than the pixel-count estimate (fixed costs per frame: scene sync, compositor, denoiser). TEST_S_PER_FRAME for the portrait runs (C5, C6) is 30.1. C3 to C6 together: about 9.8 GPU h.

## Hold on C3 to C6 (Munene, 2026-10-26)

- C3 to C6 do not start until these are done: the interior (chapters 3 and 4), the seat re-check, the P2 bakes (10:30, 18:05, 20:00) and the new render pack.
- The new pack (assets/render_pack c14cc71, 2026-10-26: frozen_FL.blend with the seat re-check stand detail, frozen_FL_interior.blend) becomes a new version of the Kaggle dataset talanta-render-pack; it is built before the bakes, because the P2 bakes run on the Kaggle GPU (Munene, 2026-10-26; blender/kaggle/BAKE_ON_KAGGLE.md). C3 to C6 run on it after the bakes, with the same notebook settings (the notebook takes frozen_FL.blend).
- C1 and C2 (frames 0 to 23 of chapter 1) were rendered on pack 7e19362. If the new pack changes the stand that chapter 1 sees (for example the seat model), frames 0 to 23 of both cuts render again on the new pack (about 0.7 GPU h), so the chapter has one scene state.

## Notebook settings for each run

| Run | CHAPTER | CUT | FRAME_START | FRAME_END | TEST_S_PER_FRAME |
|---|---|---|---|---|---|
| C1 | ch1_arrival | wide | 0 | 23 | None |
| C2 | ch1_arrival | portrait | 0 | 23 | None |
| C3 | ch1_arrival | wide | 24 | 191 | 53.2 |
| C4 | ch2_orbit | wide | 0 | 239 | 53.2 |
| C5 | ch1_arrival | portrait | 24 | 191 | 30.1 |
| C6 | ch2_orbit | portrait | 0 | 239 | 30.1 |

SAMPLES = 128 and HAZE = 1 for all runs (stills quality).
