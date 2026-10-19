# Environment pass against the drone footage (2026-10-19)

Owner: Munene. Asked for before any more look work: confirm the environment of the twin against the Kenyan Historian
drone footage (video JWNowpO44rw, January 2026).
Status: comparison done for three drone views; fixes listed in order, not yet built.
Frames are internal reference only (AGENTS.md rule 2). The side-by-side sheets stay in blender/renders/environment_pass_01/.

## Method

- Three as-built drone frames with the most environment in them:
  - 000645.000: north of the site over Ngong Road, looking SSW across the north plaza to the forest.
  - 000714.767: south of the bowl over the forest, looking N to the city.
  - 000617.567: high overview, east of the bowl, looking W.
- Cameras D01 to D03 in app/cameras/manifest.json, solved with blender/concept_match/solve_cameras.py drone: the stadium
  box and sky band of each frame, and for D01 and D03 also ground landmarks measured in Google Earth (W1b): the north
  plaza round bed and the warm-up track. 24 start bearings, best fit kept. Residuals in blender/data/drone_cameras.json.
- Render: CPU Cycles, 960 x 540, 32 samples, the overcast preset (the footage is overcast), look layer on.
- File names: the environment notes of 2026-10-17 give frame IDs in seconds; the files use minutes and seconds
  (434.767 s is JWNowpO44rw_000714.767.jpg). This pass uses file names.

## Orientation check (Munene asked: is the model turned or mirrored?)

No. The model is oriented correctly. Evidence:

- W1b coordinates (Google Earth, image 2025-12-26): the traced "shield on ground" plaza centroid is at latitude -1.30383,
  about 245 m north of the pitch zone (-1.30602). The warm-up track is north-east. Ngong Road (OSM) runs along the north
  side, 278 m from the pitch centre at bearing 348 deg; it is the only dual carriageway near the site.
- 000645.000 (D01) lines up with the model from the north: warm-up track left, north plaza with its round bed and two
  axial beds right, Ngong Road in the right foreground.
- 000617.567 fits only from the east looking west: Ngong Road runs away at the top right (north), the forest is top left
  (south-west), the warm-up track is right foreground (north-east) and the north plaza is right of the bowl.
- The first D02 solve was wrong: it was moved to the north side because engineering/forecourt_layout_2026-10-18.md calls
  the plaza in 000714.767 the north plaza. The city behind the bowl and the forest in the foreground show the drone was
  south of the bowl. That plaza is a south plaza (below).

## Result of the solves

| Camera | Frame | Fit | Reading |
|---|---|---|---|
| D01 | 000645.000 | cost 39 (box and plaza landmarks pull apart a little) | North side matches: warm-up track left, north plaza right, Ngong Road in front |
| D02 | 000714.767 | cost 0.008 | South side: the city sits behind the bowl as in the footage |
| D03 | 000617.567 | cost 2.3 with the two W1b landmarks | East side: field rectangle left, track right, north plaza beside the bowl, Ngong Road and the city top right, forest left. This confirms the orientation |

Sheets: blender/renders/environment_pass_01/D0N_vs_<frame>_internal.jpg (internal only).

## Findings

Ordered by how much of the frame each one covers. "As built" is the January 2026 footage. The site itself was built on
purpose as the finished design (Stage 03, group 1); the surroundings must match as built.

| # | Element | Footage (as built) | Twin today | Verdict | Fix |
|---|---|---|---|---|---|
| E1 | Forest belt south and south-west | Dense, dark, unbroken canopy behind the bowl to a flat horizon (000645.000, 001232.600) | Scattered round crowns, then open beige land | Wrong | Continuous canopy mass (instanced broadleaf, dense) over the forest polygon; dark green; no gaps |
| E2 | Far land and horizon | Flat, hazy, green-grey; the Ngong Hills only faint, often not visible | Beige plain and a strong hill ridge | Wrong | Far land green-grey, not beige; hills lower contrast and more haze (lookdev aerial bands) |
| E3 | Plazas | Three: the W1b north plaza (round bed, two axial beds), a matching south plaza, and an eye-shaped paved east approach (000617.567) | North plaza only | Missing | Add the south plaza (mirror of the north, labelled estimated until W1b measures it) and the east approach; ask Munene to trace both in Google Earth |
| E4 | City north of Ngong Road | Dense mid-rise blocks, 8 to 20 storeys, over a carpet of red and grey roofs with tree cover, up to the road (000714.767, 000617.567) | Sparse white boxes far off | Wrong | Denser suburbs.py near Ngong Road, more mid-rise blocks from Open Buildings heights, roof colour mix from the 2026-10-17 notes |
| E5 | Ngong Road | Dual carriageway, planted median, streetlights, billboards and the site fence along the north edge (000645.000) | Road with box traffic; median and billboards missing | Partly | Median planting, streetlights, the fence; billboards without text |
| E6 | Trees in the site | Few; young or absent (000645.000) | Many round trees everywhere | Design intent | Keep for the finished-design state, but use the real species shapes (roadside eucalyptus rows, broadleaf, palms); see E1 |
| E7 | Site ground | Red murram earthworks with green lawn wedges and red paths | Grey paving and green lawn | Design intent | Keep the finished state; add an as-built preset (murram) for comparisons |
| E8 | Training fields | Warm-up track NE under construction; south-west: lawn rectangle with a road loop and a grandstand (000714.767); a small stadium with stands south-west (000617.567) | Finished pitch and track; no grandstand | Partly | Grandstand and road loop at the SW field (estimated from frames) |
| E9 | Roof | Quilted cushion panels with radial ribs (001232.600, 000617.567) | Smooth membrane with faint seams | Wrong | Cushion panels between the ribs (bowl detail); the landing mockup 06 is right here |
| E11 | East approach and the buildings at its foot | Eye-shaped paved approach from the east, long dark-roofed buildings along its outer edge, a parking yard (000617.567) | Missing | Missing | Paved approach and plain building masses only; no gate, turnstile or access detail in public output (AGENTS.md rule 8) |
| E12 | Small stadium south-west | A second pitch with a stand and a white roof, south-west of the bowl, in the forest edge (000617.567, 000714.767) | Missing | Missing | Stand mass and roof over the SW training field, estimated from frames |
| E10 | Sky | Overcast, grey | HDRI cloud presets | Look only | No change for the look target; overcast preset for comparisons |

## Order of work

1. E1, E2: the largest areas of the frame, and they decide whether the twin reads as Nairobi.
2. E9: the roof is the most visible part of the stadium itself.
3. E3, E4, E11, E12: the plazas, the east approach, the small stadium and the city, with W1b traces from Munene for the south plaza and the east approach.
4. E5, E8.
5. E6, E7: an "as built" switch for comparisons; the landing keeps the finished design.

After each step: re-render D01 to D03 and the landing stills L06 and L07, and add the sheets to this folder.
