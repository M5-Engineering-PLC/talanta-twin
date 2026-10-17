# Stage 03 detail spec: the Codex/Astra concept level of detail

Date: 2026-10-17
Branch: claude/hopeful-archimedes-lo15is
Asked by: Munene. Replicate the level of detail of the Codex/Astra concept images (research/concepts/2026-10-17/03, 05, 06, 07), inside the stadium first.

## Rules

- The concept images set the level of detail and the mood only. They are internal (AGENTS.md rule 2) and are never textures.
- Shapes, sizes and colours come from the ledger. Where the ledger is silent, take values by eye from the named historian frames and label them "estimated".
- Where a concept image and a historian frame disagree, follow the frame. Examples: 03 shows a dark plinth and an arched clerestory, and the frames show a light base and a louvred colonnade.
- The full Blender build keeps all detail (blender/out/talanta_detail.blend, talanta_scene.blend). The web build is a separate light export made later.
- Crowds are labelled "Visualization". There are no exits, gates, security cameras or control rooms in any public output (rules 7 and 8).

## Checklist

Status values: done, in progress, to do.

### Bowl interior (03, frames 00:46, 02:00, 08:00, 09:12, 10:04)

| Element | In concept | Frame check | Status |
|---|---|---|---|
| Individual seats, about 58,000, tier colours with speckle mix | 03 | 02:00, 08:00 | done |
| Pale stepped treads, aisles with half-steps and handrails | 03 | 08:00, 09:12 | done |
| Pitch: mowing stripes, Law 1 markings, goals with nets | 03 | 00:46 | done (nets to do) |
| Roof underside: radial ribs with tension cables and struts, ring purlins, glowing membrane | 03 | 10:04, 10:38, 10:55 | done (the first diamond grid was replaced after 10:38) |
| Catwalk ring with floodlight heads near the opening | 03 | 10:04 | done (C13 check) |
| Light string along the opening edge (03 point lights) | 03 | 11:20 (LED ring at night) | to do |
| VIP band: lit glazing, white round columns, white fascia | 03 | 09:12 | columns and white bands done; lit interiors to do |
| Upper colonnade with louvred screen to the roof | (03 shows arches) | 08:00 | done (C13 check) |
| Upper gallery walkway with white railing, colonnade outside it (the 10:55 view, camera C18) | - | 10:55 (Munene's screenshot, not in the repository) | done (C18 check) |
| Video boards under the roof at both ends, 20 x 11 m | - | 10:38, 10:55 | done; smaller in C18 than in 10:55 |
| Speaker clusters hung from the roof | - | 02:00, 10:04 | to do |
| Pitch-side: perimeter boards (no text), dugouts, technical area, camera platforms off | 03 | 00:46, 13:07 | to do |
| Players and officials on the pitch (matchday camera only) | 03 | - | to do, Visualization |
| Crowd: anonymous fans in red, green and black, flags, one large Kenya flag | 03 | - | to do, Visualization |
| Seat-row LED ribbon between tiers | 03 | - | to do |

### Exterior and site (05, 06, 07, frames 12:12, 12:16, 12:40)

| Element | In concept | Frame check | Status |
|---|---|---|---|
| Fins, lattice, shields, spears, light base with columns | 05, 06, 07 | 10:28, 12:12, 12:16 | done (stage 02b) |
| Smooth roof with radial seams | 05, 06, 07 | 12:40 | done (stage 02b) |
| Forecourt: pale paving, radial paths, planted islands, flag masts | 06 | 12:40 | to do |
| Ngong Road dual carriageway with markings and traffic | 06, 07 | 07:04 | markings done; traffic to do |
| Suburbs: red and brown tile and iron-sheet roofs, mid-rise blocks | 06, 07 | 07:04 | to do (buildings render white) |
| Forest sanctuary, racecourse, ridged Ngong Hills | 06 | DEM, Sentinel-2 | to do |
| Palms and street trees along the forecourt | 06, 07 | 12:40 | to do |
| Warm-up track: lanes, infield grass, floodlight masts | 06, 07 | 05:56 (model, look only) | to do |
| Cumulus sky, warm morning colour grade | 06 | 12:40 | partly done (procedural clouds) |

## Render budget

- CPU Cycles in the cloud (4 CPUs).
- Check renders: 960x540 at 32 samples, about 100 s.
- Look renders: 960x540 at 64 samples, under 5 min.
- Hero renders: 1920x1080 at 128 samples. Time to be measured. Run them overnight if they take long.

## Height changes from the 10:55 view

The 10:55 view puts the far roof edge and video board under the near roof. Our heights blocked that sight line, so the Blender build overrides two bowl.js estimates (ledger rows *_blockout, both within the stated uncertainty):

- bowl.opening_y_blockout 50 m (bowl.js 47 m). This also gives the flatter roof seen in 12:40.
- bowl.tier_upper.y1_blockout and bowl.back_wall_h_blockout 44 m (bowl.js 46 m).

G2 still passes: roof top 53.1 m, opening edge 50.0 m.

## Check renders

- blender/renders/stage03_bowl_a/: C10 110 s and C12 97 s (seats, aisles, pitch).
- blender/renders/stage03_bowl_b/: C13 84 s and C10 102 s (roof steel, catwalk, floodlights, VIP columns, colonnade).
- All at 960x540, 32 samples, neutral sun.
- blender/renders/stage03_c18/: C18 upper gallery view, about 105 s.
