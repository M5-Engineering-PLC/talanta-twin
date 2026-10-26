# parity/: Cycles references for the app colour match (P1 cloud, 2026-10-26)

Internal reference only. Not for a build or a public page. ref_still: people, vehicles and lighting are illustrative (Visualization).
Script: blender/web_hero/render_parity_refs.py on wo/web-hero-v2. Look block: blender/web_hero/look_v2.json.
All 1920 x 1080, no haze (haze volume and its pass layer off, compositor distance haze 0; glare, streaks, vignette, grain, dispersion kept).

- ref_bake_L07.png, ref_bake_L06.png: the web export state lit as the 07:30 bake (morning_golden), exposure from the look block (L07 -1.1 EV, L06 -1.6 EV), AgX High Contrast.
- ref_still_L07.png: the hero_artistic set-up at 10:30 (daylight_artistic). ref_still_L06.png: 18:05 (sunset_artistic, with fixtures, people and cars).
- parity_log.jsonl: one record per image (time, preset, exposure, samples, render seconds: 438, 395, 392, 1110 s on the 4-core cloud CPU).
