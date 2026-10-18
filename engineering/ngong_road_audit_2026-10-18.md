# Ngong Road audit

Date: 2026-10-18. Project: Talanta Twin, track undecided. Status: software implementation for lead review.
Source paths: `blender/data/site_plan.json`, `gis/parameter_ledger.csv`, `blender/data/road_lines.json`, and the historian frames below.
Handoff: regenerate the shared lanes before web traffic, then integrate the Blender module before the scene save.
Evidence class: software and Visualization. No physical measurements or traffic capacity results appear here.
Existing sources remain intact. The initial branch `codex/ngong-road` had no local changes.

## Frame evidence and assumptions

The notes use seconds. Frame filenames use MMSS. The initial missing-frame report was wrong.
405.000 seconds maps to `JWNowpO44rw_000645.000.jpg`. 401.633 seconds maps to `JWNowpO44rw_000641.633.jpg`.
07:04 maps to `JWNowpO44rw_000704.867.jpg`. These three images were inspected directly.
The keep list is `research/video_index/drone_keyframes_2026-10-17.csv`.

The first two frames show two carriageways, moving vehicles, a planted median, roadside lighting, and unfinished verges beside the site.
The 07:04 view shows multiple marked lanes, a narrow raised median, and roadside activity.
Perspective, traffic, and image cropping prevent a reliable count of every through lane along the complete site edge.
The images do not establish lane widths, turn-lane extents, or a separate continuous service carriageway.
No confirmed bus stopping bay appears in these views. The implementation adds no stop or pull-in maneuver.

`engineering/environment_from_drone_2026-10-17.md` records the planted median and two-way traffic.
Detail sheet SR20 estimates 2–3 lanes from concepts. The ledger records 3–4 lanes by eye from the historian 07:04 frame.
Neither source provides a measured cross section. Historian footage outranks concepts 06 and 07.
Following the lead fallback, the existing Blender dimensions remain estimated.

The old and new `ngong` values are identical: `lanes_per_dir=4.0`, `lane_w=3.3`, `median_w=2.0`, and `half_carriageway=14.7` m.
`edge_strip_w=0.5`, `service_w=4.0`, and `half=22.4` m also remain unchanged.
The service width describes the existing murram strip. It does not establish another traffic carriageway.
The existing Blender concrete barrier differs from the planted median in the notes. This work leaves the cloud-owned mesh script intact.

## Defects and numbers

The former generator used `road_lines.json`: 93 segments total, including 54 named Ngong Road segments.
That source omits one-way tags. Paired, separated carriageways are apparent in its coordinates.
For example, near x=-1409 m, separate ways pass z=101.93 and z=121.95 m, about 20 m apart.
The generator assigned two opposing directions to every joined carriageway.
Its previous output contained 5 Ngong sections and 20 lane polylines, totaling 25,189.3 lane meters.
Ten pairs of opposing lane polylines approached within 1 m at sampled segment projections.
This is geometric duplication and opposing flow on mapped carriageways, not twenty supported through lanes.

The previous offsets were ±3.75 and ±7.25 m from each mapped way, with 3.5 m lanes and a 4 m reserve.
The Blender mesh uses a separate 531-point median centerline, four 3.3 m lanes per direction, and a 2 m median.
Its lane-center offsets are ±2.65, ±5.95, ±9.25, and ±12.55 m.
Even the same-centerline assumption gives nearest-center errors of 1.10 and 1.30 m for the two old positive offsets.
An approximate cross-section comparison of 572 previous points found only 70 within 0.3 m of the mesh lane-center offsets.
The median residual was 1.35 m. The maximum was 20.56 m. Absolute offsets ranged from 0.01 to 33.11 m.
These software figures describe disagreement between sources. They do not measure the physical road.

The former offset helper used `(dz,-dx)`, which is physically left in app coordinates.
That local sign was correct. The defect came from treating each separate carriageway as a two-way road.
The Blender mesh uses the opposite normal, `(-dz,dx)`. Reusing that sign without reversing travel would create right-hand traffic.
The new generator explicitly assigns forward travel to negative mesh offsets and reverse travel to positive offsets.
Kenya keep-left travel is the work-order premise. A test also checks the physical cross product in Blender coordinates.

Both `pointAt` and vehicle advancement formerly used distance modulo lane length.
This immediately moved a visible vehicle from its lane end to its start.
Several old endpoints were inside the disc, including radii near 1229, 1236, 1317, and 1429 m.
The old generator also clipped the centerline before offsets, so shifted endpoints missed the intended boundary.

## Shared layout and behavior

`app/tools/make_ngong_lanes.mjs` produces `blender/data/ngong_lanes.json` from `site_plan.json ngong.mid`.
It also compares the lane width with the ledger because the Blender mesh reads that ledger value.
Each lane contains direction, keep-left, width, outer-left status, claim, and polylines in both horizontal coordinate frames.
Coordinates remain in meters about the pitch center. Blender uses east/north. The app uses east/south.

Ngong lane ends extend along their end tangents before clipping. These extensions are estimated continuation beyond the existing mesh endpoints.
The static Blender vehicles stay inside the original mesh length. The web clips the extended lanes to the 1500 m disc.
A cloud mesh extension is outside this ownership scope. Road surface continuity beyond the original endpoints needs cloud review.

Other roads receive one keep-left lane each way. Named connected segments join before offsets.
The generator suppresses parallel chains within 30 m where over 80% of sampled points match and tangent alignment exceeds 0.95.
No additional non-Ngong parallel chain matched that rule in this dataset.
The missing direction tags prevent a claim of verified real-world routing on those roads.
The web omits sections without both usable directions. The final output has 8 road sections and 22 lane polylines.

Vehicle free-flow targets are 30–60 km/h. Queues and entry acceleration can reduce actual speeds below 30 km/h.
Leader spacing uses vehicle lengths and at least 3 m clearance. Estimated junction slowdowns create queues without a measured signal plan.
Buses and nganyas favor the outer left lane. The frames do not justify a stopping bay.
Vehicles shrink over the last 15 m of a lane, remain hidden for 1–4 seconds, and wait for entry clearance before respawn.
All Ngong entries and departures occur at the disc boundary. Other road chains can terminate inside the disc and use hidden endpoint respawns.
The exported API remains `buildTraffic({lines, groundAt, camera, count, proxyDistance}) -> {group, update, setLimit}`.

## Software evidence

Run these commands from the repository root:

```sh
node app/tools/make_ngong_lanes.mjs
node app/tools/make_traffic_lines.mjs
node app/tools/make_ngong_lanes.mjs --check
node --check app/src/hero/traffic.js
node --check app/tools/make_ngong_lanes.mjs
node --check app/tools/make_traffic_lines.mjs
python3 -m py_compile blender/context/traffic.py
```

The geometry test also compares the final web export against the shared source. It printed:

```text
PASS web export: 8 lanes match shared centers within 0.002 m; 16 endpoints on the 1500 m boundary.
PASS: 8 Ngong lanes; maximum mesh center error 0.000000 m; minimum left offset 2.65 m; separation 3.30 m; no overlapping centers; all directions keep-left; 23 clipped lane parts.
```

The 23 parts include one unusable single-direction road fragment. The web exporter removes that road section, leaving 22 lanes.
A separate endpoint test printed `PASS: 16 Ngong endpoints on the 1500 m clip boundary within 0.002 m.`
All three Node syntax commands and Python compilation returned no errors.
An initial syntax invocation used the wrong working directory. The commands above then ran successfully from the repository root.

A 600-second Node test inspected stable car, bus, and boda instance slots:

```text
PASS software traffic: 600 seconds, 2443380 stable visible matrix samples, 242220 hidden samples, maximum visible step 4.154 m; matrices finite; setLimit and empty API callable.
```

The initial test incorrectly treated compacted nganya instance slots as permanent vehicle identities and reported a false teleport.
The revised test excludes those compacted slots. The following test uses temporary private-state access without changing the production API:

```text
PASS software following: 600 seconds; 1164 hidden respawns; minimum bumper gap 4.010 m; desired speeds 30-60 km/h; 87/104 Ngong transit vehicles in the left lane.
```

That harness is `/tmp/ngong_runtime_check.mjs`. Run `node /tmp/ngong_runtime_check.mjs` from this repository while that temporary file exists.
Node cannot load the relative nganya asset URL without a browser. The existing proxy fallback remained active.

The single permitted empty-scene Blender invocation used the prescribed flock, factory startup, and one thread.
It imported `traffic`, deleted default objects, called `traffic.build(bpy.context.scene, Path.cwd())`, and asserted nonzero vehicles below 60000 triangles.
It printed:

```text
TRAFFIC_BUILD {"evidence": "software; Visualization", "seed": 704, "vehicles": 490, "counts": {"car": 415, "bus": 17, "nganya": 58}, "triangles": 35484, "minimum_bumper_gap_m": 6.632}
PASS EMPTY SCENE TRAFFIC {'evidence': 'software; Visualization', 'seed': 704, 'vehicles': 490, 'counts': {'car': 415, 'bus': 17, 'nganya': 58}, 'triangles': 35484, 'minimum_bumper_gap_m': 6.632}
```

Blender then stalled during shutdown after `pa_write() failed while trying to wake up the mainloop: Operation not permitted`.
The session was interrupted with Ctrl-C and returned 130. The build assertions passed, but clean Blender termination did not.
The shared lane directions changed after this smoke test. The final directions passed the Node geometry tests.
The one-test limit prevented another Blender invocation. No scene was opened or rendered.

The single Vite command ran in `app/`: `npx vite build --logLevel error --outDir dist-ngong`.
It returned zero with no error output. Its generated index was 5226 bytes. The temporary build folder was removed.

## Integration and budgets

The public Blender function is `build(scene, root)`. It returns vehicle counts, triangles, seed, and minimum spacing.
Add these exact lines at the end of `blender/build_site_detail.py`, before its save:

```python
from context import traffic as traffic_context
traffic_context.build(scene, ROOT)
```

The Blender module uses plain low-poly cars, buses, and nganyas, with no names, logos, or imported licensed vehicle assets.
It places estimated queues near mapped road endpoints. It reads existing road and terrain surfaces when available.
The empty-scene fallback reads the terrain binary. Surface placement in the full scene remains untested.
The smoke build used 35484 triangles against a 60000-triangle ceiling.
The shared JSON uses 379834 bytes. The generated web JSON uses 122955 bytes.

The browser appearance, loaded nganya model, final Blender directions, full-scene surface contact, and rendered stills remain untested.
Cloud review must assess the estimated lane count, barrier appearance, tangent continuation, and surface coverage beyond the current mesh.
No physical traffic study, safety simulation, public release, commit, or push occurred.
