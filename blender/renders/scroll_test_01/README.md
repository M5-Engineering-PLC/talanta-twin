# Scroll and reel test 01: 24 Cycles frames, L07 daylight (2026-10-25)

Internal test only. The frames show illustrative people, cars and lights (Visualization), as in hero_artistic_04.
Asked by the user on 2026-10-25 (option 1, scroll-scrub landing; also the first shot of a landing reel).

## What was rendered

`blender/scroll_test/render_scroll_frames.py -- blender/out/scroll_test_01 frames=24 arc_deg=30` on
blender/out/frozen_FK.blend: the hero_artistic_04 L07 set-up (daylight_artistic, hero_artistic prepare, look layer,
haze and glare), at 1920 x 1080, 128 samples adaptive (threshold 0.02), OpenImageDenoise, fixed seed. The camera orbits
the L07 target about the vertical, 30° over 24 frames (1.3° a frame), same height, distance and pitch.
Frames (PNG) and encodes stay in blender/out/scroll_test_01/ (not committed). `contact_sheet.jpg` shows all 24.

## Results

| | |
|---|---|
| Render time per frame | 704 s mean (654 to 830 s), 4-core CPU |
| 24 frames | 16,897 s (4.7 h); scene set-up once, 2 s plus about 2 min of sync in the first frame |
| Fixed cost per frame | about 2 min even at 4 samples (second pass layer, compositor look layer); persistent data saves about 10 s |
| WebP q82, 1920 wide | 239 KB a frame, 5.7 MB for 24 |
| WebP q82, 960 wide (phones) | 80 KB a frame, 1.9 MB |
| AVIF q60, 1920 / 960 | 160 KB / 55 KB a frame |
| H.264 CRF 20, 1080p | 2.2 MB (GOP 12) or 4.0 MB (every frame a key frame, for exact scrubbing) for 24 frames |
| Flicker | no frame stands out: the residual of each frame against the mean of its neighbours is 14.9 to 15.2 (8-bit grey, 960 px), flat across the sequence. Fine shimmer is not separable from parallax by this measure; judge it in the 24 fps clip. |

## What it means for a landing reel

At 704 s a frame on this machine:
- 30 s at 24 fps (720 frames): 141 h. At 12 fps with frame interpolation (360 frames): 70 h.
- The lit L06 sunset look is about 1.7 times slower (78 against 46.5 min at 4K): about 20 min a frame at 1080p.
- A 30 s 1080p H.264 reel is about 70 MB at CRF 20 for this sequence's motion density (2.2 MB per second); a delivery
  encode at CRF 23 to 26 with a normal GOP brings it to about 15 to 25 MB, and a 720p phone cut to about 8 to 12 MB.
- A bigger cloud machine or GPU rendering is needed for a full reel; this 4-core runner suits short shots and tests.

Next: scroll_test_02, the same orbit from L06 in the lit sunset look (started 14:11 UTC).
