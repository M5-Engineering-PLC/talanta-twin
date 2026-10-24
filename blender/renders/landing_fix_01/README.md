# Landing fix 01: replica plan pass E (internal)

Pass E of the lead order of 2026-10-20, finished state only. Internal only: the sheets hold the landing mockups.
No 4K and no W. This is the last pass of the order.

## What changed (`blender/context/landing_look.py`, dusk switch in `render_cycles.py`)

- **Warm uplights on the facade at dusk.** 48 spot lamps (two per lattice bay) stand on the ground 2 m outside the facade's widest ring and aim up the louvres.
  - Light: 3000 K, 48 deg cone, 30 kW in Blender units. They are Visualization.
  - Each lamp carries `night_energy` and `dusk_energy`. `render_cycles.py` now applies `dusk_energy` when a preset switches the fixtures on before night (L06 `sunset_landing`).
  - The RF38 coloured base wash keeps its night colours but gets `dusk_energy` 0, so dusk reads warm.
- **Warm glow in the ground-floor recess** under the ring beam: an emission on the recess material, on at dusk and at night only (`night:2.5`).
  No doors, gates, exits or signs are modelled.
- **People** (collection `people_visualization`): 2600 generic figures on the finished plaza and path surfaces, denser toward the bowl.
- **Parked cars** (collection `parked_cars_visualization`): 226 generic cars along the bay lines of the east car park, 72 % occupancy.
- **Labels:** people and cars are labelled Visualization. They are not a crowd count, an occupancy figure, or an evacuation or safety simulation (AGENTS.md rule 7). Both collections are finished-state only (`scene_state.py`).

## Renders (finished state, 1080p)

- Scene: `blender/out/step_FE.blend` = `step_FD` plus `landing_look.py`.
- Cycles 1920 x 1080 hero, 128 samples, look layer on.

| Render | Camera | Light | Time |
|---|---|---|---|
| L06_sunset_landing_hero.png | L06 | sunset_landing 18:05 (fixtures on: dusk) | 10.9 min |
| L07_daylight_landing_hero.png | L07 | daylight_landing 10:30 (fixtures off) | 9.6 min |

**Uplights, tested in L06 check renders:**
- At the plinth ring they lit only the soffit under the ring beam, which overhangs the plinth by up to 5.6 m.
- 9 kW read too faint.
- They now stand outside the widest ring, at 30 kW.

## Acceptance: same layout, roof read, shield read and context density as the mockups

Side-by-side sheets are in `sheets/`. Read by eye:

| | L06 | L07 |
|---|---|---|
| **Layout** | Bowl, plazas, NE track and lamp rows as before. The south-west is now the traced lawn and loop road; the mockup shows the same loop. | The south-west lawn pitch and loop road are in the foreground; the mockup shows a car park and a road there. |
| **Roof read** | Pillows read in every row (pass B). | Pillows read in every row. |
| **Shield read** | Pointed lens, crimson and black (pass A). | Pointed lens, crimson and black. |
| **Context density** | Clustered forest crowns, green to olive far land, blue-grey hills (pass D). | Denser, darker mid-rise, a taller cluster at the right edge, trees between (pass D). |
| **Landing look** | Warm recess glow, warm wash at the facade foot, people on the plazas. | Fails against the mockup: the people are hardly visible at this distance and the east car park is outside the frame. The mockup shows a full car park in the foreground (gap 6). |

## Gaps (honest list)

1. **Uplights are weaker than the mockup.**
   - The mockup shows the whole facade glowing warm. Ours lights the lower facade and the recess.
   - The light is limited by the AgX grade and the bright sunset sky.
   - A brighter facade would need a stronger dusk exposure, which belongs to the grade.
2. **People and cars are generic low-poly masses.** Fine at landing distance, but not for close views.
3. **Sky:** the mockup's sunset sky is more saturated, with orange clouds. Ours is the CC0 Wasteland Clouds HDRI under the unchanged grade.
4. **Far land** reads olive-beige under the low sun (pass D, gap 1).
5. **Mockup elements not modelled:**
   - the lit glazed concourse;
   - its doors and entrances (excluded by the no-exits rule);
   - the traffic queues and the mockup's road layout south of the loop.
6. **L07 has no visible car park or crowd.** The mockup's foreground car park is not in our layout. The trace shows a lawn and loop road there, and the frames win. People are too small to read at L07's distance.
