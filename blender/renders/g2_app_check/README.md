# G2 app check (2026-10-26)

Bundle web_hero_v2_1 (branch assets/web_hero_v2_1) staged with blender/web_hero/stage_app_preview.py and shot in hero mode with blender/web_hero/node/shot_hero.mjs (headless Chromium, software GL, 1920 x 1080, saved at 1440 x 810). Internal check images. People and vehicles are Visualization.

- app_L07_hero_0730.jpg (key 3, Cityside): the trees are green and shaded: the instanced protos, the site trees and the impostor forest. Before G2 they were black.
- app_L06_hero_0730.jpg (key 2, Hillside): the far forest (impostors) is green. The near forecourt trees are almost black. They face away from the 07:30 sun in this view and have no lightmap (instanced trees), and the app has no leaf translucency, so only the environment light reaches their shaded side. Measured albedo: leaves 0.02 to 0.11 linear (dark leaf green). This is an app lighting limit, not an export error. Options for the lead: a translucency or wrap term for the @tree materials in the app, or more environment light on unlit instances.
