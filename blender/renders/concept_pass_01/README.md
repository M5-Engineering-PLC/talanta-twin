# Concept match, pass 1: framing and light

Plan: engineering/plan_concept_match_2026-10-17.md. Renders are Visualization (artistic light and grade).
The Kenyan Historian footage decides geometry; concepts 06 and 07 decide theme and look only.

| File | What |
|---|---|
| C19_morning_golden_check.png | C19, 2026-01-15 07:30 EAT, kloppenheim_06 sky, 960 x 540, 32 samples, lookdev on |
| C20_evening_golden_check.png | C20, 17:30 EAT, wasteland_clouds sky, same settings |
| C19_side_by_side.jpg, C20_side_by_side.jpg | render, concept (06, 07) and the closest historian keep frame (000641.633, 001244.833); yellow: frozen crops, cyan: stadium box |
| metrics.csv | per crop LAB and edge density, bbox error, horizon, shadow direction, clipping, render time |
| scores.csv | the eight-category score (engineering/review_astra_hyperreal_2026-10-17.md) |
| render_log.jsonl | sky preset, HDRI rotation, sun energy and colour, haze colour, seconds |

Reproduce:
```
~/.venvs/bpy/bin/python blender/concept_match/solve_cameras.py   # C19 and C20 poses -> app/cameras/manifest.json
TALANTA_LOOKDEV=1 ~/.venvs/bpy/bin/python blender/render_cycles.py blender/renders/concept_pass_01 C19 morning_golden check
TALANTA_LOOKDEV=1 ~/.venvs/bpy/bin/python blender/render_cycles.py blender/renders/concept_pass_01 C20 evening_golden check
~/.venvs/gis/bin/python blender/concept_match/metrics.py blender/renders/concept_pass_01
```

Internal only: the concept and frame tiles in the side-by-sides never leave this private repository (AGENTS.md rule 2).
