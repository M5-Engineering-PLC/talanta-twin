# Matchday 01: group 3 (PL rows) on the matchday cameras (Visualization, internal)

Everything in these stills is a Visualization (AGENTS.md rule 7), not a record of a match or a safety simulation.
Occupancy, clothing, props, kits and positions are build estimates from engineering/detail_sheets/04_people_life.md.
Each still has a labelled copy (`*_labelled.jpg`). Use only the labelled copy outside the team, and only once Munene clears it.

Code: `blender/matchday.py` (prepare() runs from render_cycles.py for M cameras only, so the main build and the web bundle never
hold these objects). Cameras: `blender/data/matchday_cameras.json`, from `python3 blender/matchday.py cameras`. M01 and M02 stand
at the front of the north-west middle tier, looking across the pitch. They are viewpoints only, not real camera positions (rule 8).

Rendered from the seat count pass 01 build (61,039 places), 1920 x 1080, 128 samples: M01 neutral 851 s, M02 night 1,084 s.

## What is in it

| PL rows | Built | Count |
|---|---|---|
| PL-01 to PL-05, PL-10 | seated fans on the seat points, occupancy 90 / 90 / 85 % by tier with +-5 % by block, tier clothing mix | 52,283 fans, 7,914 empty seats |
| PL-06 | scarves held overhead, plain colours | 3,222 (1 in 16) |
| PL-07 | small hand flags, plain Kenya stripes | 1,660 (1 in 32) |
| PL-08 | one large flag, 15 x 10 m over an east lower-tier block, plain stripes | 1 |
| PL-09 | vuvuzelas | 1,295 (1 in 40) |
| PL-11 to PL-15 | two plain kits (red/black, white/green), goalkeepers, a loose 4-4-2 leaning to the ball | 22 players, 3 officials |
| PL-16 to PL-19 | stewards in plain vests at seeded spots round the run-off, ball attendants, small crew groups on the east side | 9, 5, 12 |
| PL-39, PL-42 (M02 only) | cool-white phone lights | 931 (1 in 60) |
| IF18 / IT07 | LED ribbons on (their "matchday:" emission) | |

Left out on purpose: faces, numbers, names, badges, sponsor marks, slogans and text of any kind. The Kenya flags have no shield
and spears. There are no fixed steward posts, gates, exits, cameras or control positions.

## Gaps

- M02: the pitch is under-lit for a match. The catwalk floodlights in the build are too weak at night; a night lighting pass
  should raise them before M02 is used.
- Figures are low-poly blocks (seated fans about 60 triangles, standing figures about 90). They read well at bowl scale.
  Close views (C12 distance) need better bodies.
- The VIP seats (218) and the sky boxes have no fans.
- PL-20 to PL-38 (forecourt life, traffic, parking) are not in this pass. The step H stills hold the plaza people and parked cars.
