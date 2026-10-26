# Scroll and reel test 02: 24 Cycles frames, L06 lit sunset (2026-10-26)

Internal test only. People, cars and lights are Visualization, as in hero_artistic_04 (L06, sunset_artistic,
2026-01-15 18:05, fixtures on). The lit counterpart of scroll_test_01, for the internal Kenyan-style test reel.

## What was rendered

`blender/scroll_test/render_scroll_frames.py -- blender/out/scroll_test_02 frames=24 arc_deg=30 cam=L06 preset=sunset_artistic`
on blender/out/frozen_FK.blend: the hero_artistic_04 L06 set-up (prepare, look layer, haze volume and its pass layer,
glare), 1920 x 1080, 128 samples adaptive (0.02), OpenImageDenoise, fixed seed, persistent data. 30 deg orbit about
the L06 target. Frames and encodes stay in blender/out/scroll_test_02/ (not committed). `contact_sheet.jpg` shows all 24.

The run was interrupted twice by container restarts (14:47 before frame 1, about 18:50 after frame 11) and resumed
from the written frames (render_scroll_frames.py keeps them). Frames 1 to 3 shared the CPU with other jobs.

## Results

| | |
|---|---|
| Render time per frame, CPU to itself | 1,021 to 1,110 s (median of all 24: 1,070 s); frames 1 to 3 with other jobs: 1,404 to 2,087 s |
| Against daylight (scroll_test_01, 704 s) | 1.5 times slower (fixtures, the dusk haze and glare) |
| WebP q82, 1920 / 960 wide | 174 KB / 59 KB a frame |
| AVIF q60, 1920 / 960 | 125 KB / 43 KB a frame |
| H.264 CRF 20, 24 frames | 1.8 MB (GOP 12) or 3.4 MB (every frame a key frame) |
| Flicker | none stands out: residual against the mean of the neighbours 9.3 to 10.1 (8-bit grey, 960 px), smooth over the sequence |

The lit frames compress better than daylight (darker, softer far land). For the walkthrough, a dusk chapter costs
about 18 min a frame on this machine, so it belongs on the GPU plan (blender/landing_reel/RENDER_ORDER.md).
