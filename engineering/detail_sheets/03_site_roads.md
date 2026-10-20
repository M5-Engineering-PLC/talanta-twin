# Detail sheet: Site, roads and entrances

All sizes that come from the ledger keep its stated method and uncertainty. Other sizes, colors, and spacings are visual estimates. Render numbers refer to the concept images in `research/concepts/2026-10-17`.

### Forecourt and paths

| id | element | detail (shape, proportions, materials, finish) | colour (hex, by eye) | count or spacing | size (m, by eye or from ledger) | source (frame file names and/or render numbers) | agreement | status | ledger row (name if it exists, else "new") | build note (one short instruction for Blender) |
|---|---|---|---|---|---|---|---|---|---|---|
| SR01 | North forecourt outline | Broad eye or shield shape in front of the stadium; paved surface | `#B9B3A5` warm grey | 1 | 102.5 × 92.9 bounding rectangle | `JWNowpO44rw_000004.000.jpg`; render 06 | frame+render | measured | `plaza_north.length`, `plaza_north.width` | Use the ledger rectangle as a size guide; shape the outer edge from the aerial frame. |
| SR02 | Forecourt paving | Large paved field with visible panel joints; render shows a paler and more uniform finish | `#B9B3A5` | Joint spacing about 1–2 | Panel size about 1–2 | `9I1korKNjig_000110.000.jpg`; render 06 | conflict | estimated | new | Use muted stone panels and keep the joints shallow. |
| SR03 | Paving edge band | Narrow darker strip follows the curved forecourt edge | `#81796D` | Continuous edge | About 0.3 wide | `9I1korKNjig_000110.000.jpg`; render 06 | frame+render | estimated | new | Add a thin edge band along the path boundary. |
| SR04 | Radial paths | Straight walks spread outward from the stadium and cross the plaza | `#C5BFB2` | About 6–10 visible axes | About 4–6 wide | `JWNowpO44rw_000004.000.jpg`; render 06 | frame+render | estimated | new | Lay broad paths from the facade and keep the spacing irregular. |
| SR05 | Curved plaza paths | Curved walks connect planted areas and the forecourt edge | `#B9B3A5` | Several arcs | About 3–5 wide | `JWNowpO44rw_000004.000.jpg`; render 06 | frame+render | estimated | new | Add a few curved connectors between the straight walks. |
| SR06 | Entrance apron | Wide, mostly level paved area next to the facade | `#8B8174` | Continuous | At least 15 deep by eye | `9I1korKNjig_000110.000.jpg`; `KEOmkVfjhu8_000206.000.jpg` | frame | estimated | new | Keep the apron open and use a low contrast surface. |

### Planting, fountain and site furniture

| id | element | detail (shape, proportions, materials, finish) | colour (hex, by eye) | count or spacing | size (m, by eye or from ledger) | source (frame file names and/or render numbers) | agreement | status | ledger row (name if it exists, else "new") | build note (one short instruction for Blender) |
|---|---|---|---|---|---|---|---|---|---|---|
| SR07 | Round planter islands | Low circular raised beds with shrubs or small trees | `#66574A` wall; `#42633E` plants | Repeated islands | Radius 7; height 0.8 | `JWNowpO44rw_000516.000.jpg`; render 06 | frame+render | estimated | `site.planter.r`, `site.planter.h` | Use low circular planters and sparse planting. |
| SR08 | Long planting beds | Narrow beds follow the paths and facade | `#725A45` soil; `#49643A` plants | Several strips | About 1–2 wide | `JWNowpO44rw_000516.000.jpg`; render 04, 06 | frame+render | estimated | new | Add thin planting strips between walks. |
| SR09 | Shrub groups | Low clipped shrubs and small ornamental plants | `#48633D` | Clumps of 3–8 | About 0.4–1.2 high | `JWNowpO44rw_000516.000.jpg`; render 04 | conflict | estimated | new | Use small mixed-height shrub groups; avoid dense hedges. |
| SR10 | Turf islands | Small grass areas between paved walks | `#52713E` | Irregular patches | Bed size varies | `JWNowpO44rw_000516.000.jpg`; render 06 | frame+render | estimated | new | Keep turf to planted islands and narrow verges. |
| SR11 | Fountain basin | Rendered long, shallow basin with rounded ends; frames show wet paved apron and jets, without a clear basin edge | `#9AA9A8` water; `#A7A195` rim | 1 in render | 66 × 15; water level 0.42 | `8n3ILabO8uw_000007.000.jpg`; `8n3ILabO8uw_000012.000.jpg`; render 04 | conflict | estimated | `site.pool.length`, `site.pool.width`, `site.pool.water_y` | Treat the basin outline as an estimate; keep it separate from the confirmed paved apron. |
| SR12 | Basin steps | Three low steps around the rendered pool edge | `#A9A398` | 3 | Step rise 0.18 | render 04 | render | estimated | `site.pool.steps`, `site.pool.step_h` | Add shallow concentric steps around the estimated basin. |
| SR13 | Fountain jets | Vertical jets across a flat paved area; visible frame jets do not establish a formal pool | `#D6E3E6` | 2 rows; about 30 per row in ledger | Row offset 3.5; jet height about 4 | `8n3ILabO8uw_000007.000.jpg`; render 04 | conflict | estimated | `site.jets.rows`, `site.jets.per_row`, `site.jets.row_offset`, `site.jets.h` | Use low, fine jets and label the full pattern as an estimate. |
| SR14 | High fountain arcs | Render-only arcing water forms above the lower jets | `#D6E3E6` | About 13 arcs | Height about 8 | render 04 | render | estimated | `site.jets.arc_count`, `site.jets.arc_h` | Add a small number of high arcs as optional geometry. |

### Masts and lighting

| id | element | detail (shape, proportions, materials, finish) | colour (hex, by eye) | count or spacing | size (m, by eye or from ledger) | source (frame file names and/or render numbers) | agreement | status | ledger row (name if it exists, else "new") | build note (one short instruction for Blender) |
|---|---|---|---|---|---|---|---|---|---|---|
| SR15 | Flag masts | Slim freestanding metal poles around the forecourt | `#BFC4C3` | About 4 per side; spacing about 70 | Height about 26 | `JWNowpO44rw_000004.000.jpg`; render 06 | frame+render | estimated | `site.masts.spacing`, `site.masts.h`, `site.masts.forecourt_rows` | Use slender poles and keep the count provisional. |
| SR16 | Flags | Rectangular flags on some masts; image detail does not resolve each design | `#D6D1C5` | One per visible mast | About 2 × 1 by eye | render 06 | render | estimated | new | Use plain, unlettered flags. |
| SR17 | Path lights | Short poles with small round or simple heads along the walks | `#626967` pole; `#F5DDA0` light | About 10–15 m apart in render | About 4–6 high | `JWNowpO44rw_000516.000.jpg`; render 04, 06 | frame+render | estimated | new | Use a repeated low-detail light fixture. |
| SR18 | Bollards | Short posts beside walk edges and planted areas | `#777B78` | About 2–4 m apart in render | About 0.8–1.0 high | render 06 | render | estimated | new | Place a few simple bollards at path edges. |

### Roads, kerbs and parking

| id | element | detail (shape, proportions, materials, finish) | colour (hex, by eye) | count or spacing | size (m, by eye or from ledger) | source (frame file names and/or render numbers) | agreement | status | ledger row (name if it exists, else "new") | build note (one short instruction for Blender) |
|---|---|---|---|---|---|---|---|---|---|---|
| SR19 | Ngong Road surface | Dark asphalt road outside the site; render shows a wide divided road | `#424541` | Two directions in render | Width not established by frames | `cyNgbyZv6BM_000152.000.jpg`; render 06, 07 | frame+render | estimated | new | Use dark asphalt and keep road width adjustable. |
| SR20 | Ngong Road lanes | Multiple lanes in each direction in the renders; individual widths cannot be measured from the images | `#454844` | About 2–3 lanes per direction in render | About 3.2–3.5 per lane | render 06, 07 | render | estimated | new | Set lane widths as a modeling estimate. |
| SR21 | Lane divider lines | White dashed lane dividers appear on the rendered road | `#E7E6DF` | Dashed, repeated | About 3 m dash and 6 m gap | render 06, 07 | render | estimated | new | Use short white dashes on the main road. |
| SR22 | Road edge lines | Pale edge marks border sections of the road in the render | `#E7E6DF` | Continuous where shown | About 0.12 wide | render 06, 07 | render | estimated | new | Add narrow edge lines only on the main road. |
| SR23 | Central reserve | Raised landscaped divider separates road directions in the renders | `#5E664F` plants; `#8B8A7D` kerb | Continuous | About 2–5 wide | render 06, 07 | render | estimated | new | Model a low, planted median. |
| SR24 | Zebra crossings | No clear crossing is visible in the sampled road frames; render detail is too small to resolve | `#E7E6DF` | Not set | Not set | `cyNgbyZv6BM_000152.000.jpg`; render 06 | frame+render | estimated | new | Leave crossings out until their positions are known. |
| SR25 | Access road surface | Internal and approach roads in the frames include unfinished earth or compacted reddish ground | `#8B4A2B` to `#A0522D` | Continuous road surface | Width not established | `3ZiiGojVM70_000618.000.jpg`; `KEOmkVfjhu8_001330.000.jpg`; render 06 | conflict | estimated | `site.ground.murram_rgb` | Keep the site road surface reddish and distinct from Ngong Road. |
| SR26 | Access road markings | Sampled access-road frames show little or no clear lane marking | `#8B4A2B` | None visible in the selected frames | Not set | `3ZiiGojVM70_000618.000.jpg`; `h--Jmi7SwBs_000058.000.jpg`; render 06 | conflict | estimated | new | Leave internal road markings minimal. |
| SR27 | Kerbs | Raised concrete or stone edges separate paving, planted beds, and road surfaces | `#8B877D` | Continuous along visible edges | About 0.15–0.25 high | `9I1korKNjig_000110.000.jpg`; `KEOmkVfjhu8_001330.000.jpg` | frame | estimated | new | Use simple low kerbs with softened corners. |
| SR28 | Drain channels | Grooved or open channels run beside some road and paved edges | `#827C70` | Along selected edges | About 0.3–0.5 wide | `KEOmkVfjhu8_001330.000.jpg` | frame | estimated | new | Add shallow linear channels near road edges. |
| SR29 | Traffic barriers | No clear road barrier type or placement is established by the sampled frames | `#A39C8D` | Not set | Not set | `cyNgbyZv6BM_000152.000.jpg`; render 06 | frame+render | estimated | new | Do not add a detailed barrier layout. |
| SR30 | Bus stops | A roadside shelter-like structure appears in a frame; its function and arrangement are unclear | `#6F756F` | Not established | About 3 × 6 footprint by eye | `cyNgbyZv6BM_000152.000.jpg` | frame | estimated | new | Use a generic shelter only if the scene needs one. |
| SR31 | Matatu stage | No distinct stage layout is visible in the sampled frames | `#77776E` | Not set | Not set | `cyNgbyZv6BM_000152.000.jpg`; render 06, 07 | frame+render | estimated | new | Leave out a defined stage layout. |
| SR32 | Parking surface | Render shows broad paved parking areas; frames do not confirm their exact boundaries | `#76766E` | Multiple areas in render | Area size not established | `JWNowpO44rw_000004.000.jpg`; render 06, 07 | conflict | estimated | new | Keep parking blocks as adjustable, generic surfaces. |
| SR33 | Parking bays | Individual bay lines are too small or absent in the sampled frames | `#D8D7CE` | About 2.5 m bay width as a modeling estimate | About 2.5 × 5 | render 06, 07 | render | estimated | new | Add sparse bay lines only in the close view. |

### Walls, fences, trees and ground

| id | element | detail (shape, proportions, materials, finish) | colour (hex, by eye) | count or spacing | size (m, by eye or from ledger) | source (frame file names and/or render numbers) | agreement | status | ledger row (name if it exists, else "new") | build note (one short instruction for Blender) |
|---|---|---|---|---|---|---|---|---|---|---|
| SR34 | Boundary wall | Plain segmented wall outside the stadium grounds; exact route and height are not established | `#A5A29A` | Long runs | About 2–3 high | `cyNgbyZv6BM_000152.000.jpg`; render 06 | frame+render | estimated | new | Use a generic wall without detailed access features. |
| SR35 | Fence panels | Light metal or sheet panels appear above or beside parts of the wall | `#9EA19D` | Repeated panels | About 2–3 high | `cyNgbyZv6BM_000152.000.jpg`; `KnQhTD_F77g_000023.022.jpg` | frame | estimated | new | Use plain, repeated panels with no sensitive layout detail. |
| SR36 | Murram ground | Exposed reddish-brown soil covers unfinished or unplanted areas | `#8B4A2B` to `#A0522D` | Broad patches | Varies | `KnQhTD_F77g_000022.021.jpg`; `3ZiiGojVM70_000618.000.jpg`; render 07 | frame+render | estimated | `site.ground.murram_rgb` | Use mottled red-brown ground with sparse grass. |
| SR37 | Young planted trees | Frames show small planted trees, but do not support exact species identification | `#597347` leaves; `#6C5540` trunks | About 5–10 m apart by eye | About 2–4 high | `KnQhTD_F77g_000022.021.jpg`; `JWNowpO44rw_000516.000.jpg`; render 06 | conflict | estimated | new | Use young generic broadleaf trees at loose spacing. |
| SR38 | Palms | Render images show palms; sampled frames do not confirm a palm species | `#48673D` leaves; `#715A42` trunk | About 6–10 m apart in render | About 5–8 high | render 01, 06, 07 | render | estimated | new | Use a few palm forms as a visual estimate. |
| SR39 | Large shade trees | Render images show mature broad-canopy trees; species are not identifiable | `#36583B` leaves; `#594A38` trunk | About 8–15 m apart in render | About 8–14 high | render 01, 04, 06, 07 | render | estimated | new | Keep mature trees in the background and near paths. |
| SR40 | Jacaranda-like flowering trees | Purple flowering crowns appear in renders; frames do not confirm species or flowering | `#655481` | Scattered in render | About 6–10 high | render 01, 04 | render | estimated | new | Treat flowering trees as optional seasonal detail. |
| SR41 | Planted verges | Low mixed shrubs and ground cover follow parts of the stadium edge | `#527044` | Repeated narrow strips | About 1–3 wide | `JWNowpO44rw_000516.000.jpg`; render 04, 06 | frame+render | estimated | new | Use sparse, low planting beside the wall. |

### Warm-up track and training areas

| id | element | detail (shape, proportions, materials, finish) | colour (hex, by eye) | count or spacing | size (m, by eye or from ledger) | source (frame file names and/or render numbers) | agreement | status | ledger row (name if it exists, else "new") | build note (one short instruction for Blender) |
|---|---|---|---|---|---|---|---|---|---|---|
| SR42 | Warm-up track outline | Oval track area east of the main bowl | `#9A493D` | 1 | 165.8 × 87.2 bounding rectangle | `020A-X2A2V4_000103.159.jpg`; render 07 | frame+render | measured | `warmup_track.length`, `warmup_track.width` | Use the ledger dimensions for the oval footprint. |
| SR43 | Track lanes | Red track surface with parallel lane lines; lane count is not clear in the aerial frame | `#9A493D` | About 6 lanes in render | About 1.2 m each as an estimate | `020A-X2A2V4_000103.159.jpg`; render 07 | frame+render | estimated | new | Add faint lane lines and keep their count adjustable. |
| SR44 | Track infield | Green infield inside the warm-up track | `#52713E` | 1 | Within track boundary | `020A-X2A2V4_000103.159.jpg`; render 07 | frame+render | estimated | new | Fill the infield with a simple grass surface. |
| SR45 | Southeast training pitch area | Rectangular grass area near the southeast side of the stadium site | `#52713E` | 1 | 126.1 × 81.5 bounding rectangle | `020A-X2A2V4_000103.159.jpg`; render 07 | frame+render | measured | `training_pitch_se.length`, `training_pitch_se.width` | Use the ledger dimensions for the pitch area. |
| SR46 | Southwest training field earthworks | Large open training area with exposed earth | `#8B4A2B` | 1 | 180.3 × 101.2 bounding rectangle | `h--Jmi7SwBs_000058.000.jpg`; render 07 | frame+render | measured | `training_field_sw.length`, `training_field_sw.width` | Keep the field surface red-brown until finished surfacing is confirmed. |
| SR47 | Training field grass | Render shows a finished grass field, while the sampled frame shows bare earth | `#52713E` grass; `#8B4A2B` earth | 1 rendered field | Based on area row | `h--Jmi7SwBs_000058.000.jpg`; render 07 | conflict | estimated | new | Separate the finished-field look from the current earth surface. |

### Generic entrance architecture and sign frames

| id | element | detail (shape, proportions, materials, finish) | colour (hex, by eye) | count or spacing | size (m, by eye or from ledger) | source (frame file names and/or render numbers) | agreement | status | ledger row (name if it exists, else "new") | build note (one short instruction for Blender) |
|---|---|---|---|---|---|---|---|---|---|---|
| SR48 | Entrance canopy | Shallow roof on simple supports beside a broad paved approach | `#6E6A60` roof; `#A6A29A` supports | Generic repeated structure | About 3–5 high | `KEOmkVfjhu8_000206.000.jpg`; render 06 | frame | estimated | new | Model a plain canopy without layout detail. |
| SR49 | Entrance paving | Wide approach surface with paving blocks and raised edges | `#8D8374` | Broad apron | About 10–20 deep by eye | `9I1korKNjig_000110.000.jpg`; `KEOmkVfjhu8_000206.000.jpg` | frame | estimated | new | Use neutral paving and low edge kerbs. |
| SR50 | Sign frames | Freestanding rectangular frames with blank faces | `#5C625F` frame; blank face | Sparse; count not fixed | About 3–5 high | render 06, 07 | render | estimated | new | Add blank frames with no lettering or symbols. |
| SR51 | Entrance columns and fascia | Simple pale supports under a horizontal canopy or fascia | `#D0CEC7` | Repeated supports | About 4–6 high | `KEOmkVfjhu8_000206.000.jpg`; render 06 | frame+render | estimated | new | Use plain pale supports and a shallow fascia. |

### Conflicts

- The renders show a large, formal pool. The sampled fountain frames show jets across a paved apron, but they do not establish the pool edge or its size.
- The renders show mature palms and flowering trees. The sampled planting frames show young trees and low plants, and they do not identify species.
- Render 06 shows pale, regular plaza paving and radial paths. The sampled ground-level frames show darker paving or unfinished ground, and they do not confirm the full radial pattern.
- The renders show clearly marked, divided roads. The sampled access-road frames show earth or reddish compacted surfaces with few visible lane marks. The frame set does not resolve Ngong Road lane widths.
- Render 07 shows a finished grass training field. The sampled frame shows exposed earth in that area.

### Not visible

- Exact forecourt joint spacing, paving pattern, road lane widths, crossing locations, and the full road marking plan.
- Exact tree species and measured tree spacing.
- Exact counts and positions for flag masts, lights, bollards, parking bays, barriers, bus stops, and matatu stages.
- Drain dimensions and routes.
- A confirmed fountain basin outline, jet count, and water depth.
- A confirmed full boundary route or complete parking plan.
