"""Stage 00: write gis/parameter_ledger.csv.

One row for each dimension the model uses. Measured rows are computed here from the W1b CSVs
in gis/measurements/ (EPSG:32737, relative to the twin origin), so the ledger can be rebuilt.
Estimated rows copy the constants in app/src/world/bowl.js, site.js and pitch.js, with the
measured value they should be checked against where one exists.

Local frame (same as the app): origin = W1b pitch-zone centroid, x = east, z = south, y = up.
Run: ~/.venvs/gis/bin/python gis/scripts/build_parameter_ledger.py
"""
import csv, json, math
from pathlib import Path
from pyproj import Transformer
from shapely.geometry import Polygon

ROOT = Path(__file__).resolve().parents[2]
MEAS = ROOT / "gis/measurements"
MAN = json.loads((ROOT / "app/public/data/manifest.json").read_text())
OX, OY = MAN["origin_utm"]
TO_UTM = Transformer.from_crs(4326, 32737, always_xy=True)
GE = "Google Earth Pro 7.3.7, Munene"
IMG = "2025-12-26 (Airbus)"
COLS = ["name", "value", "unit", "source", "date", "method", "uncertainty", "status", "used_in", "note"]
rows = []


def add(name, value, unit, source, date, method, unc, status, used_in="", note=""):
    rows.append(dict(zip(COLS, [name, value, unit, source, date, method, unc, status, used_in, note])))


def poly(fn, order_col=None):
    r = list(csv.DictReader(open(MEAS / fn)))
    pts = [TO_UTM.transform(float(a["lon"]), float(a["lat"])) for a in r]
    return Polygon([(x - OX, y - OY) for x, y in pts])


def rect(P):
    c = list(P.minimum_rotated_rectangle.exterior.coords)
    e = [math.dist(c[i], c[i + 1]) for i in range(2)]
    k = 0 if e[0] >= e[1] else 1
    b = math.degrees(math.atan2(c[k + 1][0] - c[k][0], c[k + 1][1] - c[k][1])) % 180
    return max(e), min(e), b


def shape_rows(key, fn, what, unc_size, unc_pos, used_in="", note=""):
    P = poly(fn)
    L, W, b = rect(P)
    c = P.centroid
    src = f"{GE}; gis/measurements/{fn}"
    m = "min. area rectangle in EPSG:32737"
    add(f"{key}.length", round(L, 1), "m", src, IMG, m, unc_size, "measured", used_in, what + note)
    add(f"{key}.width", round(W, 1), "m", src, IMG, m, unc_size, "measured", used_in, what)
    add(f"{key}.area", round(P.area), "m2", src, IMG, "polygon area, EPSG:32737", "", "measured", used_in, what)
    add(f"{key}.bearing", round(b, 1), "deg", src, IMG, "long axis of min. rectangle (0-180)", "+-2 deg", "measured", used_in, what)
    add(f"{key}.centroid_x", round(c.x, 1), "m east", src, IMG, "area centroid, local frame", unc_pos, "measured", used_in, what)
    add(f"{key}.centroid_z", round(-c.y, 1), "m south", src, IMG, "area centroid, local frame", unc_pos, "measured", used_in, what)
    return P, L, W


# ---------------------------------------------------------------- frame
add("origin.lon", MAN["origin_lonlat"][0], "deg", f"{GE}; pitch_zone_w1b_2026-10-16.csv", IMG, "centroid of the W1b pitch zone", "+-2 m", "measured", "export_web.py", "twin origin")
add("origin.lat", MAN["origin_lonlat"][1], "deg", f"{GE}; pitch_zone_w1b_2026-10-16.csv", IMG, "centroid of the W1b pitch zone", "+-2 m", "measured", "export_web.py", "")
add("origin.ground_elev", MAN["ground_elev_m"], "m AMSL", "Copernicus GLO-30 DEM", "2021", "DEM sample at the origin", "+-4 m", "derived", "export_web.py", "")
add("site.pad_y", MAN["features"]["site_pad_y"], "m", "GLO-30 DEM over the site boundary", "2021", "graded pad height relative to the origin", "+-2 m", "derived", "main.js PAD", "")
add("pitch.bearing", MAN["features"]["pitch_bearing_deg"], "deg", f"{GE}; pitch_zone_w1b_2026-10-16.csv", IMG, "long axis of the pitch zone", "+-1 deg", "measured", "bowl.js, site.js, pitch.js", "agrees with the roof rings (179.6, 181 deg)")

# ---------------------------------------------------------------- W1b shapes
shape_rows("pitch_zone", "pitch_zone_w1b_2026-10-16.csv", "bare-earth pitch zone, no markings", "+-1.5 m", "+-2 m", "pitch.js PITCH.zoneL/zoneW", "")
_, plL, plW = shape_rows("bowl_plinth", "bowl_plinth_w1b_2026-10-17.csv", "bowl outline at ground level", "+-2 m", "+-2 m", "bowl.js rOut (via bowl_outer)", "; N and E sides partly hidden by the roof")
ro, roL, roW = shape_rows("roof_outer", "roof_outer_w1b_2026-10-17.csv", "roof-top outer ring (steel frame)", "+-3 m", "+-20 m (relief displacement)", "bowl.js rOut", "; 12 points, corners cut")
ri, riL, riW = shape_rows("roof_inner", "roof_inner_w1b_2026-10-17.csv", "roof inner edge (opening)", "+-2 m", "+-20 m (relief displacement)", "bowl.js BOWL_EST.opening")
shape_rows("plaza_north", "north_plaza_w1b_2026-10-17.csv", "north forecourt plaza (eye/shield shape)", "+-2 m", "+-2 m", "site.js plazaC/half/depth")
shape_rows("warmup_track", "warmup_track_w1b_2026-10-17.csv", "warm-up track oval east of the bowl", "+-5 m (6 points)", "+-3 m", "manifest sport[track]")
shape_rows("training_pitch_se", "training_pitch_se_w1b_2026-10-17.csv", "training pitch SE, grass edge", "+-2 m", "+-2 m", "manifest sport[pitch 2]")
shape_rows("training_field_sw", "training_pitch_sw_w1b_2026-10-17.csv", "training field SW, earthworks", "+-3 m", "+-3 m", "not modelled yet")
S = poly("site_boundary_w1b_2026-10-16.csv")
add("site.boundary_area", round(S.area), "m2", f"{GE}; site_boundary_w1b_2026-10-16.csv", IMG, "polygon area, EPSG:32737", "+-1%", "measured", "manifest site", "8 points")

# relief displacement of roof-level outlines (roof centroids against the plinth centroid)
pl = poly("bowl_plinth_w1b_2026-10-17.csv").centroid
dx = ((ro.centroid.x + ri.centroid.x) / 2 - pl.x); dz = -((ro.centroid.y + ri.centroid.y) / 2 - pl.y)
add("roof.relief_shift_x", round(dx, 1), "m east", "roof_outer, roof_inner, bowl_plinth CSVs", IMG, "mean roof-ring centroid minus plinth centroid", "+-3 m", "derived", "subtract from roof-level positions", "oblique image; roof is centred on the plinth")
add("roof.relief_shift_z", round(dz, 1), "m south", "roof_outer, roof_inner, bowl_plinth CSVs", IMG, "as above", "+-3 m", "derived", "", "")
add("roof.depth_side", round((roW - riW) / 2, 1), "m", "roof_outer, roof_inner", IMG, "(outer width - inner width) / 2", "+-3 m", "derived", "bowl.js shoulderW + roof span", "")
add("roof.depth_end", round((roL - riL) / 2, 1), "m", "roof_outer, roof_inner", IMG, "(outer length - inner length) / 2", "+-3 m", "derived", "", "")
add("roof.band_area", round(ro.area - ri.area), "m2", "roof_outer, roof_inner", IMG, "outer area - opening area", "+-3%", "derived", "", "plan area of the roof")
add("roof.overhang_side", round((roW - plW) / 2, 1), "m", "roof_outer, bowl_plinth", IMG, "(roof outer width - plinth width) / 2", "+-3 m", "derived", "bowl.js facadeInset/plinthInset", "roof edge beyond the ground outline; oblique view may widen it (check in 01b)")
add("roof.overhang_end", round((roL - plL) / 2, 1), "m", "roof_outer, bowl_plinth", IMG, "(roof outer length - plinth length) / 2", "+-3 m", "derived", "", "negative: the roof ends inside the ground outline at the ends")

# ---------------------------------------------------------------- bowl outline used by the app (OSM)
bo = Polygon(MAN["features"]["bowl_outer"])
bx = [p[0] for p in MAN["features"]["bowl_outer"]]; bz = [p[1] for p in MAN["features"]["bowl_outer"]]
add("bowl_outer.length", round(max(bz) - min(bz), 1), "m", "OSM building r20072298", "2025", "N-S extent of the OSM outline", "+-5 m", "derived", "bowl.js rOut", f"measured plinth {plL:.1f} m")
add("bowl_outer.width", round(max(bx) - min(bx), 1), "m", "OSM building r20072298", "2025", "E-W extent of the OSM outline", "+-5 m", "derived", "bowl.js rOut", f"measured plinth {plW:.1f} m")
add("bowl_outer.centroid_x", round(bo.centroid.x, 1), "m east", "OSM building r20072298", "2025", "area centroid", "+-5 m", "derived", "bowl.js rOut", f"measured plinth {pl.x:.1f} m: the OSM outline sits about {bo.centroid.x - pl.x:.0f} m east")
add("bowl_outer.centroid_z", round(bo.centroid.y, 1), "m south", "OSM building r20072298", "2025", "area centroid", "+-5 m", "derived", "bowl.js rOut", f"measured plinth {-pl.y:.1f} m")

# ---------------------------------------------------------------- pitch.js
LOG = "IFAB Laws of the Game, Law 1"
add("pitch.length", 105, "m", "assumed FIFA recommended size", "", "assumption", "100-110 m", "estimated", "pitch.js PITCH.L", "derive from the camera match (stage 01b)")
add("pitch.width", 68, "m", "assumed FIFA recommended size", "", "assumption", "64-75 m", "estimated", "pitch.js PITCH.W", "")
for k, v in [("penalty_area.depth", 16.5), ("penalty_area.width", 40.32), ("goal_area.depth", 5.5), ("goal_area.width", 18.32),
             ("centre_circle.radius", 9.15), ("penalty_spot.distance", 11), ("goal.width", 7.32), ("goal.height", 2.44), ("corner_arc.radius", 1)]:
    add(f"pitch.{k}", v, "m", LOG, "", "fixed by the Laws of the Game", "0", "derived", "pitch.js PITCH", "")
add("pitch.line_width", 0.12, "m", LOG, "", "Law 1 maximum", "0", "derived", "pitch.js", "")
add("pitch.grass_bands", 18, "count", "look choice", "", "mowing pattern", "", "estimated", "pitch.js bands", "")

# ---------------------------------------------------------------- bowl.js BOWL_EST (all estimated)
FR = "reference frames JWNowpO44rw (look); press facts"
B = "bowl.js BOWL_EST"
e = lambda n, v, u, unc, used, note="", src=FR, m="estimate from frames, to be derived in stage 01b": add(n, v, u, src, "2026-10-16", m, unc, "estimated", used, note)
e("bowl.seat_start.half_long", 59.5, "m", "+-3 m", f"{B}.seatStart", "front row from the pitch centre along the long axis")
e("bowl.seat_start.half_wide", 39.5, "m", "+-3 m", f"{B}.seatStart")
e("bowl.seat_start.corner_r", 14, "m", "+-4 m", f"{B}.seatStart")
add("bowl.opening.half_long", 63, "m", "Sentinel-2 opening area (about 9,900 m2)", "2026", "rounded rectangle sized to the S2 area", "+-3 m", "estimated", f"{B}.opening", f"measured roof inner ring: half length {riL / 2:.1f} m")
add("bowl.opening.half_wide", 40, "m", "Sentinel-2 opening area", "2026", "as above", "+-3 m", "estimated", f"{B}.opening", f"measured: half width {riW / 2:.1f} m")
e("bowl.opening.corner_r", 20, "m", "+-5 m", f"{B}.opening")
e("bowl.back_setback", 9, "m", "+-3 m", f"{B}.backSetback", "back of the top row inside the outer edge")
e("bowl.plinth_h", 5.5, "m", "+-1.5 m", f"{B}.plinthH")
e("bowl.plinth_inset", 8, "m", "+-3 m", f"{B}.plinthInset", f"compare roof.overhang_side")
e("bowl.facade_inset", 7, "m", "+-3 m", f"{B}.facadeInset")
e("bowl.bulge_y", 30, "m", "+-5 m", f"{B}.bulgeY", "height of the widest point of the facade")
e("bowl.shoulder_w", 15, "m", "+-5 m", f"{B}.shoulderW")
e("bowl.shoulder_h", 24, "m", "+-5 m", f"{B}.shoulderH")
add("bowl.roof_top_y", 54, "m", "bulge_y + shoulder_h", "2026-10-16", "derived from two estimates", "+-6 m", "estimated", "bowl.js topY", "press: 56 m maximum height")
add("bowl.max_height_press", 56, "m", "research/Talanta_design_facts_2026-10-16.md (press)", "2026", "press statement", "unknown", "estimated", "check for bowl.roof_top_y", "")
e("bowl.opening_y", 47, "m", "+-5 m", f"{B}.openingY", "roof inner edge height")
e("bowl.roof_sag", 1.5, "m", "+-1 m", "bowl.js P() roof", "membrane sag between crest and opening")
for t in [("lower", 0.0, 0.38, 1.2, 12.5, 24, "#2c7a46"), ("middle", 0.45, 0.66, 20.5, 29.5, 13, "#b0232b"), ("upper", 0.70, 1.0, 33.0, 46.0, 21, "#b0232b to #1c1b1b")]:
    n, t0, t1, y0, y1, rows_, col = t
    e(f"bowl.tier_{n}.t0", t0, "fraction", "+-0.05", f"{B}.tiers", "fraction of the rake from front row to back wall")
    e(f"bowl.tier_{n}.t1", t1, "fraction", "+-0.05", f"{B}.tiers")
    e(f"bowl.tier_{n}.y0", y0, "m", "+-2 m", f"{B}.tiers")
    e(f"bowl.tier_{n}.y1", y1, "m", "+-2 m", f"{B}.tiers")
    e(f"bowl.tier_{n}.rows", rows_, "count", "+-4", f"{B}.tiers", "count in stage 01b")
    add(f"bowl.tier_{n}.seat_colour", col, "hex", "research/Talanta_design_facts_2026-10-16.md; frames", "2026-10-16", "design facts and frames", "", "estimated", f"{B}.tiers", "")
e("bowl.band.base_wall_h", 1.2, "m", "+-0.5 m", "bowl.js band(0)", "pitch-side wall")
e("bowl.band.lower_back_y0", 12.5, "m", "+-2 m", "bowl.js band(0.38)")
e("bowl.band.vip_glass_y0", 14.5, "m", "+-2 m", "bowl.js band(0.45)", "VIP glazing band")
e("bowl.band.vip_glass_y1", 20.5, "m", "+-2 m", "bowl.js band(0.45)")
e("bowl.band.middle_back_y1", 31.0, "m", "+-2 m", "bowl.js band(0.66)")
e("bowl.band.upper_front_y1", 33.0, "m", "+-2 m", "bowl.js band(0.70)")
e("bowl.back_wall_h", 46, "m", "+-4 m", "bowl.js back wall quad")
add("bowl.seat_pitch", 0.5, "m", "typical stadium seat width", "", "standard practice", "0.45-0.55 m", "estimated", f"{B}.seatPitch", "do not tune to force capacity (V4 failed: 56,972 against 60,000)")
e("bowl.aisle_every", 16, "seats", "+-4", f"{B}.aisleEvery")
e("bowl.aisle_w", 1.3, "m", "+-0.3 m", f"{B}.aisleW")
add("bowl.capacity_target", 60000, "seats", "research/Talanta_design_facts_2026-10-16.md (press)", "2026", "press statement", "unknown", "estimated", "validation V4", "")
add("bowl.seats_modelled", 56972, "seats", "app console (seatCount)", "2026-10-17", "count of seat instances", "", "derived", "bowl.js seats", "V4 failed: 5.05% short")
add("bowl.seat.width", 0.44, "m", "typical plastic stadium seat", "", "standard practice", "+-0.04 m", "estimated", "bowl.js seatGeometry", "")
add("bowl.seat.pan_h", 0.42, "m", "typical plastic stadium seat", "", "standard practice", "+-0.04 m", "estimated", "bowl.js seatGeometry", "")
e("bowl.shields.count", 8, "count", "+-0", f"{B}.shields", "count in stage 01b", src="research/Talanta_design_facts_2026-10-16.md; frames")
e("bowl.shield.width", 21, "m", "+-4 m", f"{B}.shieldW")
e("bowl.shield.y0", 6.5, "m", "+-3 m", f"{B}.shieldY0")
e("bowl.shield.y1", 46, "m", "+-4 m", f"{B}.shieldY1")
e("bowl.shield.offset", 2.6, "m", "+-1 m", "bowl.js surf(th, j, 2.6)", "shield face off the facade")
e("bowl.spear.offset", 1.5, "m", "+-1 m", "bowl.js spears", "spears behind the shield")
e("bowl.spear.radius", 0.5, "m", "+-0.2 m", "bowl.js spears")
add("bowl.shield.red", "#d0202a", "hex", "frames (look)", "2026-10-17", "colour pick by eye", "", "estimated", "bowl.js shieldTexture", "")
e("bowl.lattice.members", 40, "count per direction", "+-8", f"{B}.lattice", "count in stage 01b")
e("bowl.lattice.tube_r", 0.42, "m", "+-0.15 m", "bowl.js TubeGeometry 0.42")
e("bowl.lattice.ring_r", 0.5, "m", "+-0.15 m", "bowl.js horizontal rings")
e("bowl.roof.ribs", 60, "count", "+-12", "bowl.js rib every 4 of N=240", "count in stage 01b")
e("bowl.roof.rib_r", 0.22, "m", "+-0.1 m", "bowl.js rib tubes")
e("bowl.roof.ring_beam_r", 0.9, "m", "+-0.3 m", "bowl.js opening ring beam")
e("bowl.roof.trusses", 60, "count", "+-12", "bowl.js truss nT = N/4")
e("bowl.roof.truss_depth", 2.4, "m", "+-1 m", "bowl.js truss scale")
e("bowl.roof.truss_width", 0.6, "m", "+-0.3 m", "bowl.js truss scale")
e("bowl.floodlights.offset_out", 2, "m", "+-1 m", "bowl.js floodlights", "outside the opening edge")
e("bowl.floodlights.drop", 2.6, "m", "+-1 m", "bowl.js floodlights", "below the opening edge")
e("bowl.led_ring.r", 0.35, "m", "+-0.2 m", "bowl.js led-ring")
e("bowl.concourse.width_out", 6, "m", "+-3 m", "bowl.js concourse", "paved ring outside the outer edge")
# Blender blockout wall profile (stage 01b fallback). The 07:04 aerial could not be solved: no ground-level
# W1b point is identifiable in it. Shape fixed by eye against that frame; values stay estimated.
EYE = "JWNowpO44rw 07:04 (by eye, no camera solve)"
add("bowl.profile.wall", "near-vertical", "shape", EYE, "2026-10-17", "by eye: silhouette edges straight from plinth to rim", "", "estimated", "blender/build_blockout.py profile()", "replaces the bowl.js bulge (bulge_y, shoulder_w, shoulder_h) in the blockout only")
add("bowl.profile.shoulder_r", 8, "m", EYE, "2026-10-17", "by eye: tight rounded edge between wall and roof rim", "+-4 m", "estimated", "blender/build_blockout.py profile()", "")
add("bowl.profile.height_to_width_704", 0.20, "ratio", EYE, "2026-10-17", "by eye: 82 px rim-to-base over 413 px silhouette width", "+-0.02", "estimated", "check for bowl.roof_top_y", "about 50 m if the view is across the 250 m long side; view direction not solved")
add("bowl.profile.lattice_members_704", 20, "count per direction", EYE, "2026-10-17", "by eye: about 7 diamonds across the visible facade", "+-4", "estimated", "blender/build_blockout.py lattice", "bowl.js uses 40")
# Stage 02b facade details for the Blender build (lead review 2026-10-17). By eye from named
# historian frames (look references only, never textures); all estimated.
fe = lambda n, v, u, frames, method, unc, used, note="": add(n, v, u, f"JWNowpO44rw {frames} (by eye)", "2026-10-17", method, unc, "estimated", used, note)
BB = "blender/build_blockout.py"
fe("bowl.fin.pitch", 0.6, "m", "10:28, 12:12", "by eye: fin spacing against the 1 m spear shaft", "+-0.2 m", f"{BB} louvre_fins")
fe("bowl.fin.depth", 0.7, "m", "10:28", "by eye: fin depth against the spacing", "+-0.3 m", f"{BB} louvre_fins")
fe("bowl.fin.drop", 0.25, "m", "10:28, 12:16", "by eye: fins slope down outward", "+-0.15 m", f"{BB} louvre_fins")
fe("bowl.fin.backing_inset", 1.4, "m", "10:28, 12:12", "by eye: dark openings behind the fins", "+-0.5 m", f"{BB} facade_backing")
fe("bowl.lattice.section_w", 1.5, "m", "12:12, 12:16", "by eye: member width against the 1 m spear shaft", "+-0.4 m", f"{BB} lattice", "trapezoid section, flat face out")
fe("bowl.lattice.section_d", 0.8, "m", "12:12", "by eye: member stands proud of the fins", "+-0.3 m", f"{BB} lattice")
fe("bowl.shield.blockout_y0", 6.0, "m", "12:12, 12:16, 12:40", "by eye: shield foot at the bottom of the louvred band", "+-2 m", f"{BB} shields")
fe("bowl.shield.blockout_y1", 45.5, "m", "12:12, 12:16, 12:40", "by eye: shield tip just under the fascia; about 95% of the louvred band, 85-90% of ground-to-fascia height", "+-2 m", f"{BB} shields", "bowl.js uses shield.y0/y1")
fe("bowl.shield.bulge", 1.2, "m", "12:12, 12:16", "by eye: slight convex bulge at the centre", "+-0.6 m", f"{BB} shields")
fe("bowl.spear.span_shields", 1.4, "shield widths", "12:12, 00:16", "by eye: horizontal reach of each crossed spear", "+-0.2", f"{BB} spears")
fe("bowl.spear.blade_len", 6.5, "m", "10:28, 12:12", "by eye: blade length against the shield height", "+-2 m", f"{BB} spears")
fe("bowl.spear.blade_r", 1.2, "m", "10:28", "by eye: blade about 2.4 shaft widths", "+-0.4 m", f"{BB} spears")
fe("bowl.spear.tip_below_fascia", 0.6, "m", "10:28, 12:12", "by eye: blade tips stop just under the roof edge", "+-0.5 m", f"{BB} spears", "never above the roof edge")
add("bowl.mesh.N", 240, "segments", "model resolution", "", "not a dimension", "", "estimated", f"{B}.N", "")

# ---------------------------------------------------------------- site.js (all estimated, W1b now measures some)
SF = "site.js buildSite"
FRS = "reference frames JWNowpO44rw 04:45, 20:05; 8n3ILabO8uw; CuS83a44PG8 (look)"
s = lambda n, v, u, unc, used, note="": add(n, v, u, FRS, "2026-10-16", "estimate from frames", unc, "estimated", used, note)
P = poly("north_plaza_w1b_2026-10-17.csv"); pL, pW, _ = rect(P)
s("site.plaza.offset", 78, "m", "+-10 m", f"{SF} plazaC = rN + 78", f"measured plaza centroid {-P.centroid.y:.0f} m N of the origin")
s("site.plaza.half_across", 92, "m", "+-20 m", f"{SF} half", f"measured plaza: {pL:.1f} m across (half {pL / 2:.1f} m)")
s("site.plaza.depth", 46, "m", "+-10 m", f"{SF} depth", f"measured plaza: {pW:.1f} m deep")
s("site.planter.r", 7, "m", "+-2 m", f"{SF} planter")
s("site.planter.h", 0.8, "m", "+-0.3 m", f"{SF} planter")
s("site.forecourt.width", 150, "m", "+-20 m", f"{SF} fc")
s("site.pool.offset", 36, "m", "+-8 m", f"{SF} poolC = rN + 36", "measure in a later W1b batch")
s("site.pool.length", 66, "m", "+-10 m", f"{SF} poolL")
s("site.pool.width", 15, "m", "+-4 m", f"{SF} poolW")
s("site.pool.step_h", 0.18, "m", "+-0.03 m", f"{SF} STEP")
s("site.pool.steps", 3, "count", "+-1", f"{SF}")
s("site.pool.water_y", 0.42, "m", "+-0.1 m", f"{SF} waterY")
s("site.jets.rows", 2, "count", "", f"{SF} jets")
s("site.jets.per_row", 30, "count", "+-10", f"{SF} jets")
s("site.jets.row_offset", 3.5, "m", "+-1 m", f"{SF} jets")
s("site.jets.h", 4, "m", "+-2 m", f"{SF} jets")
s("site.jets.arc_count", 13, "count", "+-4", f"{SF} jets")
s("site.jets.arc_h", 8, "m", "+-3 m", f"{SF} jets")
s("site.masts.spacing", 70, "m", "+-20 m", f"{SF} masts")
s("site.masts.inset", 22, "m", "+-10 m", f"{SF} masts", "inside the site boundary")
s("site.masts.h", 26, "m", "+-6 m", f"{SF} poles")
s("site.masts.forecourt_rows", 4, "count per side", "+-1", f"{SF} masts", "at rN + 20 + 38k, 70 m either side")
add("site.people.count", 300, "count", "Visualization", "", "illustrative only", "", "estimated", f"{SF} people", "Visualization, not a crowd model (AGENTS.md rule 7)")

out = ROOT / "gis/parameter_ledger.csv"
with open(out, "w", newline="") as f:
    w = csv.DictWriter(f, COLS, lineterminator="\n"); w.writeheader(); w.writerows(rows)
from collections import Counter
print(out, len(rows), "rows", dict(Counter(r["status"] for r in rows)))
