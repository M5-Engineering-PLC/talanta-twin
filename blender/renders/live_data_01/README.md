# Live data 01: pass G, data for the live twin

These two small JSON files feed the app's light shows and its seated crowd. The lead order of 2026-10-22 set the format. `blender/scripts/export_live_data.py` writes both, reading them from the built bowl (`blender/out/step_FE.blend`). It takes about 40 s.

Run it again after any bowl rebuild:

```
~/.venvs/bpy/bin/python blender/scripts/export_live_data.py
```

## Frame

Both files use the **app frame**, the glTF frame of the exported scene:
- x east, y up (Blender z), z south (Blender -y), in metres;
- origin at the W1b pitch centre;
- y is the absolute scene height; the pitch pad sits at y 6.12.

## app/public/data/facade_lines.json (65 KB)

| Key | Content |
|---|---|
| `ribs` | 48 polylines of 40 points each: 24 rising members first, then 24 falling. Each is the centre line on the facade face, from the foot (y 11.6) to the top V point (y 57.8). Read from the built `lattice` mesh. |
| `fascia` | 259 points round the fascia line (the night fascia lamp line), ordered by bearing |
| `opening` | 194 points round the roof opening ring, ordered by bearing |
| `shields` | 8 shields, each with `center`, outward `normal` (horizontal), `w` about 21.4 m and `h` 46.1 m (lattice foot to the top V point) |
| `floodlights` | 240 heads on the catwalk ring just inside the opening (radius about 46 m, y 52.7). Each has `pos` and a unit `aim`. |

Notes on the fields:
- **Ribs:** they follow the barrel of the facade surface, so they curve. They are not straight chords.
- **Floodlight aims:** the build only tilts the heads down, so the aims are estimated: each points at the pitch at a quarter of its own radius.
- **Floodlight count:** 240 comes from the ledger (`bowl.floodlights.per_bay`). The frames show a continuous row of heads on the opening ring, not a counted set.

## app/public/data/seats.json (4.6 MB)

One record per seat place in the bowl build: `{ x, y, z, facing_deg, tier, row }`.
- **`facing_deg`:** the compass bearing the seated person faces (0 north, 90 east). Every seat faces the bowl centre: all 63,325 are within 20° of it.
- **`row`:** counts from the front of each tier, starting at 1.

| Tier | Seats | Rows | Seat height y (m) |
|---|---|---|---|
| lower | 11,184 | 15 | 7.3 to 17.9 |
| middle | 12,333 | 12 | 26.6 to 34.9 |
| upper | 39,590 (583 of them the media block) | 32 | 39.1 to 49.8 |
| vip | 218 | rows 14 and 15 of the lower tier | 15.6 to 17.9 |
| **total** | **63,325** | | |

The 63,325 places are the build's seat points: 62,524 regular, 583 media and 218 VIP.
- The 624 sky-box places in the build's 63,949 are a capacity estimate, not seat points, so they are not in the file.
- The count is 5.5 % over the narrated 60,000. This is the known capacity gap in blender/STATUS.md.

## Claims

Everything here is **estimated**: these are the build's own values (ledger rows `bowl.*`), not survey data. Crowds drawn from `seats.json` are a Visualization, not a validated occupancy or safety model (AGENTS.md rule 7). The files hold no exits, gates, camera positions or control rooms (AGENTS.md rule 8).
