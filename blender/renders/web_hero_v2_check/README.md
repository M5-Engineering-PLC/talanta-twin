# web_hero_v2 check shots (W4, engineering/cloud_web_hero_v2_2026-10-24.md)

Internal reference only. Do not use these images in a pitch or on a public page.

- `web_hero_v2_vs_hero_artistic_04_sheet.jpg`: the approved Cycles stills (blender/renders/hero_artistic_04, L06
  sunset, L07 daylight) on the left, the web build in the app on the right.
- `L06_web_hero_v2_app.jpg`, `L07_web_hero_v2_app.jpg`: the app screenshots at full size, with logs
  `shot_L06.log` and `shot_L07.log`.

How they were made: `python3 blender/web_hero/stage_app_preview.py web_hero_v2`, `npx vite --port 5199 --host
127.0.0.1` in app/, then `node blender/web_hero/node/shot_hero.mjs "http://127.0.0.1:5199/?hero&mode=full" out.png
30000 key=2` (L06) and `key=3` (L07). The baked light is 07:30 (morning_golden) for both. Headless Chromium on
SwiftShader (software GL). Checks, load times and gaps are in blender/web_hero/WEB_HERO_V2.md (W4).
