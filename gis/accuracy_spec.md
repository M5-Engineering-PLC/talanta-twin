# Accuracy spec for the twin geometry

Date: 2026-10-16
Status: proposed by the lead. Munene approves.
CRS for every number: WGS 84 / UTM zone 37S (EPSG:32737), heights in metres above the local ground unless stated.

Every geometry item in the twin needs a source and an error. The tolerance is the largest error we accept before the item can carry the label "measured data". Items over tolerance stay "estimated" and keep that label in the product.

The "Now" column is what the data in this repository supports on 2026-10-16. See `coverage_report.md` for the evidence.

## Hero: the stadium and its plot

| Item | Tolerance | Why this tolerance | Now | Best free route to close |
|---|---|---|---|---|
| Bowl centre position | 2 m | Places the bowl in the near ring and on the terrain | 1.5 m between OSM and Sentinel-2 | Done for the near ring. Keep |
| Bowl outer outline (roof edge) in plan | 1 m | A visible offset in overlays on reference frames | OSM 256 x 204 m; Sentinel-2 274 x 234 m. 18-30 m apart | W1b ruler measurements on post-Feb 2026 imagery |
| Long-axis bearing | 1 degree | Sun and shadow direction in the hero slice | 176-180 degrees (OSM best fit 178-180; Sentinel-2 median 177) | W1b |
| Roof opening (inner edge) | 1 m | The look of the bowl from the air | Sentinel-2 opening 9,300-11,100 m2; no size | W1b |
| Pitch and run-off | 0.2 m | Fixed by the Laws of the Game and CAF rules | Assumed 105 x 68 m; OSM pitch polygon with run-off 134 x 85 m | W1b with penalty-area and centre-circle checks |
| Roof edge height above pitch | 1 m | Silhouette against the sky | One unverified press figure: 56 m maximum height | Shadow method in W1b, SfM (W3) |
| Tier count, rake and row count | 0.25 m per tier; exact rows | Seat count check against 60,000 | 3 tiers (press); rows unknown | Frames + SfM (W3) + seat-count check |
| Facade module spacing | 0.5 m | Repetition is visible | Frames only | Frames scaled by the outline |
| Gate positions (8) | 2 m | Site plan and crowd flow | Not measured | W1b. Internal only (AGENTS rule 8) |
| Parking, plazas, landscaping | 2 m | Site plan | OSM land use only | W1b |
| Training pitches and mini-stadium | 2 m | Visible in every aerial view | OSM pitch polygons | W1b check of 2 pitches |

## Near ring: about 1.5 km around the bowl

| Item | Tolerance | Now | Route |
|---|---|---|---|
| Building footprints | 3 m | OSM, Google and Microsoft footprints (Overture 2026-09-23) | Done. Spot-check 10 in W1b |
| Building heights | 3 m or one storey | Open Buildings 2.5D 2023 heights where present; else defaults | Done for 2023 stock. New buildings stay estimated |
| Road centrelines | 3 m | Overture/OSM segments | Done |
| Road widths | 1 m | Not present | W1b sample of 5 roads; class defaults |

## Far ring: to the horizon

| Item | Tolerance | Now | Route |
|---|---|---|---|
| Terrain | 30 m in plan, 5 m vertical | GLO-30 DSM, 30 m | Done |
| Skyline features (Ngong Hills, CBD, Kibera) | Shape only | GLO-30 + Overture | Done for shape |
