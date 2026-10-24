# Cloud handoff: layout fix, landmark pass, 4K re-render (2026-10-23)

Date: 2026-10-23
Project: Talanta twin (M5)
From: the local lead session on Munene's laptop
To: the cloud Talanta build chat
Status: active work order
Branch: `lead/layout-audit-01` (based on `m5/vibrant-ride-5er9ju` at f2136bf)

Read this file first. Then read AGENTS.md, blender/STATUS.md and engineering/replica_plan_2026-10-20.md.

## Objective

The 4K stills L06 and L07 are on step_FH, but they are not approved. Munene saw two layout faults:

- A car park sits on a grass area.
- The road that goes into the stadium looks wrong.

Munene also wants real local apartment blocks in the background, because local viewers know them. Do the layout fix and the landmark pass first. Then re-render the 4K stills and stop for approval.

## What is on this branch

| Path | Content | Status |
|---|---|---|
| engineering/landmarks_01/LANDMARK_CANDIDATES.md | Candidate buildings, frames, camera projections, and the map positions | Done. Low confidence on names from frames alone. |
| engineering/landmarks_01/sheets/ | Frame crops of the apartment blocks | Internal only |
| engineering/landmarks_01/ref/gmaps_*.webp | Two Google Maps satellite screenshots from Munene | Internal only. Use for positions, never as a texture. |
| engineering/layout_audit_01/ | The layout audit from the drone frames, with a fix list | Draft only. Wait for LEAD_REVIEW.md. See "Step 1". |

## Work order, in this sequence

### Step 1: Pass I, layout fix

Do this step only when engineering/layout_audit_01/LEAD_REVIEW.md is on this branch. A draft of the audit is on the branch now, but it is not reviewed. Do not apply the draft. The lead writes LEAD_REVIEW.md after the review and pushes it. If LEAD_REVIEW.md is not there yet, start Step 2 and fetch again later.

Apply LEAD_REVIEW.md (revision 2). The dusk image in research/reference/ is AI-generated, so pass I removes the whole pass F layout. The notes below are from the draft. LEAD_REVIEW.md wins where it differs.

- The north-west car park (`layout_final.json:carpark_north_west`, 318 cars) covers lawn and crossed red paths in the frames. Remove it from the finished state. Show the lawn, paths, beds and palms again.
- The south-west lot (`layout_final.json:carpark_south_west`, 207 cars) covers a grass rectangle inside the loop road. Remove the lot. Show the grass and the small stand again. Keep the loop road.
- The 8 m road between the training pitches (`lf_road_between_pitches`) is wrong. The real east approach is a broad pale paved area. A long pointed island runs along its centre. The approach spreads at the east end and merges into the outer apron at the west end.
- No vehicle road crosses the north plaza or enters the bowl.
- Keep the east hardstanding as it is. Do not add new bay rows there.
- The map names the field north-east of the stadium, south of Ngong Road, "Jamhuri sports ground" (about x 224, z -288). Keep it as a field.

Keep every change in the finished state only. The asbuilt state does not change. Add ledger rows for each change.

### Step 2: Pass J, landmark buildings

Model these real buildings as plain masses with the correct footprint, height, storeys, colours and roof. Use the gpkg footprint where one exists. Otherwise, take the gpkg footprint within 40 m of the map pin.

Positions are in the app frame: metres, x east, z south, from the twin origin. The map pins are good to about 25 m.

| Building | Position | Height and source | Frame evidence |
|---|---|---|---|
| Enkang Apartments A, B, C (Ngong Road) | gpkg: x -47 to 5, z -459 to -419. Pin: x -102, z -462. | 38 to 47 m, gpkg | Probably the 12-storey cream tower with brown vertical strips in JWNowpO44rw_000706.800. Also 000619.700, 000623.200, 000626.700. |
| Ngando Flats | pin x -275, z -424 | gpkg footprint near the pin | 000619.700 group (low confidence) |
| Liberty Centre | pin x -100, z -653 | gpkg footprint near the pin | none confirmed |
| Denali Apartments | pin x -200, z -796 | 34 m, gpkg | none confirmed |
| Racecourse Gardens Apartments | pin x -468, z -825 | gpkg footprint near the pin | none confirmed |
| White Village Apartments | pin x 174, z -909 | gpkg footprint near the pin | none confirmed |
| Alba Apartments | pin x 255, z -890 | probably the gpkg footprint "TSAVO Skywalk", 41.5 m, at x 223, z -976 | 000706.800 and 000709.167 (low confidence) |
| Kenya Meteorological Department | pin x 1,084, z -632 | low buildings, gpkg | none |
| The Junction Mall and Century Cinemax | gpkg footprint, centre about x 1,410, z -879 | 11 to 17 m, gpkg | none. Outside all hero cameras. Live twin only. |

The gpkg is gis/derived/near_ring_buildings.gpkg (EPSG:32737). The twin origin is lon 36.749597, lat -1.306037.

Rules for this step:

- Remove or move the generic city boxes that overlap these footprints (blender/context/suburbs.py, background_b.py).
- Use frame colours and window rhythm. Do not use photos or map imagery as textures.
- Show no names, logos or signage on the buildings.
- Give each building a ledger row: position source, height source, confidence.
- These buildings show mainly in L07 and D02. L06 looks the other way.

Keep the Rubis station where it is (x -382, z -182, north-west on Ngong Road). Munene chose this station on 2026-10-20. It is not the station at the Dagoretti Corner junction.

### Step 3: Check renders at 1080p

Render L07, D01, D02, D03 and P01 at 1080p on the new step (step_FJ). Make sheets against the drone frames: D01 against 000645.000, D02 against 000714.767, D03 against 000617.567. Push the renders, the sheets and a README with the change list and the gaps.

### Step 4: 4K stills, then stop

1. Fix the speckle on the far ridge in L06. Use more samples or a larger adaptive minimum.
2. Make the L06 sunset sky warmer, nearer to the orange clouds of mockup 06.
3. Render L06 and L07 at 4K with the `hero_artistic` preset.
4. Push the stills, the labelled copies and the README.
5. Stop. Munene must approve the stills before the W re-bake.

### Step 5: after the approval only

1. Split the W re-bake into parts of less than 4 h of CPU each. The full re-bake costs about 4.7 h.
2. Export the bundle as `web_hero_v2`. Do not change the files of `web_hero_v1`.
3. Push the bundle to the orphan branch `assets/web_hero_v2` with a manifest (size and sha256 for each file).

## Work that stays on the laptop

- GitHub releases. The cloud cannot create them. The laptop runs `gh release create web_hero_v2 --prerelease` after it checks the manifest.
- Codex reviews of large diffs (the Codex subscription is local).
- The real-phone test of the landing page.
- New map screenshots or local knowledge from Munene.

## Later work, not in this order

The app work is on nine branches that are 55 to 149 commits ahead of `main`. `main` has not moved since 2026-10-16. A plan to merge them is necessary before the live twin can use `web_hero_v2`. The lead writes this plan separately.

## Rules that stay

- AGENTS.md applies in full.
- Frames, mockups and map screenshots are internal only.
- People, cars and lights are a Visualization. The labelled copies carry the note.
- Do not model exits, control rooms or camera positions for a public view.
- Commit as Munene's git identity. Do not add AI attribution.
- Work on a branch. Do not rewrite history on `main`.
