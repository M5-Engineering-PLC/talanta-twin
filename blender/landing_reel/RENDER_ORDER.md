# Render order: walkthrough chapters 1 and 2 (for Munene's approval)

Date: 2026-10-26. Status: **waiting for approval. Nothing of the full render has started.**
Decisions: engineering/lead_decision_2026-10-25_walkthrough.md (chapters, GPU option), engineering/lead_decision_2026-10-25_reel_and_v2.md (R3 cost rules).
Camera paths: blender/landing_reel/chapters.json, blender/landing_reel/paths.py; preview: blender/landing_reel/chapters_1_2_preview.jpg.
Renderer: blender/scroll_test/render_scroll_frames.py `chapter=<id>` on blender/out/frozen_FK.blend (or the render pack, branch assets/render_pack).
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

Flicker over 24 frames: 128 samples with haze (scroll_test_01) and the lit dusk run (scroll_test_02) show no frame that stands out. 32 samples, haze off: pending (24-frame run queued after the G2 and phone builds; this line is updated with the result).

File sizes (H.264, measured on the 24-frame day orbit, which moves 1.25 deg a frame, faster than chapters 1 and 2): 1080p CRF 26 with a 2 s GOP is 0.92 MB per second; the 720 x 1280 portrait 0.34 MB per second. So, at most: chapter 1 about 7 MB (portrait 2.7 MB), chapter 2 about 9 MB (portrait 3.4 MB).

Parallel rendering (R3 step 3): yes. A second cloud session in the TALANTA environment runs at the same time on its own machine (probe 2026-10-25: 4 cores, 15 GB, Blender 5.2.3, 29 GB disk). The frames do not depend on each other, so N sessions divide the wall time by N; the CPU hours stay the same. Each session needs the render pack (assets/render_pack, 175 MB in 2 parts).

Interpolation (R3 step 4): not used. Both versions below render every frame at 24 fps.

## Version A: rented RTX 4090 (recommended)

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

## Version B: the 4-core cloud CPU, 30 h or less

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

## Decision needed

1. Version A (GPU, stills quality, about 1 to 4 USD) or version B (cloud CPU, 26 h, lower settings).
2. For version A: the 24-frame GPU test first, on an account Munene sets up.
