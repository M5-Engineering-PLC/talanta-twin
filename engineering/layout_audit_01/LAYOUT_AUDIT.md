# Talanta layout audit 01

Date: 2026-10-23. Project: Talanta Twin. Track: separate venture, classification unresolved.
Status: partial finished plan. Internal reference only. Evidence class: software review of images and model data.
Branch: lead/layout-audit-01. No physical measurement, traffic study or new simulation forms part of this audit.

## Direct answers

Frame evidence: both disputed car parks cover green space in the inspected drone footage.
The south-west lot covers the grass rectangle inside the road loop beside the small stand.
See JWNowpO44rw_000714.767.jpg at 07:14.767 and JWNowpO44rw_000716.317.jpg at 07:16.317.
The north-west car park covers lawn and crossed paths west of the north plaza.
See JWNowpO44rw_000645.000.jpg at 06:45.000 and JWNowpO44rw_000659.633.jpg at 06:59.633.

Frame evidence: the south-west rectangle supports a lawn finding. The footage does not resolve sport markings on that rectangle.
The east training pitch is a separate feature. It lies south of the broad eastern approach in JWNowpO44rw_000617.567.jpg.
Thus, the statement that a car park replaces grass is supported. A marked playing field at that exact south-west location remains unproven.

Frame evidence: the real eastern approach is a broad pale paved area between the eastern sport areas.
It contains a pointed central island. Its western end merges into the outer apron.
See JWNowpO44rw_000617.567.jpg at 06:17.567.
The model substitutes an 8 m asphalt strip without that island. The strip looks like a road aimed at the facade.
The frame shows a junction with the apron, not a road through the internal arena.

Estimate from a camera solve: the total paved envelope is about 40 to 50 m wide and 165 m long.
This estimate includes the island and edge space. It is not a vehicle carriageway width.
Inference: a finished model can retain this footprint with a finished surface. The footage does not settle vehicle lanes or operating use.

Frame evidence: Ngong Road carries through traffic along the north frontage.
The northeast peripheral route curves around the track and joins the eastern approach.
D02 shows a loop around the south-west grass and broad work areas farther west.
The footage does not continuously establish a completed vehicle route from Ngong Road to a final drop-off.
The final external junction, turning lanes, drop-off areas and stopping rules remain unknown.

## Source authority and state

The filename dates do not prove capture dates. All inspected source capture dates remain unknown.
Video timestamps identify positions within a video only.
No inspected frame establishes a fully finished site across the whole layout.

- JWNowpO44rw at 04:41.933 to 06:12.433 shows a filmed architectural model. State: finished design intent, not completed construction.
- JWNowpO44rw at 06:17.567, 06:45.000 and 07:14.767 shows the real site with construction work. State: asbuilt construction.
- JWNowpO44rw at 12:32.600 and 12:46.333 shows the real site with work areas. State: asbuilt construction.
- OB0OE-PAAVg, _SnnNoRfzkA, zb4ISsX7Pa0 and LhY5-yDuhfc show earlier construction stages.
- mJJ4Qkl858k shows grass and completed roof surfaces, but it does not establish completion of the whole site.
- 020A-X2A2V4 shows night lighting and a partly finished landscape. State: asbuilt, full completion unknown.
- HU3J94fa8_c shows frontage earthworks. The close views do not establish a final junction shape.
- h--Jmi7SwBs, 9I1korKNjig, KEOmkVfjhu8 and cyNgbyZv6BM show local construction surfaces and planting.

The dusk image is research/reference/dusk_aerial_finished_2026-10-17.jpg.
Its source date, capture method and final-state authority remain unresolved in the supplied files.
It strongly disagrees with the drone footage at both western green areas and the transport corridor.
The pass F README also records a skyline mismatch and uncertain railway alignment.
These facts do not prove that the image is false. They prevent its use as settled finished-state authority.

Inference: stop the disputed finished-state items until the lead resolves Q1 and Q2.
Do not convert construction absence into proof that a later feature cannot exist.
Do not convert a filmed architectural model into an asbuilt observation.

The comparison table uses unknown for disputed final features.
High confidence beside unknown describes the observed grass or path, not its permanent retention.
The JSON retains asbuilt geometry for those features. It does not approve a finished replacement.
Finished entries with keep, resize or add are stated inferences from visible geometry.

## Reviewed inputs

The audit reads README.md, PLAN.md and the layout sections in engineering/replica_plan_2026-10-20.md.
It reads blender/renders/layout_final_01/README.md and the D01 to D03 and P01 definitions in app/cameras/manifest.json.
It also reads these model inputs:

- blender/data/layout_final.json
- blender/data/site_layout_ge.json
- blender/data/forecourt_layout.json
- blender/data/road_lines.json
- blender/data/site_plan.json
- blender/context/layout_final.py
- blender/context/site_layout_ge.py
- blender/context/forecourt.py

The review covers every supplied PNG in layout_final_01 and people_final_01.
It covers both labelled hero_artistic_02 JPEGs and ground_fix_01/sheets/000_plan_trace_vs_layout.png.
The renders show model software output. They are not evidence of the real site.

The audit selects 36 indexed frames before opening them. It does not open all 465 main-video frames.
source_frames.json records each exact path, timestamp, visual state and evidence sheet.
The audit excludes oL3wsPsx4Jw, PWj9s_v3G6U and subjects that contain Nyayo.
No network operation or Blender operation occurs.

## Approximate plan and coordinate method

The site frame uses metres, x east and z south. The origin is the W1b pitch centre in app/cameras/manifest.json.
A centreline is a line along the middle of a feature.
The JSON gives footprints, approximate centres or relative locations. Null coordinates mean that the evidence does not settle a site position.

Estimate from a camera solve: four hand-selected ground outlines use D02 and D03.
The method intersects camera rays with a flat plane at app y = 6.12 m.
It uses the manifest pose, vertical field of view, image aspect and roll.
It does not use the roof outline as a ground control point.
It does not intersect the actual terrain or refine a camera solve.

camera_estimates.json records the source pixels and the resulting coordinates.
The four eastern approach corners are approximately [129,25], [129,-21], [283,-37] and [298,10].
Their transverse distances are about 46 m and 49 m.
The central island corners are approximately [144,2], [184,-11], [223,-1] and [192,13].
The island length is about 79 m. Its maximum sampled width is about 24 m.

The south-west grass corners are approximately [-139,122], [-73,135], [-80,233] and [-153,228].
The estimated centre is about [-112,180]. The observed loop lies outside this grass footprint.
The east training rectangle occupies about x 152 to 226 and z 24 to 154.
Its location broadly agrees with site_plan.json:pitch_se at [187.6,96.0].
The dusk-only proposal to shift that pitch about 70 m northwest lacks drone support.

Changing the ground plane to y = 0 changes the eastern samples by up to 11.79 m.
It changes the south-west grass samples by up to 18.59 m.
Use about 20 m positional uncertainty for the eastern estimates and 25 m for the south-west grass estimate.
These are working uncertainty allowances, not measured error bounds.
The inherited Google Earth trace claims about 10 m uncertainty. This audit reads its numeric data only.
Pass F claims about 15 m near-camera uncertainty and 30 m far-camera uncertainty.

Inference: the grass and path topology is more reliable than exact dimensions.
The camera estimates locate features well enough for a review plan. They do not support construction or final vehicle design.

## Comparison table

Each row starts its observation with an evidence label.
The first fourteen rows cover every geometric feature in layout_final.json and site_layout_ge.json.
The remaining rows cover supporting features, missing geometry and unresolved operating areas.
The film of the architectural model appears only as design evidence in these rows.

| Feature | Model now | Drone frames show | Verdict | Confidence | Evidence |
|---|---|---|---|---|---|
| west_road / layout_final.json:west_road | 21 m divided road, x about -156, z -236 to 700. | frame evidence: West apron and work yards are visible. No continuous divided road is established. Ngong Road is the northern divided road. | unknown | low | JWNowpO44rw_000617.567.jpg (06:17.567)<br>JWNowpO44rw_000714.767.jpg (07:14.767)<br>OB0OE-PAAVg_000012.345.jpg (00:12.346) |
| railway / layout_final.json:railway | Two tracks on 11 m ballast, x about -204. | inference: No track alignment is resolved in these views. Vegetation and work yards obscure parts of the corridor. | unknown | low | JWNowpO44rw_000617.567.jpg (06:17.567)<br>JWNowpO44rw_000714.767.jpg (07:14.767) |
| station / layout_final.json:station | 8.5 x 240 m platform and two canopies. | inference: No railway platform is established. Visible roofs alone do not identify a station. | unknown | low | JWNowpO44rw_000617.567.jpg (06:17.567)<br>JWNowpO44rw_000714.767.jpg (07:14.767) |
| footbridge / layout_final.json:footbridge | 79 m elevated crossing across new road and railway. | inference: No matching crossing is established. These frames do not prove a later crossing absent. | unknown | low | JWNowpO44rw_000645.000.jpg (06:45.000)<br>JWNowpO44rw_000714.767.jpg (07:14.767) |
| carpark_north_west / layout_final.json:carpark_north_west | Asphalt over west forecourt, 318 illustrative cars. Lawn and paths hidden. | frame evidence: Grass and red crossed paths west of the north plaza. No car park on this observed lawn. | unknown | high | JWNowpO44rw_000645.000.jpg (06:45.000)<br>JWNowpO44rw_000659.633.jpg (06:59.633)<br>mJJ4Qkl858k_000014.000.jpg (00:14.000) |
| spine_beds / layout_final.json:spine_beds | 12 m strip at x -64 to -52, z -228 to -148. | frame evidence: Planting borders a lawn and path network. A car park spine is not established. | unknown | medium | JWNowpO44rw_000645.000.jpg (06:45.000)<br>JWNowpO44rw_000659.633.jpg (06:59.633) |
| carpark_south_west / layout_final.json:carpark_south_west | 72 x 96 m asphalt lot, 207 illustrative cars, pitch and small stand hidden. | estimate from a camera solve: A grass rectangle lies inside a paved loop beside a stand. No bays appear on the grass. Sport markings are not resolved. | unknown | high | JWNowpO44rw_000714.767.jpg (07:14.767)<br>JWNowpO44rw_000716.317.jpg (07:16.317)<br>JWNowpO44rw_001246.333.jpg (12:46.333) |
| road_between_pitches / layout_final.json:road_between_pitches | 8 m asphalt ribbon from [252,-12] to [128,-2]. No central island. | estimate from a camera solve: A broad pale approach lies between the eastern sport areas. A long central island splits its surface. It joins the outer apron. | resize | medium | JWNowpO44rw_000617.567.jpg (06:17.567)<br>JWNowpO44rw_000454.933.jpg (04:54.933) |
| track_ring_ne / layout_final.json:track_ring_ne | Dark asphalt track surface in finished state. | frame evidence: The near curved strip is dark while the infield contains soil and equipment. Earlier footage shows red track sections. | unknown | medium | JWNowpO44rw_000617.567.jpg (06:17.567)<br>JWNowpO44rw_000645.000.jpg (06:45.000)<br>LhY5-yDuhfc_000020.000.jpg (00:20.000) |
| apron_ring / site_layout_ge.json:apron_ring | 18 m pale ring outside the plinth. | inference: A continuous pale apron surrounds the bowl. Its width varies at plazas and sport areas. | keep | medium | JWNowpO44rw_000617.567.jpg (06:17.567)<br>JWNowpO44rw_000714.767.jpg (07:14.767) |
| ge_road_north_east / site_layout_ge.json:roads[0] | 9 m road curves north of the track, then follows its east side to z 73. | inference: A curved peripheral route skirts the track and joins the eastern paved approach. It does not run through the north plaza. | keep | medium | JWNowpO44rw_000617.567.jpg (06:17.567)<br>JWNowpO44rw_000641.633.jpg (06:41.633)<br>LhY5-yDuhfc_000020.000.jpg (00:20.000) |
| ge_east_building_a / site_layout_ge.json:buildings[0] | Plain roof mass, 16 m wide and 7 m high. | inference: Long low roofs stand east of the approach. The views support roof masses, but not exact wall heights or final function. | keep | medium | JWNowpO44rw_000617.567.jpg (06:17.567) |
| ge_east_building_b / site_layout_ge.json:buildings[1] | Plain roof mass, 22 m wide and 7 m high. | inference: Long low roofs stand east of the approach. The views support roof masses, but not exact wall heights or final function. | keep | medium | JWNowpO44rw_000617.567.jpg (06:17.567)<br>JWNowpO44rw_000714.767.jpg (07:14.767) |
| ge_east_hardstanding / site_layout_ge.json:car_parks[0] | Striped asphalt car park with illustrative cars and planted rows. | frame evidence: The east area contains roofs and work space. No complete final bay layout is resolved. | unknown | low | JWNowpO44rw_000617.567.jpg (06:17.567)<br>JWNowpO44rw_001246.333.jpg (12:46.333)<br>JWNowpO44rw_000506.533.jpg (05:06.533) |
| east_training_pitch / site_plan.json:pitch_se | Pitch centre [187.6,96.0], footprint 81.5 x 126.1 m. | estimate from a camera solve: A rectangular graded sport area lies south of the eastern approach. The filmed design model shows a marked green pitch. | keep | medium | JWNowpO44rw_000617.567.jpg (06:17.567)<br>JWNowpO44rw_000606.233.jpg (06:06.233) |
| north_east_track_footprint / site_plan.json:tracks[0] | Track and infield northeast of bowl. | inference: The track location and north-south orientation agree. Construction material covers the infield. | keep | medium | JWNowpO44rw_000617.567.jpg (06:17.567)<br>JWNowpO44rw_000645.000.jpg (06:45.000) |
| south_west_loop / layout_final.py:KEEP / sw_loop_road | Existing loop survives. Pass F fills its grass interior with cars. | inference: A rounded rectangular paved loop surrounds grass. It bends into the west apron beside the stand. | keep | medium | JWNowpO44rw_000714.767.jpg (07:14.767)<br>JWNowpO44rw_000716.317.jpg (07:16.317) |
| south_west_stand / layout_final.py:hide_finished / sw_stand prefix | Small stand hidden in finished state. | frame evidence: A long roofed stand lies west of the grass rectangle and loop. It is visible in D02. | unknown | medium | JWNowpO44rw_000714.767.jpg (07:14.767)<br>JWNowpO44rw_000716.317.jpg (07:16.317) |
| north_plaza / forecourt_layout.json:elements[id=plaza_edge] | Pale plaza with central round bed and two axial beds. | inference: A pale oval plaza contains a dark circular bed and two long beds. Pedestrian access connects toward Ngong Road. | keep | high | JWNowpO44rw_000645.000.jpg (06:45.000)<br>JWNowpO44rw_000659.633.jpg (06:59.633)<br>mJJ4Qkl858k_000014.000.jpg (00:14.000) |
| south_plaza / ground context visible in step_FF/step_FH renders | Pale plaza and central bed remain. | inference: D02 shows a pale elongated plaza east of the grass loop. It contains a round bed and axial beds. | keep | high | JWNowpO44rw_000714.767.jpg (07:14.767)<br>JWNowpO44rw_000716.317.jpg (07:16.317) |
| forecourt_paths / forecourt_layout.json:elements with path_ prefix / layout_final.py:fp_paths | Red paths. West paths hidden below the new car park. | inference: Crossed red paths divide the north lawns. They reach the plaza and skirt the track. The design model also shows these paths. | keep | medium | JWNowpO44rw_000645.000.jpg (06:45.000)<br>JWNowpO44rw_000659.633.jpg (06:59.633)<br>JWNowpO44rw_000441.933.jpg (04:41.933) |
| east_approach_island / no dedicated island in layout_final.json:road_between_pitches | Absent from the 8 m ribbon. | estimate from a camera solve: D03 shows a pointed elongated island along the centre of the broad approach. | add | medium | JWNowpO44rw_000617.567.jpg (06:17.567) |
| east_approach_flared_join / layout_final.py:ribbon / lf_road_between_pitches | Constant-width strip stops at [252,-12]. | inference: The eastern mouth spreads across the frontage. It joins a peripheral route around the sport areas. | add | medium | JWNowpO44rw_000617.567.jpg (06:17.567) |
| apron_approach_join / layout_final.py:ribbon / lf_road_between_pitches | 8 m strip ends abruptly against the apron. | inference: The pale approach merges into the outer apron. No road enters the internal arena in this view. | resize | medium | JWNowpO44rw_000617.567.jpg (06:17.567)<br>JWNowpO44rw_000454.933.jpg (04:54.933) |
| north_frontage / site_plan.json:ngong / road_lines.json:name=Ngong Road | Four lanes each way, 3.3 m each, 2 m median, plus edge and pedestrian strips. | frame evidence: Ngong Road is divided and carries traffic along the north boundary. Perspective does not settle all lane counts or total width. | unknown | medium | JWNowpO44rw_000645.000.jpg (06:45.000)<br>HU3J94fa8_c_000650.000.jpg (06:50.000) |
| external_vehicle_access / road_lines.json:Cemetery Road / layout_final.json:west_road | Pass F road ends at Ngong Road. The data does not supply a joined final junction. | frame evidence: Footage shows frontage works beside a live road. It does not continuously show a completed turn from Ngong Road into the site. | unknown | low | HU3J94fa8_c_001334.000.jpg (13:34.000)<br>HU3J94fa8_c_001822.000.jpg (18:22.000)<br>JWNowpO44rw_000645.000.jpg (06:45.000) |
| drop_off / not identified in layout_final.json or site_layout_ge.json | No dedicated drop-off is specified. | frame evidence: Vehicles and equipment appear on work surfaces. No marked final drop-off or lay-by is resolved. | unknown | low | JWNowpO44rw_000617.567.jpg (06:17.567)<br>h--Jmi7SwBs_000058.000.jpg (00:58.000) |
| west_hardstanding / layout_final.json:west_road / railway / station overlap this region | Straight transport corridor replaces parts of the west context. | frame evidence: D02 shows broad paved work areas northwest of the grass loop. Temporary use does not establish permanent parking. | unknown | medium | JWNowpO44rw_000714.767.jpg (07:14.767)<br>OB0OE-PAAVg_000012.345.jpg (00:12.346) |
| forest_belt / site_plan.json:trees / existing context | Southern forest context remains, with generic tree crowns. | inference: A dense forest belt borders the south side. It frames D02 and the L07 foreground. | keep | high | JWNowpO44rw_000714.767.jpg (07:14.767)<br>JWNowpO44rw_001232.600.jpg (12:32.600) |
| roadside_trees / site_layout_ge.py:road verge tree loop | Two tall tree rows on both verges of the northeast road. | frame evidence: The filmed design model shows regular roadside trees. Live footage shows uneven young planting and mature boundary trees. | unknown | medium | JWNowpO44rw_000612.433.jpg (06:12.433)<br>JWNowpO44rw_000617.567.jpg (06:17.567)<br>KEOmkVfjhu8_001330.000.jpg (13:30.000) |
| east_lawns_beds / forecourt_layout.json:elements[id=east_lawn] / fp_beds | Green lawn panels, red paths and planted beds. | inference: The north-east lawn panels contain grass and triangular red soil beds. The final planting density is unknown. | keep | medium | JWNowpO44rw_000645.000.jpg (06:45.000)<br>JWNowpO44rw_000659.633.jpg (06:59.633)<br>JWNowpO44rw_000441.933.jpg (04:41.933) |
| far_track / absent; layout_final_01/README.md gap 5 | No additional far track beyond the eastern pitch. | frame evidence: The design model shows two track ovals in total. A third distant track appears only in the disputed dusk photo. | unknown | low | JWNowpO44rw_000454.933.jpg (04:54.933)<br>JWNowpO44rw_000617.567.jpg (06:17.567) |

## Fix list in visual order

This list ranks visible effect on L06, L07, D01 to D03 and P01.
The targets describe proposed edits for the next builder. This audit changes no model file.
Items marked hold require the named lead decision first.

| Order | Main views | File and key or script section | Target values or shape | Basis and release condition |
|---|---|---|---|---|
| 1 | L07, D02, P01 far side | blender/data/layout_final.json:carpark_south_west. blender/context/layout_final.py:ZONES, hide_finished, car_park calls | Hold. If Q1 supports the drone layout, omit this lot and its planted strip. Restore sw_lawn and sw_stand. Use grass ring [-139,122], [-73,135], [-80,233], [-153,228]. Retain the existing surrounding loop. Do not add pitch markings. | Estimate from a camera solve, JWNowpO44rw_000714.767.jpg and _000716.317.jpg. Final retention requires Q1/Q3. |
| 2 | D01, P01, L06 background | blender/data/layout_final.json:carpark_north_west and spine_beds. blender/context/layout_final.py:ZONES and hide_finished | Hold. If Q1 supports the drone layout, omit the new lot. Restore fc_west_lawn and fc_path_west prefixes. Use forecourt_layout.json:west_lawn with app z = minus Blender y. Approximate envelope x -125 to -57, z -238 to -143. | Frame evidence, JWNowpO44rw_000645.000.jpg and _000659.633.jpg. Do not replace the lawn with bays on construction evidence alone. |
| 3 | D03, L06, P01 left side | blender/data/layout_final.json:road_between_pitches. blender/context/layout_final.py:ribbon calls for lf_road_between_pitches | Replace the constant 8 m ribbon with a pale paved polygon. Use [129,25], [129,-21], [283,-37], [298,10]. Add the island [144,2], [184,-11], [223,-1], [192,13]. Blend the west edge into the apron and flare the east mouth into the peripheral route. | Estimate from a camera solve, JWNowpO44rw_000617.567.jpg. Keep the total width at about 40 to 50 m. Q4 holds vehicle lanes and drop-off details. |
| 4 | L07, D02, D01, P01 right side | blender/data/layout_final.json:west_road, railway, station, footbridge. blender/context/layout_final.py:ZONES and transport sections | Hold all four items. Do not extend or realign the corridor from this audit. If Q1 rejects the dusk image as layout authority, omit these additions and restore the context that ZONES removes. No alternate rail alignment is proposed. | Inference from unresolved conflict. JWNowpO44rw_000617.567.jpg and _000714.767.jpg do not establish these features. Q1/Q2 control release. |
| 5 | D01, D03, L06, P01 | blender/data/layout_final.json:track_ring_ne. blender/context/layout_final.py:TRACKG and recolour section | Hold the uniform dark finished material. Retain the observed track footprint at [171,-120], about 166 x 87 m. Use separate track, infield and temporary soil surfaces. Do not change geometry to match a surface colour. | Frame evidence, JWNowpO44rw_000617.567.jpg and LhY5-yDuhfc_000020.000.jpg. Q5 selects the final surface. |
| 6 | D03, L06 | blender/data/site_layout_ge.json:roads[0]. blender/context/site_layout_ge.py:ribbon and verge tree loop | Retain the approximate 9 m peripheral route. Make its junction share the paved edge from item 3. Keep trees outside the approach envelope and junction. Do not close the junction with an uninterrupted tree row. | Inference, JWNowpO44rw_000617.567.jpg. The 7 to 10 m width range is an estimate. Q8 controls finished tree maturity. |
| 7 | D01, D02, P01, L06 | blender/data/forecourt_layout.json:elements. blender/context/layout_final.py:fp_paths, fp_beds, fc_murram | Retain both pale plazas, round beds, axial beds and red crossed paths. Restore any west paths only after item 2 clears Q1. Keep path widths at the inherited 3 to 5 m until stronger evidence exists. | Frame evidence and inference, JWNowpO44rw_000659.633.jpg and _000714.767.jpg. These are surface targets, not final planting specifications. |
| 8 | D03 edges, L06 background | blender/data/site_layout_ge.json:car_parks[0], buildings[0:2]. blender/context/site_layout_ge.py:car park section | Hold new bay rows, occupancy and roof-function claims. Retain approximate low roof masses. Preserve the eastern hardstanding envelope as an unresolved area. No new bay spacing is justified. | Frame evidence, JWNowpO44rw_000617.567.jpg. Q6 selects finished parking evidence. |
| 9 | D01 foreground, P01 foreground | blender/data/site_plan.json:ngong. blender/data/road_lines.json:Ngong Road and Cemetery Road | Retain existing frontage centrelines for review. Hold changes to lane count, final junctions and drop-off geometry. Add no direct vehicle route across the north plaza. | Frame evidence, JWNowpO44rw_000645.000.jpg and HU3J94fa8_c_001334.000.jpg. Q7 requires completed approach evidence. |

## Questions for the lead

- Q1: What is the provenance and capture date of dusk_aerial_finished_2026-10-17.jpg? Does it show the real completed site or an edited proposal? It conflicts with the two western green areas. Hold their finished replacements until this answer exists.
- Q2: What independent plan or completed footage establishes the west road, railway, station and footbridge? The supplied drone views do not settle their alignment. Do not resolve the railway from appearance alone.
- Q3: What is the final use of the south-west grass rectangle? D02 supports grass and a stand, but it does not resolve sport markings.
- Q4: What parts of the broad eastern paved approach carry vehicles? The geometry is visible, but final lanes, island finish and drop-off use remain unknown.
- Q5: What is the finished track surface? The dark construction strip and earlier red track do not settle the final material.
- Q6: Which completed view establishes the east and west parking footprints and bay rows? The architectural model supports design intent only.
- Q7: Which continuous view or approved plan establishes the completed Ngong Road vehicle approach, junction widths and drop-off areas? The frontage work footage does not settle them.
- Q8: Does the finished landscape retain the regular mature avenue from the architectural model? Live footage supports sparse young planting and existing boundary trees.
- Q9: Does a third track beyond the east sport areas exist? The supplied real-site frames do not establish its location.

These questions stop only the named items. The comparison, observed plan and other geometry recommendations remain available for review.

## Evidence sheets and handoff

- sheets/01_main.jpg shows the filmed design model, its parking pattern and its two-lane avenue.
- sheets/02_main.jpg shows D03, D01 and the north plaza detail.
- sheets/03_main.jpg shows D02, a nearby frame, a west apron view and design planting intent.
- sheets/04_other.jpg to sheets/06_other.jpg show construction stages, night lighting and local surfaces.
- sheets/07_model.jpg to sheets/09_model.jpg show all supplied renders and the earlier plan comparison.
- sheets/10_followup.jpg shows frontage earthworks at four indexed moments.
- sheets/11_followup.jpg shows local construction surfaces and night views.
- sheets/12_followup.jpg shows design paths, design sport areas and real-site context.
- sheets/13_plan.jpg compares the disputed model footprints with observed or inferred footprints.

Original source paths remain unchanged. The audit copies source pixels only into internal evidence sheets in this folder.
layout_plan.json holds 32 feature records. source_frames.json holds the frame states and timestamps.
camera_estimates.json holds the selected pixels and computed coordinates.
audit_tools.py reproduces the nine frame sheets and camera estimates without Blender.
build_plan.py reproduces the JSON and the separate comparison table.
make_plan_image.py reproduces the schematic plan. validate_audit.py performs the structural acceptance tests.

The lead reviews the proposed plan and answers Q1 to Q9 before the builder changes disputed finished geometry.
The builder must retain separate asbuilt and finished states. This audit approves no rendering, baking or export.

No tool guarantees STE compliance. The official dictionary is free at asd-ste100.org.

## Acceptance record

Software result: the plan contains 32 features and all 14 required model features.
All 32 rows cite indexed frames. Every plan feature has evidence and a state.
All 13 JPEG sheets decode. The JSON parser accepts layout_plan.json.
The three longest descriptive sentences contain 20, 18 and 18 words.
The text scan finds no banned modal, asterisk or em dash. The scan does not prove dictionary compliance.

The first full validate_audit.py run stopped at the worktree scope test.
It reported: AssertionError: ?? engineering/landmarks_01/LANDMARK_CANDIDATES.md
Another process then committed the shared worktree in 67ffc4e. That commit includes an earlier audit draft and unrelated work.
The audit preserves that commit and all unrelated files. The final status contains changes only under engineering/layout_audit_01/.
The final full validator run passes the content and path scope tests. Acceptance 7 remains incomplete because final updates are uncommitted.

The original paths remain intact. The destination is engineering/layout_audit_01/.
Operation: derived report and internal contact sheets. Source preservation: yes. Network publication by this worker: none.
The lead receives a local review artifact with unresolved finished-state authority.

Git staging initially succeeded for this folder. The final staging attempt failed with this exact error:

fatal: Unable to create '/home/munene/CEO/14_talanta_twin/.git/worktrees/talanta_layout_audit/index.lock': Read-only file system

The earlier audit snapshot is in commit 67ffc4e. The working files contain the final updates.
The lead must stage and commit those updates when Git metadata permits writes. This worker made no commit or push.
