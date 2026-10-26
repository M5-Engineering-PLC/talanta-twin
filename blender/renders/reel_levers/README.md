# Reel cost levers (R3 step 2, 2026-10-26)

Internal test only. Frames of the 24-frame, 30 deg L07 day orbit of scroll_test_01 (same camera positions), rendered
with blender/scroll_test/render_scroll_frames.py options; logs in the JSON files, frames in blender/out/reel_levers/
(not committed). People, vehicles and lighting are Visualization.

| Test | Options | Frames | s per frame |
|---|---|---|---|
| baseline (scroll_test_01) | 128 samples, haze volume, persistent data | 24 | 704 mean (frames 0 to 2: 704, 693, 686) |
| p0_haze_s128 | persistent=0 | 0-2 | 770 (shared CPU), 691, 682 |
| h0_s128 | haze=0 | 0-2 | 374, 375, 369 |
| h0_s48 | haze=0 samples=48 | 0-4 | 218 to 231 |
| h0_s32 | haze=0 samples=32 | 0-4 | 148 to 160 |
| h0_s48_portrait | haze=0 samples=48 res=720x1280 | 0-2 | 91 to 98 |

Look (look_crops.jpg: facade, far land and sky, foreground trees; frame 0): mean absolute difference of the whole
frame against "128, haze off": 1.46 for the haze version, 1.22 for 48 samples, 1.35 for 32 samples (8-bit). The
haze volume barely shows in this day view; 32 and 48 samples are clean after the denoiser, with slightly softer
grass. Persistent data saves nothing measurable. Use: blender/landing_reel/RENDER_ORDER.md.
