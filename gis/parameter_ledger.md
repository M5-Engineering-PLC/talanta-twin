# Parameter ledger (stage 00)

Date: 2026-10-17
Files: `parameter_ledger.csv` (rebuild with `gis/scripts/build_parameter_ledger.py`), `app/cameras/manifest.json` (rebuild with `gis/scripts/build_camera_manifest.py`).

The ledger has one row for each dimension that the model uses. Measured facts outrank looks: Blender (stage 01) reads this file, and an estimated value keeps its "estimated" label through Blender, glTF and the app.

## Columns

name, value, unit, source, date, method, uncertainty, status (measured, derived or estimated), used_in (the file and symbol that use the value), note.

- **measured**: Munene's Google Earth Pro W1b shapes, recomputed in EPSG:32737 from `gis/measurements/`.
- **derived**: computed from measured values or fixed by a rule (Laws of the Game, DEM).
- **estimated**: read from frames or assumed. These are the values that stage 01b (camera match) must replace.

Frame: origin at the W1b pitch-zone centroid, x = east, z = south, y = up. Blender uses (x, -z, y).

## Coverage

Every dimension constant in `app/src/world/bowl.js`, `site.js` and `pitch.js` has a row. Not included: canvas texture sizes and colours inside the texture painters, fountain and crowd animation constants, and mesh tessellation counts other than `N`. None of these is a dimension of the stadium.

## What the W1b numbers change (for stage 01)

| Item | Twin today | Ledger (measured) | Action in the blockout |
|---|---|---|---|
| Bowl outline at ground | OSM, 256.3 x 203.4 m, centroid 4.0 m E | Plinth 253.0 x 202.8 m, centroid 2.2 m W | Use the W1b plinth outline; the OSM outline sits about 6 m east |
| Roof opening | 126 x 80 m (rounded rectangle from Sentinel-2 area) | 130.0 x 88.1 m, 10,443 m2 | Use the measured ring after removing the relief shift |
| Roof outer ring | follows the OSM outline | 250.1 x 214.5 m | Roof edge overhangs the plinth by about 6 m on the long sides, none at the ends (check in 01b) |
| Roof-level positions | | shifted 13.9 m E, 26.3 m N on the oblique image | Subtract the shift from the roof rings |
| North plaza | eye shape 184 x 92 m | 102.5 x 92.9 m, centroid 205 m N | Use the measured outline |
| Training field SW | not modelled | 180.3 x 101.2 m, earthworks | Add as estimated surface |
| Heights (plinth, bulge, roof top 54 m, opening 47 m) | estimated | none yet | Keep estimated; stage 01b derives them from the historian frames |

## Cameras

`app/cameras/manifest.json` freezes C01 to C16 from the Astra review: four orthographic elevations, an orthographic roof plan, four elevated diagonals (C06 is the hero), two views across the bowl, a seat section, the roof underside, a shield detail, the forecourt and the approach. Each camera has a position, target, lens on a 36 mm sensor, resolution, exposure, sun state and seed. These are render viewpoints for review, not real camera locations (AGENTS.md rule 8).

Checks (both pass on 2026-10-17): `node cameras/check.mjs` from `app/`, and `~/.venvs/bpy/bin/python blender/scripts/check_cameras.py` from the repository root. Both put every target at the frame centre, and the vertical field of view agrees to 0.01 degree.
