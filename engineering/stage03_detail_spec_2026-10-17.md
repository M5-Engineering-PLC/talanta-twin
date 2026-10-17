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
| Speaker clusters hung from the roof (curved white line arrays, lead review correction 4) | - | 02:00, 10:04 | to do (group 2) |
| Pitch-side: perimeter boards (no text), dugouts, technical area, camera platforms off | 03 | 00:46, 13:07 | to do |
| Players and officials on the pitch (matchday camera only) | 03 | - | to do, Visualization |
| Crowd: anonymous fans in red, green and black, flags, one large Kenya flag | 03 | - | to do, Visualization |
| Seat-row LED ribbon between tiers | 03 | - | to do |

### Exterior and site (05, 06, 07, frames 12:12, 12:16, 12:40)

| Element | In concept | Frame check | Status |
|---|---|---|---|
| Fins, lattice, shields, spears, light base with columns | 05, 06, 07 | 10:28, 12:12, 12:16 | done (stage 02b) |
| Smooth roof with radial seams | 05, 06, 07 | 12:40 | done (stage 02b) |
| Forecourt: pale paving, radial paths, planted islands, flag masts | 06 | 12:40; design model 04:45, 05:12, 05:16 | done (detail sheet SR, group 1) |
| Ngong Road dual carriageway with markings and traffic | 06, 07 | 07:04 | road done (group 1); traffic is sheet PL, matchday camera only |
| Suburbs: red and brown tile and iron-sheet roofs, mid-rise blocks | 06, 07 | 07:04 | roofs done (group 1); mid-rise blocks keep their Overture heights |
| Forest sanctuary, racecourse, ridged Ngong Hills | 06 | DEM, Sentinel-2 | to do |
| Palms and street trees along the forecourt | 06, 07 | 12:40; design model | done (group 1) |
| Warm-up track: lanes, infield grass, floodlight masts | 06, 07 | 05:12 (design model) | done (group 1), both tracks |
| Cumulus sky, warm morning colour grade | 06 | 12:40 | partly done (procedural clouds) |

## Detail sheet ids (engineering/detail_sheets, with the lead review)

Status values: done, partly done, not possible. "Done (left out)" means the sheet says to leave the item out.
New values are in gis/parameter_ledger.csv as "estimated (detail sheet <id>)" or "estimated (design model)".

### Group 1: RF roof and facade

| Id | Status | Note |
|---|---|---|
| RF01-RF04 | done | stage 02b fins, drop, dark backing, trapezoid lattice |
| RF05 | not possible | the slim ties behind the lattice are not resolved in 10:28 or 12:12 (count and positions unknown) |
| RF06-RF08 | done | lattice rings, flush joints, lattice ends at the base band |
| RF09-RF12 | done | 8 bulged shields; white spine, leaves and boss; dark side fields |
| RF13 | done | pale rim, bowl.shield.rim 0.3 m (group 1) |
| RF14 | done (left out) | no fasteners |
| RF15-RF18 | done | crossed spears, blades, tips under the fascia |
| RF19-RF21 | done | measured roof outline, opening and depth |
| RF22, RF24 | done | membrane and fascia |
| RF23 | partly done | radial seams at the rib count; the seam count is unknown |
| RF25 | done | night fascia points, white, cyan and violet (Visualization) |
| RF26 | done | dark border round the opening (group 1) |
| RF27 | done | radial ribs with tension cables and purlin rings (10:38 replaced the diamond grid) |
| RF28-RF30 | done | catwalk and floodlight heads at 2.5 m |
| RF31 | done | night light row at the opening edge (Visualization) |
| RF32-RF36 | done | base step, recess, band, base columns, upper colonnade |
| RF37 | done | clean facade with subtle roughness noise |
| RF38, RF39 | done | night wash spots (green, white, red) and shield spots (Visualization) |
| RF40 | done | night membrane glow (Visualization) |
| RF41 | done | light masts and path lights, lamps on at night |

### Group 1: SR site, roads and entrances

| Id | Status | Note |
|---|---|---|
| SR01-SR06 | done | paved forecourt, 1.5 m stone panels with shallow joints, edge band, radial and ring walks, entrance apron |
| SR07-SR10 | done | 8 raised planters, red flower beds by the paths (design model), shrubs, lawns |
| SR11 | done | jets on a wet paved deck without a basin (frame reading, lead review item 9) |
| SR12, SR14 | not possible | render-only basin steps and high arcs; the frames show no basin |
| SR13 | done | 2 rows of 30 jets |
| SR15, SR16 | done | 8 flag masts with plain flags |
| SR17, SR18 | done | 105 path lights, bollards at the avenue end |
| SR19-SR23 | done | Ngong Road from 07:04: 4 lanes each way at 3.3 m, edge and dashed lane lines, central reserve |
| SR24 | done (left out) | crossing positions unknown |
| SR25, SR26 | done | site roads are finished asphalt (lead review item 1), no internal markings |
| SR27 | partly done | kerbs on Ngong Road and the planters; site road kerbs not modelled |
| SR28 | partly done | drain channels on Ngong Road only |
| SR29 | done | central concrete barrier (07:04 overrides the sheet's "no barrier") |
| SR30, SR31 | done (left out) | bus stop and matatu stage not needed by C06, 06 or 07 |
| SR32, SR33 | done | two car parks on the OSM aisles with bay lines and tree rows |
| SR34, SR35 | done | plain palisade fence on the site boundary, broken only where OSM roads and the avenues cross |
| SR36 | partly done | the finished site is lawn (lead review item 1); murram stays on the Ngong Road service strip |
| SR37 | done | superseded by item 1: mature planting |
| SR38, SR39 | done | 315 palms along the paths and the concourse edge; 888 broad-crowned trees in clumps, a boundary belt and car-park rows |
| SR40 | partly done | 2% jacaranda-like crowns (optional seasonal detail) |
| SR41 | partly done | beds along the paths; no separate verge along the boundary fence |
| SR42-SR44 | done | NE warm-up track: 6 lanes, grass infield with pitch markings, 4 floodlight masts |
| SR45 | done | SE training pitch: grass, stripes, markings |
| SR46, SR47 | done | SW: a second track with a grass infield, as in the design model (lead review item 1) |
| SR48, SR49, SR51 | done | two generic canopies on paved aprons at the plaza's road side |
| SR50 | done | 3 blank sign frames on the Ngong Road verge |

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
- blender/renders/stage03_site_a/ (group 1, RF and SR): C06 morning 68 s, C08 75 s, C15 78 s, C17 overcast 75 s, C06 night 98 s, all 960x540 at 32 samples. Side-by-side sheets *_internal.jpg put each render next to its frame and lead render (internal only, AGENTS.md rule 2).
