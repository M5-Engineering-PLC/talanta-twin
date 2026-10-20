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
