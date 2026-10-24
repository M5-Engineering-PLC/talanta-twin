# Landing pass 02 (internal)

Landing stills L06 (sunset_landing, 18:05) and L07 (daylight_landing, 10:30) at 1920 x 1080, one folder per step of
Munene's 2026-10-19 work order (G, L, T, B, R, H, W). Each folder holds the two renders and `L0N_vs_mockup_<step>_internal.jpg`,
the render next to landing mockup 06 or 07.

Internal only. The mockups are look and layout targets. Their pixels are never used as a texture or backdrop (AGENTS.md rule 2).
Do not publish these sheets.

Renders: `TALANTA_LOOKDEV=1 blender/render_cycles.py <dir> L06 sunset_landing hero` (L07 daylight_landing). Each step renders
from a frozen copy of the site scene (`TALANTA_SITE_BLEND`), so one step's build cannot leak into another step's stills.

## G: convex barrel and rolled top

Time: fit 20 min (fit4_convex.py, top anchor; the widest-anchor run was a comparison) + build 25 s + overlay 1 min + renders 24 min (L06 766 s, L07 664 s).

- Fit (gis/scripts/profile_fit/fit4_convex.py, 8 frames + 3 edge-on frames, wall_bulge >= 0, top anchor):
  - bulge 2.02 m: basin 0.88, LOO 1.04. Accepted, derived.
  - shoulder_rv 4.74 m: basin 1.86, LOO 0.64. Accepted, derived.
  - shoulder_rh failed the rule (LOO 2.75 m). Set to 8.5 m, "estimated (by eye, convex locked by Munene)".
  - New ledger rows only; no old row edited. roof_top_y stays 54.
- Roof cushions: deeper (1.2 m) and fuller pillows, by eye from 001232.600 and 001235.934.
- Silhouette overlay: `G/silhouette_overlay_L06_L07_internal.jpg`; before and after: `G/silhouette_before_after_internal.jpg`.
- Drone checks (`G/drone_check.json`, box cost in units of 1 % of the frame):

  | Check | Before | After G |
  |---|---|---|
  | D01 | 39.2 | 42.4 |
  | D02 | 0.23 | 1.02 |
  | D03 | 2.26 | 2.52 |

  - Each box is less than 0.6 % of the frame wider; the landmarks are unchanged.
  - Read as not clearly worse, so no stop.
  - The D01 cost is dominated by the landmark term, as it was before G.

Gaps after G:
- L06: the dusk façade reads grey-blue. The mockup has a warm uplit white façade with a lit base, which belongs to step H.
- L06: the roof cushions barely read from this distance. In the mockup they read as a strong quilt. Depth was set by eye in the frames, not to the mockup.
- L07: the barrel shoulder is close. The mockup roof rim is thicker and flatter than the frames support; the frames win.
- L06 and L07: foreground, trees and background are unchanged and belong to steps L, T and B. Beige far land, umbrella trees on lawns, no city mass.

## L: site layout (from Munene's Google Earth screenshot, the single source of truth)

Time: trace and script about 1 h, build 30 s, renders 21 min (L06 10.4 min, L07 9.0 min).

- Traced in `blender/data/site_layout_ge.json`; built by `blender/context/site_layout_ge.py`. Every feature is estimated (by eye, ±10 m).
  - Apron ring: an 18 m paved band round the bowl, with 60 lamps.
  - North-east road: 9 m wide, curved, with lamps every 30 m and eucalyptus rows on both sides.
  - Two flat-roofed buildings on the east side.
  - East car park: asphalt, with tree islands and lamps.
- W1b and OSM positions are unchanged.

Gaps after L:
- The new features barely show in either still. The road, buildings and car park are on the east side. L06 looks south-west from the north-east, and L07 looks north from the south, so they sit at or beyond the frame edge. Only the apron ring reads.
- The mockups' plaza paving rings, radiating paths, flower beds and lamp rows round the forecourt are not modelled. The GE screenshot does not resolve them.

Conflicts with the mockups (the frames and GE win; nothing was copied):
- L06: the mockup's roundabout lawn sits on the W1b-measured north-east warm-up track.
- L07: the mockup's curved approach road and lawn sit on the south-west training field. The as-built road loop in frame 000714.767 only partly matches.
- L07: the small flat-roofed building in the mockup is not in the GE screenshot.

## T: trees only where they belong

Time: rule script and checks about 50 min, build 7 min, renders 22 min (L06 12.6 min, L07 9.1 min).

- `blender/context/tree_rules.py` checks the surface under every tree point.
  - No trees on paving, roads, paths, pitches, tracks, car-park aisles or the forecourt.
  - Inside the W1b boundary a tree also needs a lawn or planting bed under it, or a path or road within 9 m (a row along the path).
- Removed:

  | Group | Removed | Of |
  |---|---|---|
  | Site trees | 645 | 823 |
  | Palms | 36 | 261 |
  | Context trees | 19 | 31,976 |

- The nearest trees get the irregular high crowns in stills (`canopy.py` LIMIT). The web bundle keeps the web level of detail.
- L07: trees now line the paths, and the pitch, track and forecourt are clear.

Gaps after T:
- The foreground is now barer than the mockups.
  - Mockups 06 and 07 show dense shrub and flower beds round the plaza. Those beds are not traced, so the trees that would stand in them are gone.
  - Needs a closer GE capture of the forecourt (about 500 m eye altitude).
- Crown types: eucalyptus rows (step L) and broadleaf are in. Jacaranda is a sparse lilac tint. Palms only stay where the site plan has them, not checked against the mockups one by one.
- The off-site context trees still use the umbrella crown far out; they read as lollipops in L07's middle distance.

## R: Rubis petrol station (north-west, chosen by Munene on 2026-10-20)

Time: OSM lookup 10 min, script 25 min, build 20 s, check stills 8 min.

- Location: OpenStreetMap node 30092080, `amenity=fuel`, `brand=Rubis`, Ngong Road.
  - Coordinates: -1.3041947, 36.7461493, which is app x -384, z -204: north side of Ngong Road at Dagoretti Corner, opposite the north-west corner of the site.
  - The OSM forecourt loop (way 654718658) and the shop (way 1242664906) fix the layout.
  - Data in `blender/data/rubis_station.json`; built by `blender/context/rubis_station.py`.
- Modelled to typical size (estimated):
  - Canopy 22 x 10 m, 5.2 m clear, along the road. Soffit lights come on at dusk.
  - 3 pump islands with dispensers, the forecourt slab, and a pylon sign.
  - The shop is already a context building on the OSM footprint; not duplicated.
- Brand: the red and yellow fascia band and the pylon panel are tagged `internal_only`. No text and no logo artwork, only the brand colours.
  - The public export skips them, which leaves a plain white canopy and a bare post. Step W must honour the tag.
  - See `R/rubis_closeup_internal.png` and `R/rubis_closeup_public_plain.png` (Workbench check views).

Gaps after R:
- The station is outside both landing frames (just right of L06, just left of L07), so the L06 and L07 stills for R are the same as B's and were not re-rendered.
- Canopy size, height and pump count are typical values, not measured. A GE trace of the canopy would fix them.
- The brief put the station near the Jamhuri entrance, on the east side. The only Rubis in OSM near the site is this north-west one, and Munene chose it.

## B: background (from data plus estimated masses; no image cards)

Time: script 40 min, build 10 min per pass, renders 25 to 30 min per pass (pass 2: L06 13.3 min, L07 11.5 min). Pass 1 is kept in `B/pass1/`.

- `blender/context/background_b.py`:
  - Forest belt: the Sentinel-2 belt cells get 2 extra jittered trees per point (38,432 added), so the belt reads as one canopy.
  - Far land: pulled toward a hazy green-grey (pass 3 makes it greener; that is in the F scene and the H stills).
  - City: mid-rise blocks north of Ngong Road and clusters at the CBD, Upper Hill, Kilimani and Westlands. Walls in warm greys and roofs in a red and grey mix.
    - Blocks are placed only where a ray hits bare terrain, so Open Buildings and OSM footprints are never overlapped.
    - Positions and heights are estimated (Visualization).
  - Town lights: warm points over the far land, on at dusk only.
- Pass 2, after the L07 sheet showed a wall of white towers:
  - The near blocks drop to 4–12 storeys, there are fewer of them, and they are spread wider, so roofs and tree cover read between them.
  - Walls are darker and warmer. Town lights are dimmer.

Gaps after B:
- L07: the CBD skyline reads but is lower and paler than the mockup's. Tower counts and heights are estimated; no skyline data was used.
- L06: the far land behind the forest belt still shows a beige band in pass 2. The pass 3 tint fixes most of it (F and H).
- Mockup 06's warm town glow at the horizon depends on the sunset sky; the H stills use a real sunset HDRI.

## F: plaza, beds and paths, with B pass 3 (rendered 2026-10-23)

Time: build 42 s, context chain 30 min (the second tree_rules pass alone takes about 20 min), renders 20 min (L06 614 s,
L07 566 s). The stills come from a frozen copy of the site scene built from this branch (finish_plaza.py and background_b.py
pass 3 included). They replace the lost B pass 2 stills, which only ever existed in the container that rendered them.

- `F/L06_sunset_landing_hero.png`, `F/L07_daylight_landing_hero.png`, and `F/L0N_vs_mockup_F_internal.jpg` (internal only).
- finish_plaza.py built 36 plaza quads, 133 bed quads, 17 radiating paths, 194 shrubs, 148 flower clumps, 38 trees and 48 lamps.
  It builds only on unmeasured ground, so most of the ring stays as W1b, OSM and GE put it.
- L07: the plaza ring, the planting beds with paths through them and the lamp rows read clearly in the foreground.
- L06: the change is small. The murram paths at lower right now read in a light paving tone (orange in B pass 1), and there are a
  few more beds and trees at the bowl's base. The mockup's wide plaza and flower ring stay mostly outside the unmeasured ground.

Note for the next agent: freeze the site blend inside `blender/out/` (as `frozen_<step>.blend`). Its image paths are relative
(`//../textures`, `//../assets`). A copy anywhere else renders every image texture missing (magenta shields). This happened
once in this pass, and those stills were discarded.

## H: hero_artistic stills (rendered 2026-10-23)

The code came with commit 79432fc (hero_artistic.py). It had not been rendered. Time: L06 71 min, L07 40 min (3840 x 2160, 128
samples, adaptive). They were rendered from the same frozen F scene, with the step H CC0 skies (`blender/assets/fetch_hdri_h.sh`).
Pillow had to be installed into Blender's bundled Python for `stamp()`.

- `H/L0N_*_hero_artistic.jpg` (quality 94), and `H/L0N_*_hero_artistic_labelled.jpg` with "Visualization: people, vehicles and
  lighting are illustrative" in the corner. The 16 MB PNG masters are not committed. They can be re-rendered from this commit.
- Added by the preset: 96 uplights (dusk only), a warm base glow, volumetric haze, glare, bevels, fins 1.35x deeper, 409 parked
  cars (plain bodies) and 1,400 people on paving (Visualization).

Read against the mockups:
- L06: the warm lit base reads strongly, as in mockup 06, and so does the sunset cloud sky.
- L06: the facade still reads mid-grey, not the mockup's warm uplit white. The 96 x 1,800 W uplights barely reach the louvres.
  Try more power or a wider spot angle.
- L06: the far land and the Ngong Hills show salt-and-pepper grain. That is volumetric haze noise at 128 samples that the denoiser
  did not clear. Try more samples, or haze only in the near band.
- L07: clean. The cumulus sky, the plaza people and the deeper fins read. The overall grade is a little darker than mockup 07.
