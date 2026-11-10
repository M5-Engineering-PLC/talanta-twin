# Kaggle GPU render test: result (2026-10-25)

Date: 2026-10-25
From: the local lead session, for Munene and the cloud build chat
Branch: `wo/web-hero-v2`
Related: engineering/lead_decision_2026-10-25_walkthrough.md (section "Render power"), blender/kaggle/talanta_gpu_render_test.ipynb

## What ran

- Machine: Kaggle notebook, GPU T4 x2 (2 x Tesla T4, 16 GB each), Blender 5.2.2, OptiX on both GPUs.
- Input: the private dataset `talanta-render-pack` (the cloud render pack 7e19362, sha256 checked on the laptop).
- Scene: the 24-frame L07 orbit at the scroll_test_01 settings, 1920 x 1080, persistent data on.
- The test rendered frames 0 to 4 only, to save GPU hours. The full 24 frames did not run.

## Result

| Run | Settings | Time for each frame |
|---|---|---|
| Step 1, frame 0 only | 128 samples, haze on | 228.8 s (first start: OptiX kernel load) |
| Step 2, frames 0 to 4 | 128 samples, haze on | 59.9, 54.7, 54.4, 54.4, 54.4 s |
| Step 3, frames 0 to 4 | 48 samples, haze volume off | 29.9, 22.6, 22.3, 22.3, 22.3 s |
| Cloud CPU, scroll_test_01 | 128 samples, haze on | 704 s |

- At the same settings, the Kaggle GPU is about 13 times faster than the 4-core cloud CPU (54.4 s against 704 s).
- With the cheap settings, it is about 32 times faster (22.3 s against 704 s). The cheap settings change the image. The R3 lever test on the cloud must approve them first.
- The first frame of each new Blender run is slower. Render many frames in each run.

## What this means for the walkthrough film

| Frames | Full settings (54.4 s) | Cheap settings (22.3 s) |
|---|---|---|
| One chapter of 8 s at 24 fps (192 frames) | about 2.9 h | about 1.2 h |
| Chapters 1 and 2 (384 frames) | about 5.8 h | about 2.4 h |
| Chapters 1 to 6 (about 1,150 frames) | about 17.4 h | about 7.1 h |

- Kaggle gives 30 GPU hours each week, free. Chapters 1 and 2 at full settings fit in one week.
- These times are for the daylight L07 orbit. The lit sunset look was about 1.7 times slower on the CPU. Expect about 90 s a frame for it on the GPU. Measure it.
- The GPU rental (option 1 in the walkthrough decision) is not necessary for chapters 1 and 2.

## Rules for Kaggle renders

- The dataset and the notebook stay private. Do not publish the notebook or save a public version.
- Stop the session after each run. An idle session uses GPU hours.
- Files in /kaggle/working are lost when the session stops. A real render run must save the frames as notebook output or download them before the stop.
- People, cars and lights in the frames are Visualization. The frames are internal until a review approves them.

## Next

1. Cloud: write RENDER_ORDER.md for chapters 1 and 2 with the Kaggle GPU as the main machine, in runs of less than 9 h.
2. Cloud: finish the R3 lever test. It decides between the full and the cheap settings.
3. Lead: add a frame download step to the notebook before the first real render.
