# People final 01: pass H, CC0 figures and crown detail (finished state, Visualization)

Lead order of 2026-10-22, pass H. The scene is **step_FH**: step_FF (pass F) plus `blender/context/people_figures.py` plus `blender/context/crown_detail.py`.

## People

The stick figures of pass E are replaced by real low-poly people. People are a **Visualization**: not a crowd count, not occupancy, not an evacuation or safety simulation.

**Source:** Quaternius **Background Posed Humans**, CC0 1.0.
- Ten posed figures, 510 to 734 polygons each: men and women standing, walking, hands on hips, waving and looking up.
- The licence and source are in `blender/assets/CREDITS.md`, and the pack's `License.txt` is in `blender/assets/people/`.
- The figure files are binaries and are not committed. Fetch them with `blender/assets/fetch_people_quaternius.sh`.

**Scatter:** 4,200 people, instanced with geometry nodes on points over the finished walking surfaces:
- the plaza, the murram paths, the bowl apron and the forecourt paving;
- the station forecourt, weighted 2.5 times, because the photo shows a crowd there.

Density falls off with distance from the bowl. About a third stand in small groups. Walkers head toward or away from the bowl. This is about the density of the dusk photo's forecourt; the plaza in front of the bowl is somewhat denser than the photo.

**Variation:**

| Attribute | Values |
|---|---|
| Pose mix | 39 % walking, 36 % standing, 11 % hands on hips, 9 % looking up, 5 % waving |
| Height | men about 1.74 ± 0.07 m, women about 1.62 ± 0.06 m |
| Shirts | 11 colours, including Kenya red, green and black, white and blue |
| Trousers | 6 colours |
| Skin | 5 dark-brown tones |

The colours are instancer attributes read by the figure materials (`hum_shirt`, `hum_pants`, `hum_skin`).

## Tree crowns

The order says the clustered crowns of pass D read as soft blobs in the D02 and D03 foregrounds.
- **Leaf materials:** the forest, site and suburb leaf materials (9 of them) get leaf masses in object space:
  - a coarse distorted noise, masses of about 0.6 m, sets the tone from 0.5 to 1.2 times the leaf colour;
  - a fine noise adds leaf grain;
  - both drive a soft bump.
- **Voronoi tried first:** a Voronoi cell pattern was tried and rejected; it read as a tortoise shell.
- **Outlines:** the two crown meshes of the trace trees nearest the cameras get their leaf vertices pushed in and out by a smooth noise (±0.35 m), baked into the mesh, so the outlines break up. The forest instances share those meshes, so every round and acacia crown changes too. Trunks stay straight.
- **Modifiers rejected:** subdivision and Displace modifiers were tried first. On the shared meshes they took about 10 GB at render and broke the P01 render (out of memory). The baked version renders at 2.5 GB.
- **Unchanged:** crown size and tree positions do not change.

## Renders (1080p, Cycles 128 samples, look layer on, step_FH)

| Render | Camera | Light | Time |
|---|---|---|---|
| P01_sunset_landing_hero.png | P01 (dusk photo camera, 1920 x 1288) | sunset_landing | 16.5 min |
| D02_daylight_landing_hero.png | D02 | daylight_landing, -1.2 EV | 9.5 min |
| D03_daylight_landing_hero.png | D03 | daylight_landing, -1.2 EV | 12.9 min |

`sheets/P01_vs_photo_internal.jpg` sets the people against the photo; it is internal, because it contains the photo.

## Gaps

1. **The figures are static poses**, with no animation. From drone height they read as people; within about 30 m they read as low-poly.
2. **Their clothes are flat colours**, with no prints or texture.
3. **Their hair is one dark colour.** The female figures have no separate hair material; it is part of the skin mesh.
4. **People stand only on the walking surfaces.** There are none on the car parks, the platform or the footbridge. That avoids figures in vehicles or on the tracks, but the photo has some people in the car park aisles.
5. **The crown fix is mainly a shading fix.** The silhouettes are still rounded clusters, and the forest instances away from the trace trees keep their smooth outlines.
