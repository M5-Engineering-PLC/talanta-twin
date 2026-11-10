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
# Design plan (gis/scripts/fit_design_plan.py): symmetric superellipses fitted to the three W1b rings
DP = json.loads((ROOT / "gis/measurements/normalized/bowl_design_plan_2026-10-17.json").read_text())
for ring, f in DP["rings"].items():
    for k, u, note in (("a_cross", "m", "half width across the pitch"), ("b_long", "m", "half length along the pitch"), ("n", "exponent", "superellipse exponent; 2 = ellipse, higher = squarer")):
        add(f"bowl.plan.{ring}.{k}", f[k], u, f"{f['source']} (W1b trace)", "2026-10-17", DP["method"], f"rms {f['rms_m']} m, max {f['max_m']} m against the trace", "estimated", "blender/build_blockout.py, gis/scripts/export_site_plan.py, export_ground_regions.py", note)
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
add("bowl.profile.shoulder_r", 3, "m", "JWNowpO44rw 12:12, 12:16 (by eye); JWNowpO44rw 07:04", "2026-10-17", "by eye: louvres run up to a thin fascia band, then the edge turns onto the roof within about one fascia height", "+-1.5 m", "estimated", "blender/build_blockout.py profile()", "was 8 m (07:04 silhouette only); the smooth 8 m shoulder read as wall above the louvres")
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
fe("bowl.fin.fascia_h", 1.5, "m", "12:12, 12:16", "by eye: thin white band between the top fin and the roof edge, against the 0.6 m fin pitch", "+-0.5 m", f"{BB} louvre_fins, facade", "fins follow the shoulder up to this line")
fe("bowl.shield.blockout_y1", 51.5, "m", "12:12, 12:16, 12:40", "by eye: shield tip about one fin pitch under the fascia line (roof_top_y - fin.fascia_h)", "+-2 m", f"{BB} shields", "was 45.5 m under the 8 m shoulder; bowl.js uses shield.y0/y1")
fe("bowl.shield.bulge", 1.2, "m", "12:12, 12:16", "by eye: slight convex bulge at the centre", "+-0.6 m", f"{BB} shields")
fe("bowl.spear.span_shields", 1.4, "shield widths", "12:12, 00:16", "by eye: horizontal reach of each crossed spear", "+-0.2", f"{BB} spears")
fe("bowl.spear.blade_len", 6.5, "m", "10:28, 12:12", "by eye: blade length against the shield height", "+-2 m", f"{BB} spears")
fe("bowl.spear.blade_r", 1.2, "m", "10:28", "by eye: blade about 2.4 shaft widths", "+-0.4 m", f"{BB} spears")
fe("bowl.spear.tip_below_fascia", 0.6, "m", "10:28, 12:12", "by eye: blade tips stop just under the roof edge", "+-0.5 m", f"{BB} spears", "never above the roof edge")
fe("bowl.base.step_h", 0.6, "m", "12:16, 12:40", "by eye: light concrete step at the ground edge", "+-0.3 m", f"{BB} plinth", "outline stays the measured W1b plinth")
fe("bowl.base.recess", 4.0, "m", "12:12, 12:16", "by eye: shaded wall set back behind the columns", "+-2 m", f"{BB} base_recess")
fe("bowl.base.band_h", 1.6, "m", "12:12, 12:16", "by eye: light band under the louvres", "+-0.6 m", f"{BB} base_band")
fe("bowl.base.column_w", 1.2, "m", "12:16, 12:40", "by eye: white columns in the recess", "+-0.4 m", f"{BB} base_columns")
fe("bowl.base.column_spacing", 9.0, "m", "12:16, 12:40", "by eye: column rhythm along the base", "+-3 m", f"{BB} base_columns")
fe("bowl.ground.concourse_w", 35, "m", "12:40", "by eye: light paved apron round the base", "+-10 m", "gis/scripts/export_ground_regions.py", "inside the W1b site boundary")
fe("site.ground.murram_rgb", "#8B4A2B-#A0522D", "hex", "11:20, 12:40", "lead review colour range for red murram", "", "blender/build_scene.py terrain_site", "look only")
# Stage 03 bowl interior (blender/build_bowl_detail.py), by eye from named frames; all estimated.
BD = "blender/build_bowl_detail.py"
fe("bowl.seat.green_hex", "#3ca07e", "hex", "00:46, 02:00", "colour pick by eye: mint-green lower tier", "", f"{BD} seats")
fe("bowl.seat.red_hex", "#c4283a", "hex", "02:00, 08:00, 09:12", "colour pick by eye: middle and upper tiers", "", f"{BD} seats")
fe("bowl.seat.dark_hex", "#2b2b2e", "hex", "08:00", "colour pick by eye: dark seats mixed into the upper rows", "", f"{BD} seats")
fe("bowl.seat.mix_lower_red_top", 0.3, "probability", "02:00", "by eye: red seats speckled into the top rows of the green tier", "+-0.15", f"{BD} seats", "rises from 0 at 60% of the rows to this at the top row")
fe("bowl.seat.mix_middle_green", 0.08, "probability", "02:00", "by eye: occasional green seats in the red middle tier", "+-0.05", f"{BD} seats")
fe("bowl.seat.mix_upper_dark_top", 0.6, "probability", "08:00", "by eye: dark seats increase towards the back of the upper tier", "+-0.2", f"{BD} seats", "0.12 at the front row")
fe("bowl.aisle.spacing", 14, "m along the front row", "09:12, 02:00", "by eye: blocks about 28 seats wide", "+-3 m", f"{BD} aisles")
fe("bowl.aisle.width", 1.2, "m", "08:00", "by eye: aisle stair width", "+-0.3 m", f"{BD} aisles")
fe("bowl.tread.colour", "#c9cacb", "hex", "08:00, 09:12", "colour pick by eye: pale grey painted concrete", "", f"{BD} tiers")
add("pitch.markings", "FIFA Laws of the Game, Law 1", "standard", "IFAB Laws of the Game 2025/26", "2026-10-17", "standard dimensions on the estimated 105 x 68 m pitch", "", "estimated", f"{BD} pitch_markings", "centre circle 9.15 m, penalty area 16.5 x 40.32 m, goal area 5.5 x 18.32 m, goal 7.32 x 2.44 m")
fe("pitch.mow_stripes", 20, "count along the length", "00:46, 09:48", "by eye: alternating mowing bands", "+-4", f"{BD} pitch_turf", "look only")
fe("bowl.roofsteel.ribs", 60, "count", "10:38, 10:55", "by eye: radial ribs from the rim to the opening ring (tension cable roof)", "+-12", f"{BD} roof_ribs_under", "matches bowl.roof.trusses")
fe("bowl.roofsteel.cable_sag", 3.0, "m", "10:55", "by eye: tension cable below each rib, with struts", "+-1.5 m", f"{BD} roof_cables")
fe("bowl.roofsteel.member_r", 0.3, "m", "10:04, 10:55", "by eye: rib against the catwalk width and the railing", "+-0.15 m", f"{BD} roof_ribs_under")
fe("bowl.roofsteel.drop", 1.2, "m", "10:04", "by eye: primaries hang below the membrane", "+-0.5 m", f"{BD} roof_ribs_under")
fe("bowl.roofsteel.purlin_rings", 9, "count", "10:04", "by eye: arched purlins between the primaries", "+-3", f"{BD} roof_purlins")
fe("bowl.catwalk.drop", 3.0, "m", "10:04, 09:12", "by eye: catwalk below the membrane near the opening", "+-1 m", f"{BD} catwalk", "floodlights on its inner side")
fe("bowl.catwalk.width", 1.4, "m", "10:04", "by eye: catwalk deck width", "+-0.4 m", f"{BD} catwalk")
fe("bowl.floodlights.spacing", 2.5, "m", "10:04", "by eye: floodlight heads along the catwalk", "+-1 m", f"{BD} floodlights")
fe("bowl.vip.column_spacing", 8, "m", "09:12", "by eye: round white columns in front of the VIP glazing", "+-2 m", f"{BD} vip_columns")
fe("bowl.vip.column_r", 0.45, "m", "09:12", "by eye", "+-0.15 m", f"{BD} vip_columns")
fe("bowl.colonnade.spacing", 8, "m", "08:00, 10:55", "by eye: white columns behind the upper tier", "+-2 m", f"{BD} colonnade")
fe("bowl.tier_upper.y1_blockout", 44.0, "m", "10:55 (Munene's screenshot)", "by eye: the far roof edge sits well above the gallery eye line, so the top of the upper tier is lower than bowl.js 46 m", "+-2 m", "blender/build_blockout.py, build_bowl_detail.py tiers", "overrides bowl.tier_upper.y1 in the Blender build only")
fe("bowl.opening_y_blockout", 50.0, "m", "10:55 (Munene's screenshot), 12:40", "by eye: from the upper gallery the far roof edge and video board show under the near roof, and 12:40 shows a flatter roof than bowl.js", "+-3 m", "blender/build_blockout.py profile()", "overrides bowl.opening_y (47) in the Blender build only")
fe("bowl.back_wall_h_blockout", 44.0, "m", "10:55 (Munene's screenshot)", "follows bowl.tier_upper.y1_blockout", "+-2 m", "blender/build_blockout.py back_wall", "overrides bowl.back_wall_h in the Blender build only")
fe("bowl.gallery.width", 2.2, "m", "10:55 (Munene's screenshot, not in the repository)", "by eye: walkway at the back of the upper tier", "+-0.6 m", f"{BD} gallery_deck")
fe("bowl.gallery.rail_h", 1.1, "m", "10:55 (Munene's screenshot)", "by eye: white railing against a standing person", "+-0.1 m", f"{BD} gallery_rail")
fe("bowl.gallery.post_spacing", 1.5, "m", "10:55 (Munene's screenshot)", "by eye: railing posts", "+-0.5 m", f"{BD} gallery_rail")
fe("bowl.screen.width", 20, "m", "10:38, 10:55", "by eye: about 6% of the 10:55 frame width at about 200 m with a 90 deg lens", "+-5 m", f"{BD} video_boards", "two boards, north and south ends")
fe("bowl.screen.height", 11, "m", "10:38, 10:55", "by eye: aspect about 1.8 in 10:55", "+-3 m", f"{BD} video_boards")
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
# Stage 03 detail sheets (engineering/detail_sheets, with the lead review that overrides them). Finished state:
# treatment from the design model (JWNowpO44rw 04:45, 05:12, 05:16) and the lead renders 06/07 as look references,
# positions from W1b and OSM. Status names the sheet row or the design model (lead review, "How to build").
SB, SS = "blender/build_blockout.py", "gis/scripts/export_site_plan.py; blender/build_site_detail.py"
def fs(n, v, u, sid, src, method, unc, used, note=""):
    add(n, v, u, src, "2026-10-17", method, unc, f"estimated (detail sheet {sid})", used, note)
def fdm(n, v, u, src, method, unc, used, note=""):
    add(n, v, u, src, "2026-10-17", method, unc, "estimated (design model)", used, note)
LR3 = "JWNowpO44rw 07:04 (by eye); lead review correction 3"
fs("ngong.lanes_per_dir", 4, "count", "SR20", LR3, "by eye: three to four lanes each way", "+-1", SS)
fs("ngong.lane_w", 3.3, "m", "SR20", "detail sheet SR20 (3.2-3.5)", "modelling estimate", "+-0.3 m", SS)
fs("ngong.median_w", 2.0, "m", "SR23", LR3, "by eye: narrow central reserve with a barrier", "+-1 m", SS, "sheet SR23 planted median overridden by 07:04")
fs("ngong.barrier_h", 0.8, "m", "SR29", LR3, "by eye: concrete barrier against cars", "+-0.2 m", SS)
fs("ngong.edge_strip_w", 0.5, "m", "SR22", "detail sheet SR22", "modelling estimate", "+-0.3 m", SS)
fs("ngong.kerb_w", 0.3, "m", "SR27", "detail sheet SR27", "modelling estimate", "+-0.1 m", SS)
fs("ngong.kerb_h", 0.18, "m", "SR27", "detail sheet SR27 (0.15-0.25)", "modelling estimate", "+-0.05 m", SS)
fs("ngong.drain_w", 0.4, "m", "SR28", "detail sheet SR28 (0.3-0.5)", "modelling estimate", "+-0.1 m", SS)
fs("ngong.footpath_w", 3.0, "m", "SR19", LR3, "by eye: footpath beside the carriageway", "+-1 m", SS)
fs("ngong.service_w", 4.0, "m", "SR19", LR3, "by eye: earth and grass service strip at the side", "+-2 m", SS)
fs("ngong.dash_len", 3, "m", "SR21", "detail sheet SR21", "modelling estimate", "+-1 m", SS)
fs("ngong.dash_gap", 6, "m", "SR21", "detail sheet SR21", "modelling estimate", "+-2 m", SS)
fs("ngong.line_w", 0.12, "m", "SR22", "detail sheet SR22", "modelling estimate", "+-0.03 m", SS)
DM = "JWNowpO44rw 04:45, 05:12, 05:16 (design model, by eye); lead renders 06, 07 (look)"
fdm("site.avenue.w", 12, "m", DM, "by eye: main palm avenue from the plaza to Ngong Road", "+-4 m", SS)
fs("site.path.radial_w", 5, "m", "SR04", DM, "by eye (sheet 4-6 m)", "+-1 m", SS)
fs("site.path.ring_w", 4, "m", "SR05", DM, "by eye (sheet 3-5 m)", "+-1 m", SS)
fdm("site.path.ring_offset", 80, "m", DM, "by eye: curved walk round the bowl, from the plinth", "+-20 m", SS)
fs("site.bed.w", 2.0, "m", "SR08", DM, "by eye: red flower beds beside the paths (sheet 1-2 m)", "+-1 m", SS)
fs("site.bed.flower_rgb", "#B3262E", "hex", "SR08", DM, "by eye: red flower beds in the design model", "", SS)
fs("site.apron.depth", 15, "m", "SR06", "detail sheet SR06 (at least 15 m by eye); 9I1korKNjig 01:10", "by eye", "+-5 m", SS)
fs("site.paving.edge_w", 0.3, "m", "SR03", "detail sheet SR03", "modelling estimate", "+-0.1 m", SS)
fs("site.paving.joint", 1.5, "m", "SR02", "detail sheet SR02 (1-2 m)", "modelling estimate", "+-0.5 m", "blender/build_site_detail.py")
fs("site.paving.rgb", "#B9B3A5", "hex", "SR02", "detail sheet SR02; render 06 paler", "by eye", "", "blender/build_site_detail.py")
fs("site.palm.spacing", 8, "m", "SR38", "detail sheet SR38; lead review correction 2", "by eye (sheet 6-10 m)", "+-2 m", SS)
fs("site.palm.h", 7, "m", "SR38", "detail sheet SR38; lead review correction 2", "by eye (sheet 5-8 m)", "+-2 m", "blender/build_site_detail.py")
fs("site.tree.spacing", 11, "m", "SR39", DM, "by eye (sheet 8-15 m), in clumps", "+-4 m", SS)
fs("site.pathlight.spacing", 14, "m", "SR17", DM, "by eye (sheet 10-15 m)", "+-4 m", SS)
fs("site.pathlight.h", 5, "m", "SR17", DM, "by eye (sheet 4-6 m)", "+-1 m", "blender/build_site_detail.py")
fs("site.bollard.spacing", 3, "m", "SR18", "detail sheet SR18 (2-4 m)", "modelling estimate", "+-1 m", SS)
fs("site.bollard.h", 0.9, "m", "SR18", "detail sheet SR18 (0.8-1.0 m)", "modelling estimate", "+-0.1 m", "blender/build_site_detail.py")
fs("site.fence.gap", 14, "m", "SR34", "detail sheet SR34, SR35", "gaps only where OSM roads and the avenues cross the boundary", "", SS, "no access features (AGENTS.md rule 8)")
fs("site.fence.h", 2.4, "m", "SR35", "detail sheet SR34, SR35 (2-3 m)", "modelling estimate", "+-0.5 m", "blender/build_site_detail.py")
fs("site.parking.bay_w", 2.5, "m", "SR33", "detail sheet SR33", "modelling estimate", "+-0.2 m", SS)
fs("site.parking.bay_d", 5.0, "m", "SR33", "detail sheet SR33", "modelling estimate", "+-0.5 m", SS)
fs("site.flag.w", 2.0, "m", "SR16", "detail sheet SR16", "by eye; plain unlettered flags", "+-0.5 m", "blender/build_site_detail.py")
fs("site.flag.h", 1.0, "m", "SR16", "detail sheet SR16", "by eye", "+-0.3 m", "blender/build_site_detail.py")
fs("site.canopy.w", 18, "m", "SR48", "detail sheet SR48, SR51", "generic canopy, no layout detail", "+-6 m", "blender/build_site_detail.py")
fs("site.canopy.d", 7, "m", "SR48", "detail sheet SR48, SR51", "generic canopy", "+-3 m", "blender/build_site_detail.py")
fs("site.canopy.h", 4.5, "m", "SR48", "detail sheet SR48 (3-5 m), SR51 (4-6 m)", "generic canopy", "+-1 m", "blender/build_site_detail.py")
fs("site.sign.w", 10, "m", "SR50", "detail sheet SR50; lead review correction 3 (billboards blank)", "by eye from 07:04", "+-4 m", "blender/build_site_detail.py")
fs("site.sign.h", 5, "m", "SR50", "detail sheet SR50 (3-5 m)", "modelling estimate", "+-2 m", "blender/build_site_detail.py")
fs("site.sign.post_h", 6, "m", "SR50", "JWNowpO44rw 07:04 (by eye)", "by eye: raised roadside frames", "+-2 m", "blender/build_site_detail.py")
fs("site.track.lanes", 6, "count", "SR43", "detail sheet SR43 (render 07)", "by eye", "+-2", "blender/build_site_detail.py")
fs("site.track.lane_w", 1.22, "m", "SR43", "detail sheet SR43; World Athletics lane width", "standard", "+-0.02 m", "blender/build_site_detail.py")
fdm("site.track.mast_h", 20, "m", DM + "; detail sheet SR42", "by eye: floodlight masts round the training tracks", "+-6 m", "blender/build_site_detail.py")
fdm("site.track_sw.surface", "track with grass infield", "", DM, "finished state: the design model shows two tracks with grass infields (lead correction 1)", "", "blender/build_site_detail.py", "sheet SR46/SR47 earthworks are the construction state")
add("site.roof_palette", "#8E3B2A,#A0522D,#6B4A3A,#7C7F82", "hex", "JWNowpO44rw 07:04 (by eye)", "2026-10-17", "tile and iron-sheet roof colours", "", "estimated", "blender/build_site_detail.py", "Stage 03 checklist: suburbs (not in a detail sheet)")
fs("bowl.shield.rim", 0.3, "m", "RF13", "JWNowpO44rw 12:12 (by eye); detail sheet RF13", "by eye: thin pale edge strip", "+-0.15 m", SB)
fs("bowl.opening.trim_h", 1.2, "m", "RF26", "JWNowpO44rw 00:16, 10:04 (by eye); detail sheet RF26", "by eye: dark border round the opening", "+-0.5 m", "blender/build_site_detail.py")
fs("bowl.night.fascia_spacing", 3.0, "m", "RF25", "JWNowpO44rw 11:48 (by eye); detail sheet RF25", "Visualization of the night effect", "+-1 m", "blender/build_site_detail.py")
fs("bowl.night.ring_spacing", 2.0, "m", "RF31", "JWNowpO44rw 11:48 (by eye); detail sheet RF31", "Visualization of the night effect", "+-1 m", "blender/build_site_detail.py")
fs("bowl.night.wash_spacing", 18, "m", "RF38", "JWNowpO44rw 20:05, 11:48 (by eye); detail sheet RF38", "Visualization of the night effect", "+-6 m", "blender/build_site_detail.py")
# group 2, sheet BS (bowl interior)
BDS = "blender/build_bowl_detail.py"
F200 = "JWNowpO44rw 02:00 (by eye); lead review correction 4"
fs("bowl.speaker.count", 16, "count", "BS30", F200, "by eye: three clusters across about a sixth of the bowl", "+-6", BDS)
fs("bowl.speaker.elements", 8, "count", "BS30", F200, "by eye: boxes in one J array", "+-3", BDS)
fs("bowl.speaker.el_w", 1.4, "m", "BS30", F200, "by eye against the roof steel", "+-0.4 m", BDS)
fs("bowl.speaker.el_h", 0.55, "m", "BS30", F200, "by eye", "+-0.2 m", BDS)
fs("bowl.speaker.el_d", 0.8, "m", "BS30", F200, "by eye", "+-0.3 m", BDS)
fs("bowl.speaker.drop", 4.5, "m", "BS30", F200, "by eye: frame hung on chains below the roof steel", "+-2 m", BDS)
fs("bowl.speaker.t_over_tier", 0.12, "fraction", "BS30", F200, "by eye: above the front of the upper tier", "+-0.1", BDS)
fs("bowl.vip.glow_day", 0.03, "W/m2 (emission)", "BS18", "JWNowpO44rw 02:00; cyNgbyZv6BM 10:02 (by eye)", "look value: warm light behind the glazing; 0.6 and 0.15 read as a beige band in C13 and C18; the frames show dark glass by day", "", BDS)
fs("bowl.vip.glow_night", 4.0, "W/m2 (emission)", "BS18", "detail sheet BS18", "look value, Visualization", "", BDS)
fs("bowl.vip.mullion_spacing", 4.0, "m", "BS19", "detail sheet BS19 (box fronts not clear)", "modelling estimate", "+-2 m", BDS)
fs("bowl.apron.width", 3.0, "m", "BS41", "JWNowpO44rw 05:56; KEOmkVfjhu8 02:48 (by eye)", "by eye: pale strip before the lowest rows", "+-1.5 m", BDS)
fs("bowl.corner_flag.h", 1.5, "m", "BS40", "Laws of the Game, Law 1 (minimum)", "standard", "", BDS)
fs("bowl.dugout.length", 12, "m", "BS44", "detail sheet BS44 (render only)", "generic estimate", "+-4 m", BDS)
fs("bowl.dugout.depth", 2.5, "m", "BS44", "detail sheet BS44 (render only)", "generic estimate", "+-1 m", BDS)
fs("bowl.dugout.h", 2.3, "m", "BS44", "detail sheet BS44 (render only)", "generic estimate", "+-0.5 m", BDS)
fs("bowl.dugout.offset_halfway", 4, "m", "BS44", "detail sheet BS44 (render only)", "generic estimate", "+-3 m", BDS)
fs("bowl.dugout.from_touchline", 4, "m", "BS44", "detail sheet BS44 (render only)", "generic estimate", "+-2 m", BDS)
add("site.people.count", 300, "count", "Visualization", "", "illustrative only", "", "estimated", f"{SF} people", "Visualization, not a crowd model (AGENTS.md rule 7)")

# ---- side profile fitted to the drone frames (gis/scripts/profile_fit/fit2.py, cloud session 2026-10-18).
# Geometry pass 2 (fit2.py with the opening ring inset dRi and three opening landmarks). Accepted rows: the larger of
# two spreads is under 2 m: leave-one-frame-out (max - min over 8 runs) and the spread across the three multistart
# basins (costs within 4 % of each other). Values are the median over the basins. 001232.600 is left out: its camera
# could not be matched (junction error 150-180 px in every start). Rejected fits are kept as *.fit_* rows (not read).
PF = "JWNowpO44rw 000641.633, 000659.633, 001221.500, 001224.500, 001235.934, 001239.267, 001244.833, 001247.833"
PFU = "blender/build_blockout.py profile()"
PFM = "least squares on silhouette, roof opening ring (with inset), opening landmarks, junction, foot and labelled shields; one focal length and k1 per lens; 3-start multistart and leave-one-out"
def pf(n, v, u, spread, method, note="", used=PFU):
    add(n, v, u, PF, "2026-10-18", method, f"+-{spread / 2:.1f} m", f"derived (8 frames, spread {spread:.1f} m)", used, note)
def pfr(n, v, u, spread, method, note="not read by the build; the earlier estimate stays"):
    add(n, v, u, PF, "2026-10-18", method, f"spread {spread:.1f} m", f"estimated (frame fit, spread {spread:.1f} m, not accepted)", "", note)
pf("bowl.profile.foot_inset", 0.66, "m", 0.94, PFM, "wall foot inside the roof outer ring; pass 1 gave 0.74")
pf("bowl.profile.wall_bulge", -3.09, "m", 0.43, PFM, "negative: the wall bows inward at mid height; pass 1 gave -2.89")
pf("bowl.shield.centre_y", 27.92, "m", 0.70, PFM, "shield moved whole to this centre, height kept; pass 1 spread 4.9 m", "blender/build_blockout.py shields")
add("bowl.profile.roof_sag", -2.74, "m", PF, "2026-10-18", "geometry pass 1: least squares on silhouette, roof opening, junction, foot and labelled shields; one focal length and k1 per lens", "+-0.8 m", "withdrawn (pass 2, LOO spread 6.2 m)", "", "accepted in pass 1 (leave-one-out spread 1.6 m); kept as evidence, not read by the build (VO skips withdrawn rows)")
pfr("bowl.profile.fit_roof_sag", -2.66, "m", 6.19, PFM, "was accepted in pass 1 (-2.74, spread 1.6 m); pass 2 leave-one-out without 001239.267 jumps to +5.95 and one basin gives -0.24, so bowl.roof_sag (1.5 m, estimated) is read again")
pfr("bowl.profile.fit_wall_top_y", 47.01, "m", 4.84, PFM)
pfr("bowl.profile.fit_shoulder_rh", 10.18, "m", 5.37, PFM)
pfr("bowl.profile.fit_shoulder_rv", 4.23, "m", 5.34, PFM)
pfr("bowl.profile.fit_opening_y", 50.22, "m", 2.57, PFM)
pfr("bowl.profile.fit_opening_inset", 2.77, "m", 3.64, PFM, "roof opening ring inset from blender/out/bowl_rings.json rRi; not read, the ring stays")
pfr("bowl.profile.fit_crest_y", 48.19, "m", 4.84, PFM)
# Geometry pass 3 (last height-fit run): pass 2 objective plus a Gaussian crest prior ((yW + Rv - 54) / 2)^2 with the
# image residuals in units of the 10 px robust scale; same 8 frames, lenses and 3 starts. The rule (fit2.acceptance)
# failed for every parameter, so the build keeps its values. Evidence rows only, not read by the build.
add("bowl.profile.crest_prior", 54, "m", "JWNowpO44rw transcript 10:27 (\"the roof structure rises to roughly 54 m\"); press (max about 56 m); engineering/detail_sheets/06_interior_inventory.md", "2026-10-18", "narration and press", "+-2 m (sd of the prior)", "estimated (narration)", "gis/scripts/profile_fit/fit2.py CREST_PRIOR", "prior for geometry pass 3 only")
PF3 = "geometry pass 3: " + PFM + "; Gaussian crest prior 54 +- 2 m"
add("bowl.profile.fit3_wall_top_y", 45.19, "m", PF, "2026-10-18", PF3, "spread 5.6 m", "estimated (prior-constrained fit, spread 5.6 m, not accepted)", "", "not read by the build; basin spread 0.3 m, leave-one-out 5.6 m")
add("bowl.profile.fit3_shoulder_rh", 14.14, "m", PF, "2026-10-18", PF3, "spread 23.5 m", "estimated (prior-constrained fit, spread 23.5 m, not accepted)", "", "not read by the build; basin spread 23.5 m, leave-one-out 1.3 m")
add("bowl.profile.fit3_shoulder_rv", 1.80, "m", PF, "2026-10-18", PF3, "spread 3.1 m", "estimated (prior-constrained fit, spread 3.1 m, not accepted)", "", "not read by the build; basin spread 0.1 m, leave-one-out 3.1 m")
add("bowl.profile.fit3_opening_y", 47.91, "m", PF, "2026-10-18", PF3, "spread 4.7 m", "estimated (prior-constrained fit, spread 4.7 m, not accepted)", "", "not read by the build; basin spread 1.2 m, leave-one-out 4.7 m")
add("bowl.profile.fit3_roof_sag", 0.75, "m", PF, "2026-10-18", PF3, "spread 6.0 m", "estimated (prior-constrained fit, spread 6.0 m, not accepted)", "", "not read by the build; basin spread 1.8 m, leave-one-out 6.0 m")
add("bowl.profile.fit3_foot_inset", 0.31, "m", PF, "2026-10-18", PF3, "spread 3.4 m", "estimated (prior-constrained fit, spread 3.4 m, not accepted)", "", "not read by the build; basin spread 0.1 m, leave-one-out 3.4 m")
add("bowl.profile.fit3_wall_bulge", -4.00, "m", PF, "2026-10-18", PF3, "spread 0.0 m", "estimated (prior-constrained fit, spread 0.0 m, not accepted)", "", "not read by the build; held at its bound (-4 m) in every run")
add("bowl.profile.fit3_shield_centre_y", 24.81, "m", PF, "2026-10-18", PF3, "spread 3.7 m", "estimated (prior-constrained fit, spread 3.7 m, not accepted)", "", "not read by the build; basin spread 0.4 m, leave-one-out 3.7 m")
add("bowl.profile.fit3_opening_inset", 6.50, "m", PF, "2026-10-18", PF3, "spread 2.4 m", "estimated (prior-constrained fit, spread 2.4 m, not accepted)", "", "not read by the build; basin spread 0.0 m, leave-one-out 2.4 m")
add("bowl.profile.fit3_crest_y", 46.99, "m", PF, "2026-10-18", PF3, "spread 2.7 m", "estimated (prior-constrained fit, spread 2.7 m, not accepted)", "", "not read by the build; basin spread 0.2 m, leave-one-out 2.7 m")
add("bowl.roof.cushion_bays", 30, "count", "JWNowpO44rw 001221.500, 001224.500", "2026-10-18", "topside rib seams against projected rib lines (30, 40, 60) with the solved cameras; both frames match 30", "+-2", "derived (2 frames)", "blender/build_blockout.py roof, roof_ribs", "the 60 underside primaries (bowl.roofsteel.ribs) carry a top rib on every other one")
add("bowl.roof.cushion_rows", 8, "count", "JWNowpO44rw 001232.600, 001235.934", "2026-10-18", "by eye: cushion rows from the rim to the opening in the front bays", "+-1", "estimated (frames 001232.600, 001235.934)", "blender/build_blockout.py roof")
add("bowl.roof.cushion_bulge", 0.45, "m", "JWNowpO44rw 001232.600, 001235.934", "2026-10-18", "by eye: highlight and shadow per cushion", "+-0.2 m", "estimated (frames 001232.600, 001235.934)", "blender/build_blockout.py roof")

# Geometry pass 4 (2026-10-19, convex locked by Munene): gis/scripts/profile_fit/fit4_convex.py top. Wall bulge >= 0;
# crest kept at roof_top_y 54 m (yW = 54 - Rv); other profile values at the build values; free: bulge, Rh, Rv. Frames:
# the 8 of passes 2 and 3 plus 3 edge-on frames with hand-read limbs (lines_edge.json). Rule as before (fit2.acceptance).
# The _blockout rows override the build; the earlier rows above stay as they were.
PF4 = PF + ", 001212.500, 001227.500, 001230.050 (edge-on)"
PF4M = "geometry pass 4: least squares on silhouette (edge-on frames: hand-read limb), opening, junction, foot and labelled shields; one focal length and k1 per lens; bulge >= 0, crest 54 m; 3-start multistart and leave-one-out (11 drops)"
add("bowl.profile.wall_bulge_blockout", 2.02, "m", PF4, "2026-10-19", PF4M, "+-0.5 m", "derived (11 frames, spread 1.0 m; convex locked by Munene)", "blender/build_blockout.py profile()", "positive: the wall bulges outward at mid height; replaces -3.09 (pass 2) in the build")
add("bowl.profile.shoulder_rv_blockout", 4.74, "m", PF4, "2026-10-19", PF4M, "+-0.9 m", "derived (11 frames, spread 1.9 m; convex locked by Munene)", "blender/build_blockout.py profile()", "vertical radius of the rolled shoulder")
add("bowl.profile.wall_top_y_blockout", 49.26, "m", PF4, "2026-10-19", "roof_top_y 54 minus shoulder_rv 4.74", "+-0.9 m", "derived (from roof_top_y and shoulder_rv)", "blender/build_blockout.py profile()", "keeps the crest at 54 m")
add("bowl.profile.shoulder_rh_blockout", 8.5, "m", "JWNowpO44rw 001227.500, 001230.050 (edge-on limbs); landing mockups 06 and 07 (look only)", "2026-10-19", "by eye: the rolled edge from the louvres into the roof; the pass 4 fit gave 8.49 m but failed the rule (leave-one-out spread 2.75 m)", "+-3 m", "estimated (by eye, convex locked by Munene)", "blender/build_blockout.py profile()", "horizontal radius of the rolled shoulder")
add("bowl.profile.bulge_anchor_blockout", "top", "", PF4, "2026-10-19", "pass 4 run with both anchors; top (wall top on the W1b roof outer ring) had the lower image cost (476,926 against 492,995 for widest)", "", "derived (pass 4 comparison)", "blender/build_blockout.py ANCHOR", "widest would put the barrel's widest ring on the W1b ring")
add("bowl.profile.fit4_shoulder_rh", 8.49, "m", PF4, "2026-10-19", PF4M, "spread 2.8 m", "estimated (frame fit, spread 2.8 m, not accepted)", "", "not read by the build; basin spread 1.5 m, leave-one-out 2.75 m (without 001239.267: 12.0 m)")
add("bowl.roof.cushion_bulge_blockout", 1.2, "m", "JWNowpO44rw 001232.600, 001235.934, 001033.567", "2026-10-19", "by eye: deep inflated cushions, rise about a fifth of the cushion width; the 0.45 m row read too flat against the frames and mockup 06", "+-0.4 m", "estimated (by eye, frames 001232.600, 001235.934, 001033.567)", "blender/build_blockout.py roof", "replaces 0.45 in the build")
add("bowl.roof.cushion_pillow_blockout", 0.6, "exponent", "JWNowpO44rw 001033.567, 001232.600", "2026-10-19", "by eye: flat-topped pillows with steep seams; bulge * (sin pi u sin pi v)^0.6", "+-0.2", "estimated (by eye)", "blender/build_blockout.py roof", "")


# ---- interior pass (detail sheet 05_interior_tour.md, IT01-IT13; cloud session 2026-10-18). Sheet 05 wins over 02 (BS).
IT = "blender/build_bowl_detail.py F. interior tour"
def itr(n, v, u, frames, method, unc, status=None, note=""):
    add(n, v, u, "JWNowpO44rw " + frames, "2026-10-18", method, unc, status or f"estimated (frames {frames})", IT, note)
itr("bowl.seat.lower_tones", "#3EA98A;#5CBF9F;#2F8F74", "hex", "000945.200, 002144.300", "by eye with k-means of the seat colours, saturated for haze: mint turquoise", "", note="IT01, IT05")
itr("bowl.seat.lower_tone_weights", "0.5;0.3;0.2", "share", "000945.200", "by eye", "+-0.1")
itr("bowl.seat.middle_tones", "#C4283A;#D95C68;#E58A98", "hex", "000945.200, 002144.300", "by eye with k-means: red, salmon, pink mosaic", "", note="IT02; green flecks kept (bowl.seat.mix_middle_green), denser in the lower rows")
itr("bowl.seat.middle_tone_weights", "0.5;0.3;0.2", "share", "000945.200", "by eye", "+-0.1")
itr("bowl.seat.upper_tones", "#7A1F2C;#A8283A;#C98A92", "hex", "000945.200, 002320.200", "by eye with k-means: maroon and red with lighter seats", "", note="IT03")
itr("bowl.seat.upper_tone_weights", "0.4;0.4;0.2", "share", "000945.200", "by eye", "+-0.1")
# ---- interior pass 2 (detail sheet 06_interior_inventory.md, IF rows win over 05; cloud session 2026-10-18)
# Row counts: vertical luminance profile through the centre of one full block per tier, square on, row period from
# the FFT peak, rows = block height / period (000945.200: lower 50 px / 3.16 px, middle 40 px / 3.73 px;
# 000735.433: lower 38 px / 2.2-2.5 px, middle 28 px / 2.5 px). The upper tier is cut by the frame edge (000945.200)
# and by the concourse ceiling (000735.433) in both, so it keeps its estimate.
IF6 = "blender/build_bowl_detail.py F2. interior inventory"
def ifr(n, v, u, src, method, unc, status="estimated", note=""):
    add(n, v, u, src, "2026-10-18", method, unc, status, IF6, note)
# Tier-section pass (2026-10-18): hand counts at native resolution, one full block per tier, square on
# (gis/scripts/tier_section/rows.json). Two overlapping frames within +-1 mark a count derived. The pass 2 FFT counts
# stay as estimated evidence rows. The two-view tread/riser fit (tier_fit.py) was rejected (README in
# blender/renders/tier_section_01/), so the tier extents (t0, t1, y0, y1) keep their estimates.
TS = "gis/scripts/tier_section/rows.json"
itr("bowl.tier_lower.rows_fft_pass2", 16, "count", "000945.200, 000735.433", "pass 2: row period by FFT of a vertical profile", "+-1", "estimated (FFT, superseded by the hand count)", "not read by the build")
itr("bowl.tier_middle.rows_fft_pass2", 11, "count", "000945.200, 000735.433", "pass 2: row period by FFT of a vertical profile", "+-1", "estimated (FFT, superseded by the hand count)", "not read by the build")
itr("bowl.tier_lower.rows_blockout", 15, "count", "000745.000, 000747.000 (and 000945.200)", "hand count at native resolution, one full block square on: 14-15, 15-16 (000945.200: 15); 002500-002506 are too blurred to count", "+-1", "derived (2 frames)", "overrides bowl.tier_lower.rows (24); " + TS)
itr("bowl.tier_middle.rows_blockout", 12, "count", "000745.000, 000747.000 (and 002348.000)", "hand count at native resolution, one full block square on: 11-12, 12-13 (002348.000: 12-14)", "+-1", "derived (2 frames)", "overrides bowl.tier_middle.rows (13); " + TS)
itr("bowl.tier_upper.rows_blockout", 32, "count", "000745.000, 000747.000 (and 002348.000)", "hand count at native resolution, one full block square on: 32, 32 (002348.000, other stand: 29-31)", "+-1", "derived (2 frames)", "overrides bowl.tier_upper.rows (21); " + TS)
itr("bowl.portals.upper_per_aisle", 1, "count", "000945.200, 002320.200", "one portal at the foot of every upper-tier aisle", "+-0", note="IT03 generic openings; no signage")
itr("bowl.portals.middle_every", 2, "aisles", "000945.200, 002144.300", "dark openings at the top of the middle tier at every other aisle", "+-1")
itr("bowl.portals.width", 2.4, "m", "000945.200", "by eye against the aisle width", "+-0.5 m")
itr("bowl.portals.height", 2.4, "m", "000945.200", "by eye against the row height", "+-0.5 m")
itr("bowl.portals.panel_hex", "#8C97A6", "hex", "000945.200", "by eye: pale blue-grey panel; text not copied", "")
itr("bowl.boxband.bays_per_aisle", 2, "count", "000945.200", "two glazed bays per upper-tier aisle block", "+-1", note="IT04")
itr("bowl.concourse.floor_hex", "#8A8C8E", "hex", "002144.300", "by eye: grey concrete floor", "", note="IT13")
itr("bowl.concourse.back_hex", "#3A3D40", "hex", "002144.300", "by eye: dark back of the concourse", "", note="IT13")
itr("bowl.concourse.depth", 10.0, "m", "002144.300, 000735.433", "by eye: open floor from the top row of the lower tier back to the column row under the middle tier", "+-3 m", note="IT13")
itr("bowl.band.vip_glass_y0_blockout", 12.8, "m", "002144.300", "the concourse floor runs onto the top row: a low kerb, not a 2 m wall", "+-0.3 m", note="IT13; overrides bowl.band.vip_glass_y0 (14.5) in the Blender build")
itr("bowl.balustrade.h", 1.1, "m", "002320.200", "by eye against the standing figure", "+-0.2 m", note="IT08")
itr("bowl.led_ribbon.h", 0.9, "m", "001940.267", "by eye", "+-0.3 m", note="IT07, matchday only")
itr("bowl.led_ribbon.strength", 2.5, "W/m2 (emission)", "001940.267", "look value", "", note="Visualization")
itr("bowl.floodlights.per_bay", 4, "count", "000154.067", "LED heads between neighbouring primary trusses on the catwalk", "+-1", note="IT11")
F06 = "engineering/detail_sheets/06_interior_features.csv"
ifr("bowl.vip.side", "west", "side", "JWNowpO44rw transcript 5:01, 22:47-24:30; " + F06 + " IF08", "VIP parking on the west side; VIP rows at the lounge level", "")
ifr("bowl.vip.arc", 48, "m along the lower tier back row", "JWNowpO44rw 002400.000, 002402.700; IF40", "by eye: the lounge glazing runs about three aisle blocks", "+-15 m")
ifr("bowl.vip.rows", 4, "count", "JWNowpO44rw 002421.000, 002433.000; IF08", "the top rows of the lower tier in front of the lounge glazing (3 to 4)", "+-1")
ifr("bowl.vip.seat_pitch", 0.75, "m", "JWNowpO44rw 002427.667, 002433.000; IF07", "by eye: wider upholstered chairs with armrests and cup holders", "+-0.1 m", note="VIP seats only; bowl.seat_pitch is unchanged")
ifr("bowl.vip.seat_hex", "#B3202E", "hex", "JWNowpO44rw 002433.000; IF07", "by eye: red upholstery", "")
ifr("bowl.vip.balustrade_h", 1.1, "m", "JWNowpO44rw 002421.000, 002433.000; IF08", "by eye: glass with a steel top rail at the front of the VIP rows", "+-0.2 m")
ifr("bowl.media.side", "east", "side", "JWNowpO44rw 000748.500, 000752.867; IF30", "side not confirmed in the video; east until a frame proves otherwise (sheet 06)", "", "estimated (placeholder side)")
ifr("bowl.media.arc", 40, "m along the upper tier front", "JWNowpO44rw 000748.500, 000752.867; IF30", "by eye: a block of plain red seats", "+-15 m", "estimated (placeholder side)")
ifr("bowl.media.rows", 8, "count", "JWNowpO44rw 000752.867; IF30", "by eye: plain red rows on the steep upper tier", "+-3", "estimated (placeholder side)", "no desks (lead: not seen)")
ifr("bowl.media.seat_hex", "#A8283A", "hex", "JWNowpO44rw 000752.867", "by eye: plain red, no mosaic", "")
ifr("bowl.media.office_bays", 2, "box-band bays", "JWNowpO44rw 000833.400; IF34", "placeholder: the media offices take the box-band bays behind and below the media block", "+-2", "estimated (placeholder side)", "54 bays - 2 = 52 sky boxes (transcript 23:55)")
ifr("bowl.skybox.count", 52, "count", "JWNowpO44rw transcript 23:55", "narrated", "+-0", "measured (narration)")
ifr("bowl.skybox.places_each", 12, "places", "06_interior_inventory.md seat section", "sheet 06: about 10 to 20 places per box", "10-20")
ifr("bowl.tunnel.side", "west", "side", "JWNowpO44rw 002503.000, 002506.000; IF71", "placeholder: the side is not confirmed; west with the VIP stand", "", "estimated (placeholder side)")
ifr("bowl.tunnel.width", 8.0, "m", "JWNowpO44rw 002503.000, 002506.000; IF44, IF71", "by eye: a wide dark opening about three seat blocks of rows high", "+-2 m")
ifr("bowl.tunnel.height", 3.2, "m", "JWNowpO44rw 002503.000, 002506.000", "by eye against the standing figures", "+-0.6 m")
ifr("bowl.dugout.from_touchline_blockout", 2.5, "m", "IF45; blender/out/bowl_rings.json", "the west tier front is about 5.3 m behind the touchline, so the 2.5 m deep shelter starts 2.5 m out", "+-1 m", note="overrides bowl.dugout.from_touchline (4, BS44)")
ifr("bowl.aisle_sign.plate_hex", "#2D5DA8", "hex", "JWNowpO44rw 000735.433, 000752.867; IF73", "by eye: plain blue plates on white aisle-head bands; no text", "")
ifr("bowl.tier_front_band.hex", "#2A2C2E", "hex", "JWNowpO44rw 000912.000, 000945.200; IF17", "by eye: dark fascia bands between tiers", "")
ifr("bowl.led_ribbon.colours", "#2AA8F0;#2BE07A", "hex (middle front; upper front)", "JWNowpO44rw 002503.000, 002506.000; IF18", "by eye: blue under the middle tier, green under the upper tier", "", note="Visualization, matchday only")
ifr("bowl.hung_screens.count", 8, "count", "JWNowpO44rw 000155.000, 000158.000, 001003.000, 001006.000; IF20", "by eye: small dark panels hung from the trusses at intervals", "+-4")
ifr("bowl.hung_screens.size", "4.0;2.4", "m (w;h)", "JWNowpO44rw 000155.000", "by eye", "+-1 m")
ifr("bowl.hung_screens.drop", 4.0, "m below the primaries", "JWNowpO44rw 000155.000, 001003.000; IF25", "by eye: on visible hanging cables", "+-2 m")

# Rows added to the CSV by hand between 2026-10-20 and 2026-10-23 (facade spec and fix, replica passes A and B,
# pass F (withdrawn later), the pass I corrections and pass J landmarks), copied here so the generator writes the
# committed ledger again (web hero v2 order W0.1). Values are kept as the strings in the CSV.
add('bowl.profile.lattice_members_704', '24', 'count per direction', 'JWNowpO44rw 000714.767, 001221.500, 001216.000', '2026-10-20', 'shields sit on every third top V point (3 bays between shields on the long side); 8 shields x 3', '+-2', 'derived', 'blender/build_blockout.py lattice', 'supersedes 20; assumes the end bays follow the same 3-bay rhythm')
add('bowl.fin.pitch', '0.65', 'm', 'JWNowpO44rw 001216.000, 001221.500 (pixel profiles, lead)', '2026-10-20', 'louvre pitch 12.5 px against the bay width 625 px in 001216.000; bay = facade perimeter 780.4 m / 24', '+-0.08 m', 'derived', 'blender/build_blockout.py louvre_fins', 'agrees with the 0.6 m estimate')
add('bowl.lattice.section_w', '0.45', 'm', 'JWNowpO44rw 001216.000, 001221.500 (pixel profiles, lead)', '2026-10-20', 'rib face width 8.7 px across the rib (FWHM) = 0.70 louvre pitch in 001216.000; 001221.500 gives 1.0 pitch at lower resolution', '+-0.15 m', 'derived', 'blender/build_blockout.py lattice', 'slim flat rib, flat face out, square edges; supersedes 1.5')
add('bowl.lattice.section_d', '0.25', 'm', 'JWNowpO44rw 001216.000, 001221.500 (by eye)', '2026-10-20', 'by eye: rib almost flush with the louvre faces; thin shadow line only', '+-0.15 m', 'estimated', 'blender/build_blockout.py lattice', 'supersedes 0.8')
add('bowl.spear.radius', '0.37', 'm', 'JWNowpO44rw 001216.000, 001221.500 (pixel profiles, lead)', '2026-10-20', 'shaft width 14.4 px across the shaft = 1.15 louvre pitch in 001216.000', '+-0.1 m', 'derived', 'bowl.js spears; blender/build_blockout.py spears', 'supersedes 0.5')
add('bowl.shield.red', '#ad2750', 'sRGB', 'JWNowpO44rw 001216.000 (sun), 001232.600 (shade), 000714.767 (overcast)', '2026-10-20', 'median pixel of the red field; value from the sunlit sample, scaled by the white stripe (225) to a 0.80 white albedo; hue between the sun and shade samples', 'hue +-8 deg, value +-15 %', 'derived', 'blender/build_blockout.py shield_png', 'crimson, matte; the maroon look in 000714.767 and 001232.600 is overcast and shade, not the paint')
add('bowl.shield.black', '#1c1e22', 'sRGB', 'JWNowpO44rw 001216.000 (sun)', '2026-10-20', 'median pixel of the black lobe in sun', '+-10 %', 'derived', 'blender/build_blockout.py shield_png', 'near black, matte')
add('bowl.shield.roughness', '0.6', '1', 'JWNowpO44rw 001216.000, 001221.500 (by eye)', '2026-10-20', 'by eye: no specular highlight on the sunlit shield face; no metal rim visible', '+-0.15', 'estimated', 'shield material', 'metallic 0; no chrome or bright rim')
add('bowl.base.ring_beam_h', '2.0', 'm', 'JWNowpO44rw 001216.000, 001221.500 (by eye)', '2026-10-20', 'by eye: white ring beam under the lowest louvre, about 3 louvre pitches', '+-0.5 m', 'estimated', 'blender/build_blockout.py base band', 'bottom of the lattice; the bottom points of the ribs sit on it')
add('bowl.base.recess', 'dark recessed ground floor with white piers', 'description', 'JWNowpO44rw 001216.000, 001221.500, 000714.767 (by eye)', '2026-10-20', 'by eye: under the ring beam the ground floor is set back and in shadow; white piers about one per bay, positions estimated', 'piers +-1 bay', 'estimated', 'blender/build_blockout.py base band', 'not a continuous white colonnade; no gates, exits or signs in public output')
add('bowl.base.recess_depth', '4.0', 'm', 'JWNowpO44rw 12:12, 12:16 (by eye)', '2026-10-20', 'numeric depth carried from the 2026-10-17 bowl.base.recess row, whose last row is now a description', '+-2 m', 'estimated', 'blender/build_blockout.py base_recess', 'set back from the plinth face; added because bowl.base.recess is no longer a number')
add('bowl.fin.fascia_h', '2.5', 'm', 'JWNowpO44rw 001216.000 (pixel profile, lead)', '2026-10-20', 'white band from the top V points to the roof edge, about 4 louvre pitches at 0.65 m', '+-0.7 m', 'derived', 'blender/build_blockout.py louvre_fins', 'supersedes 1.5; broad white band, not a thin rim (facade_fix_01 review)')
add('bowl.shield.outline_a', '1.85', 'exponent', 'JWNowpO44rw 001216.000 (pixel profile, red field)', '2026-10-21', 'lens outline half-width w(v) = (1-|v|^a)^b of the drawn shield, tuned in F16 crop renders until the rendered red-field width fractions (10 % from the top, 3 % from the bottom tip, over mid-height) are 0.725 and 0.304 against the frame 0.734 and 0.300 (blender/concept_match/shield_fractions.py)', '+-0.2', 'derived', 'blender/shield_paint.py; blender/build_blockout.py shield_png', 'pointed lens, not a blunt oval (replica plan pass A)')
add('bowl.shield.outline_b', '0.82', 'exponent', 'JWNowpO44rw 001216.000 (pixel profile, red field)', '2026-10-21', 'tuned with bowl.shield.outline_a', '+-0.05', 'derived', 'blender/shield_paint.py; blender/build_blockout.py shield_png', '')
add('bowl.spear.blade_width_ratio', '2.2', 'x shaft diameter', 'lead order 2026-10-20 (pass A)', '2026-10-21', 'lead: long slender leaf blade, pointed tip, length 6.5 m (bowl.spear.blade_len), max width 2.2 x shaft diameter', '+-0.4', 'estimated', 'blender/build_blockout.py spears', 'supersedes bowl.spear.blade_r for the blade shape')
add('bowl.fin.backing_grey', '0.45', 'linear albedo', 'lead order 2026-10-20 (pass A)', '2026-10-21', 'lead: light grey backing behind the louvre fins, not a dark void; value set so the louvres read near-white in D02 overcast', '+-0.1', 'estimated', 'blender/build_scene.py facade_void_pbr', 'fin depth and slope unchanged')
add('bowl.shield.red', '#a4122c', 'sRGB albedo', 'JWNowpO44rw 001216.000 (sun), F16 render', '2026-10-21', 'paint albedo tuned in F16 crop renders (AgX + look layer unchanged) until the median red-field pixel renders within 12 levels/channel of the frame (165, 12, 57); crop tests: #a40c2c -> (170, 4, 59), #a4162c -> (171, 17, 59)', '+-4 levels', 'derived (render match)', 'blender/shield_paint.py; blender/build_blockout.py shield_png', 'supersedes #ad2750 (the paint, not the grade, per lead 2026-10-20)')
add('bowl.shield.black', '#1a1b1e', 'sRGB albedo', 'JWNowpO44rw 001216.000 (sun), F16 render', '2026-10-21', 'lobe albedo tuned with bowl.shield.red; crop test renders (20, 31, 42) against the frame (24, 28, 35)', '+-4 levels', 'derived (render match)', 'blender/shield_paint.py; blender/build_blockout.py shield_png', 'supersedes #1c1e22')
add('bowl.shield.roughness', '0.85', '1', 'JWNowpO44rw 001216.000, F16 render', '2026-10-21', 'matte paint: at 0.6 the sky reflection added a blue-grey veil (pure black rendered (33, 46, 56), pure red never below G 38); at 0.85 with low specular pure black renders (7, 13, 19)', '+-0.1', 'derived (render match)', 'shield material', 'supersedes 0.6')
add('bowl.shield.specular', '0.1', 'Specular IOR Level', 'JWNowpO44rw 001216.000, F16 render', '2026-10-21', 'set with bowl.shield.roughness: no sheen on the sunlit shield in the frame', '+-0.1', 'derived (render match)', 'blender/build_blockout.py shield material', 'Blender default 0.5')
add('bowl.roof.cushion_cols_per_bay', '2', 'count', 'JWNowpO44rw 000617.567 (D03, solved camera)', '2026-10-21', 'seam pitch along the near side measured in brightness profiles (rows 150, 160, 170 px): 26-30 px, against 52-55 px per topside-rib bay (30 bays) projected with the solved D03 camera; two cushion columns per rib bay (60 round the roof)', '+-0 (2 or 1)', 'derived (1 frame)', 'blender/build_blockout.py roof', 'the topside ribs (bowl.roof.cushion_bays 30) stay on every other seam')
add('bowl.roof.cushion_rows', '6', 'count', 'JWNowpO44rw 000617.567 (D03), 001221.500', '2026-10-21', 'seams counted from the opening trim to the outer rim in column profiles: D03 x 560-680 px, 5-6 intervals; 001221.500 x 500-900 px, 6 intervals', '+-1', 'derived (2 frames)', 'blender/build_blockout.py roof', 'supersedes 8')
add('bowl.roof.cushion_bulge_blockout', '2.8', 'm', 'JWNowpO44rw 000617.567 (D03), D03 crop renders', '2026-10-21', 'raised until the D03 overcast render shows a pillow in every row as in the frame (crop tests: 2.0 m read faint, 2.8 m with exponent 0.4 reads)', '+-0.6 m', 'estimated (render match by eye)', 'blender/build_blockout.py roof', 'supersedes 1.2')
add('bowl.roof.cushion_pillow_blockout', '0.4', 'exponent', 'JWNowpO44rw 000617.567 (D03), D03 crop renders', '2026-10-21', 'flat-topped pillows with steep seams: bulge * (sin pi u sin pi v)^0.4', '+-0.1', 'estimated (render match by eye)', 'blender/build_blockout.py roof', 'supersedes 0.6')
add('bowl.shield.outline_a', '2.1', 'exponent', 'JWNowpO44rw 001216.000, F16 crop renders on step_FA', '2026-10-21', 'with the 2.5 m fascia row the shield top sits lower and a = 1.85 renders a top fraction of 0.680 (limit); crop tests on step_FA: a = 2.0 -> 0.715 / 0.316, a = 2.15 -> 0.742 / 0.330; 2.1 interpolates to about 0.73 / 0.32 against the frame 0.734 / 0.300', '+-0.1', 'derived (render match)', 'blender/shield_paint.py; blender/build_blockout.py shield_png', 'supersedes 1.85')
add('site.west_road.width', '21', 'm', 'research/reference/dusk_aerial_finished_2026-10-17.jpg via camera P01 (back-projection)', '2026-10-22', 'by eye: two lanes each way and a median against the parked cars (4.5 m) in the photo', '+-3 m', 'estimated (photo back-projection, pass F)', 'blender/context/layout_final.py', 'finished state; the photo is internal reference only')
add('site.west_road.median', '2', 'm', 'research/reference/dusk_aerial_finished_2026-10-17.jpg via camera P01 (back-projection)', '2026-10-22', 'by eye', '+-1 m', 'estimated (photo back-projection, pass F)', 'blender/context/layout_final.py', 'finished state; the photo is internal reference only')
add('site.west_road.centre_x', '-156', 'm (app x at z 0)', 'research/reference/dusk_aerial_finished_2026-10-17.jpg via camera P01 (back-projection)', '2026-10-22', 'back-projected lane markings, 7 points from Ngong Road to z 650', '+-15 m', 'estimated (photo back-projection, pass F)', 'blender/context/layout_final.py', 'finished state; the photo is internal reference only')
add('site.railway.track_spacing', '4.5', 'm', 'standard metre-gauge double track; photo', '2026-10-22', 'by eye: two tracks, train on the far one', '+-0.5 m', 'estimated (photo back-projection, pass F)', 'blender/context/layout_final.py', 'finished state; the photo is internal reference only')
add('site.railway.ballast_width', '11', 'm', 'research/reference/dusk_aerial_finished_2026-10-17.jpg via camera P01 (back-projection)', '2026-10-22', 'by eye', '+-2 m', 'estimated (photo back-projection, pass F)', 'blender/context/layout_final.py', 'finished state; the photo is internal reference only')
add('site.railway.centre_x', '-204', 'm (app x at z 0)', 'research/reference/dusk_aerial_finished_2026-10-17.jpg via camera P01 (back-projection)', '2026-10-22', 'back-projected track centre', '+-20 m', 'estimated (photo back-projection, pass F)', 'blender/context/layout_final.py', 'finished state; the photo is internal reference only')
add('site.station.platform', '8.5;240;0.9', 'm (w;l;h)', 'research/reference/dusk_aerial_finished_2026-10-17.jpg via camera P01 (back-projection)', '2026-10-22', 'by eye: one side platform between the road and the tracks', '+-2 m; +-30 m; +-0.3 m', 'estimated (photo back-projection, pass F)', 'blender/context/layout_final.py', 'finished state; the photo is internal reference only')
add('site.station.canopy', '9.5;5.2', 'm (w;h above platform)', 'research/reference/dusk_aerial_finished_2026-10-17.jpg via camera P01 (back-projection)', '2026-10-22', 'by eye: two plain canopies, 74 m and 78 m long', '+-2 m', 'estimated (photo back-projection, pass F)', 'blender/context/layout_final.py', 'finished state; the photo is internal reference only')
add('site.footbridge.deck_clearance', '6.6', 'm above the road', 'research/reference/dusk_aerial_finished_2026-10-17.jpg via camera P01 (back-projection)', '2026-10-22', 'by eye against the buses and the station canopy', '+-1 m', 'estimated (photo back-projection, pass F)', 'blender/context/layout_final.py', 'finished state; the photo is internal reference only')
add('site.footbridge.width', '4.0', 'm', 'research/reference/dusk_aerial_finished_2026-10-17.jpg via camera P01 (back-projection)', '2026-10-22', 'by eye: enclosed deck', '+-1 m', 'estimated (photo back-projection, pass F)', 'blender/context/layout_final.py', 'finished state; the photo is internal reference only')
add('site.footbridge.length', '78.8', 'm', 'research/reference/dusk_aerial_finished_2026-10-17.jpg via camera P01 (back-projection)', '2026-10-22', 'from the car park verge over the road and both tracks to the west tower', '+-15 m', 'estimated (photo back-projection, pass F)', 'blender/context/layout_final.py', 'finished state; the photo is internal reference only')
add('site.carpark.module', '16.5', 'm (bay 5 + aisle 6.5 + bay 5)', 'convention; photo', '2026-10-22', 'bay rows as in the photo, stall pitch 2.6 m', '+-1 m', 'estimated (photo back-projection, pass F)', 'blender/context/layout_final.py', 'finished state; the photo is internal reference only')
add('site.carpark_north_west.area', '9432', 'm2', 'research/reference/dusk_aerial_finished_2026-10-17.jpg via camera P01 (back-projection)', '2026-10-22', 'polygon in blender/data/layout_final.json', '+-20%', 'estimated (photo back-projection, pass F)', 'blender/context/layout_final.py', 'finished state; the photo is internal reference only')
add('site.road_between_pitches.width', '8', 'm', 'research/reference/dusk_aerial_finished_2026-10-17.jpg via camera P01 (back-projection)', '2026-10-22', 'by eye', '+-2 m', 'estimated (photo back-projection, pass F)', 'blender/context/layout_final.py', 'finished state; the photo is internal reference only')
add('site.west_road.width', '21', 'm', 'research/reference/dusk_aerial_finished_2026-10-17.jpg via camera P01 (back-projection)', '2026-10-23', 'correction row; the pass F row above is kept for the record', '+-3 m', 'withdrawn 2026-10-23: source is an AI-generated image', 'none (blender/context/layout_final.py is out of the chain)', 'engineering/layout_audit_01/LEAD_REVIEW.md rev 2: research/reference/dusk_aerial_finished_2026-10-17.jpg is AI-generated (Argon), not layout evidence')
add('site.west_road.median', '2', 'm', 'research/reference/dusk_aerial_finished_2026-10-17.jpg via camera P01 (back-projection)', '2026-10-23', 'correction row; the pass F row above is kept for the record', '+-1 m', 'withdrawn 2026-10-23: source is an AI-generated image', 'none (blender/context/layout_final.py is out of the chain)', 'engineering/layout_audit_01/LEAD_REVIEW.md rev 2: research/reference/dusk_aerial_finished_2026-10-17.jpg is AI-generated (Argon), not layout evidence')
add('site.west_road.centre_x', '-156', 'm (app x at z 0)', 'research/reference/dusk_aerial_finished_2026-10-17.jpg via camera P01 (back-projection)', '2026-10-23', 'correction row; the pass F row above is kept for the record', '+-15 m', 'withdrawn 2026-10-23: source is an AI-generated image', 'none (blender/context/layout_final.py is out of the chain)', 'engineering/layout_audit_01/LEAD_REVIEW.md rev 2: research/reference/dusk_aerial_finished_2026-10-17.jpg is AI-generated (Argon), not layout evidence')
add('site.railway.track_spacing', '4.5', 'm', 'standard metre-gauge double track; photo', '2026-10-23', 'correction row; the pass F row above is kept for the record', '+-0.5 m', 'withdrawn 2026-10-23: source is an AI-generated image', 'none (blender/context/layout_final.py is out of the chain)', 'engineering/layout_audit_01/LEAD_REVIEW.md rev 2: research/reference/dusk_aerial_finished_2026-10-17.jpg is AI-generated (Argon), not layout evidence')
add('site.railway.ballast_width', '11', 'm', 'research/reference/dusk_aerial_finished_2026-10-17.jpg via camera P01 (back-projection)', '2026-10-23', 'correction row; the pass F row above is kept for the record', '+-2 m', 'withdrawn 2026-10-23: source is an AI-generated image', 'none (blender/context/layout_final.py is out of the chain)', 'engineering/layout_audit_01/LEAD_REVIEW.md rev 2: research/reference/dusk_aerial_finished_2026-10-17.jpg is AI-generated (Argon), not layout evidence')
add('site.railway.centre_x', '-204', 'm (app x at z 0)', 'research/reference/dusk_aerial_finished_2026-10-17.jpg via camera P01 (back-projection)', '2026-10-23', 'correction row; the pass F row above is kept for the record', '+-20 m', 'withdrawn 2026-10-23: source is an AI-generated image', 'none (blender/context/layout_final.py is out of the chain)', 'engineering/layout_audit_01/LEAD_REVIEW.md rev 2: research/reference/dusk_aerial_finished_2026-10-17.jpg is AI-generated (Argon), not layout evidence')
add('site.station.platform', '8.5;240;0.9', 'm (w;l;h)', 'research/reference/dusk_aerial_finished_2026-10-17.jpg via camera P01 (back-projection)', '2026-10-23', 'correction row; the pass F row above is kept for the record', '+-2 m; +-30 m; +-0.3 m', 'withdrawn 2026-10-23: source is an AI-generated image', 'none (blender/context/layout_final.py is out of the chain)', 'engineering/layout_audit_01/LEAD_REVIEW.md rev 2: research/reference/dusk_aerial_finished_2026-10-17.jpg is AI-generated (Argon), not layout evidence')
add('site.station.canopy', '9.5;5.2', 'm (w;h above platform)', 'research/reference/dusk_aerial_finished_2026-10-17.jpg via camera P01 (back-projection)', '2026-10-23', 'correction row; the pass F row above is kept for the record', '+-2 m', 'withdrawn 2026-10-23: source is an AI-generated image', 'none (blender/context/layout_final.py is out of the chain)', 'engineering/layout_audit_01/LEAD_REVIEW.md rev 2: research/reference/dusk_aerial_finished_2026-10-17.jpg is AI-generated (Argon), not layout evidence')
add('site.footbridge.deck_clearance', '6.6', 'm above the road', 'research/reference/dusk_aerial_finished_2026-10-17.jpg via camera P01 (back-projection)', '2026-10-23', 'correction row; the pass F row above is kept for the record', '+-1 m', 'withdrawn 2026-10-23: source is an AI-generated image', 'none (blender/context/layout_final.py is out of the chain)', 'engineering/layout_audit_01/LEAD_REVIEW.md rev 2: research/reference/dusk_aerial_finished_2026-10-17.jpg is AI-generated (Argon), not layout evidence')
add('site.footbridge.width', '4.0', 'm', 'research/reference/dusk_aerial_finished_2026-10-17.jpg via camera P01 (back-projection)', '2026-10-23', 'correction row; the pass F row above is kept for the record', '+-1 m', 'withdrawn 2026-10-23: source is an AI-generated image', 'none (blender/context/layout_final.py is out of the chain)', 'engineering/layout_audit_01/LEAD_REVIEW.md rev 2: research/reference/dusk_aerial_finished_2026-10-17.jpg is AI-generated (Argon), not layout evidence')
add('site.footbridge.length', '78.8', 'm', 'research/reference/dusk_aerial_finished_2026-10-17.jpg via camera P01 (back-projection)', '2026-10-23', 'correction row; the pass F row above is kept for the record', '+-15 m', 'withdrawn 2026-10-23: source is an AI-generated image', 'none (blender/context/layout_final.py is out of the chain)', 'engineering/layout_audit_01/LEAD_REVIEW.md rev 2: research/reference/dusk_aerial_finished_2026-10-17.jpg is AI-generated (Argon), not layout evidence')
add('site.carpark.module', '16.5', 'm (bay 5 + aisle 6.5 + bay 5)', 'convention; photo', '2026-10-23', 'correction row; the pass F row above is kept for the record', '+-1 m', 'withdrawn 2026-10-23: source is an AI-generated image', 'none (blender/context/layout_final.py is out of the chain)', 'engineering/layout_audit_01/LEAD_REVIEW.md rev 2: research/reference/dusk_aerial_finished_2026-10-17.jpg is AI-generated (Argon), not layout evidence')
add('site.carpark_north_west.area', '9432', 'm2', 'research/reference/dusk_aerial_finished_2026-10-17.jpg via camera P01 (back-projection)', '2026-10-23', 'correction row; the pass F row above is kept for the record', '+-20%', 'withdrawn 2026-10-23: source is an AI-generated image', 'none (blender/context/layout_final.py is out of the chain)', 'engineering/layout_audit_01/LEAD_REVIEW.md rev 2: research/reference/dusk_aerial_finished_2026-10-17.jpg is AI-generated (Argon), not layout evidence')
add('site.road_between_pitches.width', '8', 'm', 'research/reference/dusk_aerial_finished_2026-10-17.jpg via camera P01 (back-projection)', '2026-10-23', 'correction row; the pass F row above is kept for the record', '+-2 m', 'withdrawn 2026-10-23: source is an AI-generated image', 'none (blender/context/layout_final.py is out of the chain)', 'engineering/layout_audit_01/LEAD_REVIEW.md rev 2: research/reference/dusk_aerial_finished_2026-10-17.jpg is AI-generated (Argon), not layout evidence')
add('site.east_approach.ring', '129,25;129,-21;283,-37;298,10', 'm (app x,z corners)', 'JWNowpO44rw 000617.567 (D03); engineering/layout_audit_01/camera_estimates.json', '2026-10-23', 'camera rays on a flat ground plane (audit 01); west edge set on the outer edge of ge_apron_ring', '+-20 m', 'estimated (estimate from a camera solve)', 'blender/context/layout_pass_i.py', 'finished state; pale paving, no lanes, no markings, no cars; LEAD_REVIEW item 5')
add('site.east_approach.width', '40-50', 'm', 'JWNowpO44rw 000617.567 (D03); camera_estimates.json', '2026-10-23', 'transverse distances 46 m and 49 m between the solved corners', '+-10 m', 'estimated (estimate from a camera solve)', 'blender/context/layout_pass_i.py', 'total paved envelope, not a carriageway width')
add('site.east_approach.island', '144,2;184,-11;223,-1;192,13', 'm (app x,z corners)', 'JWNowpO44rw 000617.567 (D03); camera_estimates.json', '2026-10-23', 'camera rays on a flat ground plane (audit 01); about 79 m long, up to 24 m wide', '+-20 m', 'estimated (estimate from a camera solve)', 'blender/context/layout_pass_i.py', 'raised planted island, 0.25 m kerb; LEAD_REVIEW item 5')
add('site.east_approach.junction', 'ge_road_north_east meets the east end', 'topology', 'JWNowpO44rw 000617.567 (D03)', '2026-10-23', 'the 9 m route (site_layout_ge.json roads[0]) stops at the paved edge; no trees within 6 m of the approach', '', 'inference', 'blender/context/layout_pass_i.py', 'LEAD_REVIEW item 6')
add('site.south_west.grass', '-139,122;-73,135;-80,233;-153,228', 'm (app x,z corners)', 'JWNowpO44rw 000714.767 (D02), 000716.317; camera_estimates.json', '2026-10-23', 'camera rays on a flat ground plane (audit 01)', '+-25 m', 'estimated (estimate from a camera solve)', 'blender/context/layout_pass_i.py', 'finished state: grass inside the loop road, no pitch markings; loop road kept; LEAD_REVIEW item 3')
add('site.north_west.lawn', '-125..-57;-238..-143', 'm (app x range; z range)', 'JWNowpO44rw 000645.000 (D01), 000659.633', '2026-10-23', 'fc_west_lawn and fc_path_west from forecourt_layout.json:west_lawn, shown again in the finished state', '+-15 m', 'frame evidence', 'blender/context/layout_pass_i.py', 'lawn with red crossed paths, no cars; LEAD_REVIEW item 4')
add('site.forecourt_paths.colour', 'red murram', 'material', 'JWNowpO44rw 000645.000, 000659.633', '2026-10-23', 'kept from pass F; source changed from the AI image to the drone frames', '', 'frame evidence', 'blender/context/layout_pass_i.py', 'LEAD_REVIEW item 7')
add('site.osm_footways_inside_w1b', 'dropped', 'finished state', 'JWNowpO44rw 000645.000, 000659.633', '2026-10-23', 'kept from pass F; the frames show the new path network, not the old footways', '', 'frame evidence', 'blender/context/layout_pass_i.py', 'LEAD_REVIEW item 7; source changed from the AI image to these frames')
add('site.north_plaza.vehicle_route', 'none', 'topology', 'engineering/layout_audit_01/LAYOUT_AUDIT.md fix 9', '2026-10-23', 'no vehicle route across the north plaza or into the bowl', '', 'inference', 'blender/context/layout_pass_i.py', 'LEAD_REVIEW item 8')
add('site.pass_f_layout.finished', 'removed', 'finished state', 'engineering/layout_audit_01/LEAD_REVIEW.md rev 2 items 1 and 2', '2026-10-23', 'west_road, railway, station, footbridge, carpark_north_west (318 cars), spine_beds, carpark_south_west (207 cars, planted strip), road_between_pitches, track_ring_ne dark recolour not built; the objects pass F hid or cut are shown uncut (step_FE originals)', '', 'withdrawn 2026-10-23: source is an AI-generated image', 'blender/context/layout_pass_i.py (replaces layout_final.py)', 'asbuilt state unchanged')
add('context.landmark.enkang_a', '2,-423;45.5', 'm (app x,z centre; height)', 'gis/derived/near_ring_buildings.gpkg fid 8630 (Enkang Apartments A); map pin -102,-462 (engineering/landmarks_01/LANDMARK_CANDIDATES.md)', '2026-10-23', 'position: gpkg footprint named Enkang Apartments A (pin 111 m west: the pin marks the group label); height: gpkg open_buildings_2023 (open_buildings_2023), 14 storeys at 3.2 m; colours: JWNowpO44rw_000706.800 (cream tower, brown vertical strips, at dusk), 000619.700 (white towers with red-brown vertical panels, daylight)', 'footprint +-5 m; pin +-25 m', 'estimated (medium (inference: the 12-storey tower of 000706.800 is probably an Enkang block))', 'blender/context/landmarks_pass_j.py', 'Enkang Apartments A; plain mass, no names or signage; both states')
add('context.landmark.enkang_b', '-12,-457;47.0', 'm (app x,z centre; height)', 'gis/derived/near_ring_buildings.gpkg fid 8635 (Enkang Apartments B); map pin -102,-462 (engineering/landmarks_01/LANDMARK_CANDIDATES.md)', '2026-10-23', 'position: gpkg footprint named Enkang Apartments B; height: gpkg open_buildings_2023 (open_buildings_2023), 15 storeys at 3.2 m; colours: JWNowpO44rw_000706.800 (cream tower, brown vertical strips, at dusk), 000619.700 (white towers with red-brown vertical panels, daylight)', 'footprint +-5 m; pin +-25 m', 'estimated (medium)', 'blender/context/landmarks_pass_j.py', 'Enkang Apartments B; plain mass, no names or signage; both states')
add('context.landmark.enkang_c', '-52,-444;38.0', 'm (app x,z centre; height)', 'gis/derived/near_ring_buildings.gpkg fid 8625 (Enkang Apartments C); map pin -102,-462 (engineering/landmarks_01/LANDMARK_CANDIDATES.md)', '2026-10-23', 'position: gpkg footprint named Enkang Apartments C; height: gpkg open_buildings_2023 (open_buildings_2023), 12 storeys at 3.2 m; colours: JWNowpO44rw_000706.800 (cream tower, brown vertical strips, at dusk), 000619.700 (white towers with red-brown vertical panels, daylight)', 'footprint +-5 m; pin +-25 m', 'estimated (medium)', 'blender/context/landmarks_pass_j.py', 'Enkang Apartments C; plain mass, no names or signage; both states')
add('context.landmark.ngando_flats', '-275,-433;4.5', 'm (app x,z centre; height)', 'gis/derived/near_ring_buildings.gpkg fid 8575 (unnamed); map pin -275,-424 (engineering/landmarks_01/LANDMARK_CANDIDATES.md)', '2026-10-23', 'position: largest-area rule: nearest gpkg footprint of 100 m2 or more within 40 m of the map pin; height: gpkg (low; Open Buildings 2023) (open_buildings_2023), 1 storeys at 3.2 m; colours: JWNowpO44rw_000619.700, 000706.800, 000709.167: cream and white flat-roofed blocks (group level)', 'footprint +-5 m; pin +-25 m', 'estimated (low (000619.700 group, not resolved))', 'blender/context/landmarks_pass_j.py', 'Ngando Flats; plain mass, no names or signage; both states')
add('context.landmark.liberty_centre', '-102,-644;11.5', 'm (app x,z centre; height)', 'gis/derived/near_ring_buildings.gpkg fid 8408 (unnamed); map pin -100,-653 (engineering/landmarks_01/LANDMARK_CANDIDATES.md)', '2026-10-23', 'position: nearest gpkg footprint of 100 m2 or more within 40 m of the map pin; height: gpkg open_buildings_2023 (open_buildings_2023), 4 storeys at 3.2 m; colours: no frame; neutral pale walls, pale grey flat roofs', 'footprint +-5 m; pin +-25 m', 'estimated (low (no frame))', 'blender/context/landmarks_pass_j.py', 'Liberty Centre; plain mass, no names or signage; both states')
add('context.landmark.denali', '-155,-719;34.0', 'm (app x,z centre; height)', 'gis/derived/near_ring_buildings.gpkg fid 8290 (Denali Apartments); map pin -200,-796 (engineering/landmarks_01/LANDMARK_CANDIDATES.md)', '2026-10-23', 'position: gpkg footprint named Denali Apartments (34 m), 89 m from the map pin; used because the gpkg has only low buildings (5 m or less) within 40 m of the pin, so the pin marks the map label, not the block (decided 2026-10-23); height: gpkg open_buildings_2023 (open_buildings_2023), 11 storeys at 3.2 m; colours: JWNowpO44rw_000619.700, 000706.800, 000709.167: cream and white flat-roofed blocks (group level)', 'footprint +-5 m; pin +-25 m', 'estimated (medium (named footprint; no frame))', 'blender/context/landmarks_pass_j.py', 'Denali Apartments; plain mass, no names or signage; both states')
add('context.landmark.racecourse_gardens', '-472,-802;4.0', 'm (app x,z centre; height)', 'gis/derived/near_ring_buildings.gpkg fid 7113 (unnamed); map pin -468,-825 (engineering/landmarks_01/LANDMARK_CANDIDATES.md)', '2026-10-23', 'position: nearest gpkg footprint of 100 m2 or more within 40 m of the map pin; height: gpkg default_by_area (no measured height) (default_by_area), 1 storeys at 3.2 m; colours: JWNowpO44rw_000619.700, 000706.800, 000709.167: cream and white flat-roofed blocks (group level)', 'footprint +-5 m; pin +-25 m', 'estimated (low (no frame))', 'blender/context/landmarks_pass_j.py', 'Racecourse Gardens Apartments; plain mass, no names or signage; both states')
add('context.landmark.white_village', '164,-893;23.5', 'm (app x,z centre; height)', 'gis/derived/near_ring_buildings.gpkg fid 7827 (unnamed); map pin 174,-909 (engineering/landmarks_01/LANDMARK_CANDIDATES.md)', '2026-10-23', 'position: nearest gpkg footprint of 100 m2 or more within 40 m of the map pin; height: gpkg open_buildings_2023 (open_buildings_2023), 7 storeys at 3.2 m; colours: JWNowpO44rw_001242.050, 001244.833: white, grey and cream distant blocks (group level)', 'footprint +-5 m; pin +-25 m', 'estimated (low (no frame))', 'blender/context/landmarks_pass_j.py', 'White Village Apartments; plain mass, no names or signage; both states')
add('context.landmark.alba', '223,-976;41.5', 'm (app x,z centre; height)', 'gis/derived/near_ring_buildings.gpkg fid 10428 (TSAVO Skywalk); map pin 255,-890 (engineering/landmarks_01/LANDMARK_CANDIDATES.md)', '2026-10-23', 'position: gpkg footprint named TSAVO Skywalk (41.5 m), 92 m from the Alba pin; the gpkg has nothing above 15 m within 40 m of the pin, so the nearest tall block is used (handoff: probably Alba). The identity stays unconfirmed (decided 2026-10-23); height: gpkg open_buildings_2023 (open_buildings_2023), 13 storeys at 3.2 m; colours: JWNowpO44rw_000619.700, 000706.800, 000709.167: cream and white flat-roofed blocks (group level)', 'footprint +-5 m; pin +-25 m', 'estimated (low (000706.800 and 000709.167, not resolved))', 'blender/context/landmarks_pass_j.py', 'Alba Apartments; plain mass, no names or signage; both states')
add('context.landmark.kmd', '1095,-622;7.0', 'm (app x,z centre; height)', 'gis/derived/near_ring_buildings.gpkg fid 9665 (Kenya Meteorological Department); map pin 1084,-632 (engineering/landmarks_01/LANDMARK_CANDIDATES.md)', '2026-10-23', 'position: gpkg footprint named Kenya Meteorological Department; height: gpkg open_buildings_2023 (open_buildings_2023), 2 storeys at 3.2 m; colours: no frame; neutral pale walls, pale grey flat roofs', 'footprint +-5 m; pin +-25 m', 'estimated (medium (named footprint; no frame))', 'blender/context/landmarks_pass_j.py', 'Kenya Meteorological Department; plain mass, no names or signage; both states')
add('context.landmark.junction_0', '1357,-865;17.0', 'm (app x,z centre; height)', 'gis/derived/near_ring_buildings.gpkg fid 9846 (The Junction Mall); map pin 1410,-879 (engineering/landmarks_01/LANDMARK_CANDIDATES.md)', '2026-10-23', 'position: gpkg footprints named The Junction Mall; height: gpkg open_buildings_2023 (open_buildings_2023), 5 storeys at 3.2 m; colours: no frame; neutral pale walls, pale grey flat roofs', 'footprint +-5 m; pin +-25 m', 'estimated (medium (named footprints; outside all hero cameras, live twin only))', 'blender/context/landmarks_pass_j.py', 'The Junction Mall and Century Cinemax; plain mass, no names or signage; both states')
add('context.landmark.junction_1', '1442,-869;11.0', 'm (app x,z centre; height)', 'gis/derived/near_ring_buildings.gpkg fid 14176 (The Junction Mall); map pin 1410,-879 (engineering/landmarks_01/LANDMARK_CANDIDATES.md)', '2026-10-23', 'position: gpkg footprints named The Junction Mall; height: gpkg open_buildings_2023 (open_buildings_2023), 3 storeys at 3.2 m; colours: no frame; neutral pale walls, pale grey flat roofs', 'footprint +-5 m; pin +-25 m', 'estimated (medium (named footprints; outside all hero cameras, live twin only))', 'blender/context/landmarks_pass_j.py', 'The Junction Mall and Century Cinemax; plain mass, no names or signage; both states')

# Seat count pass 01 (2026-10-23, HANDOFF task 6): the upper tier gets the depth its 32 derived rows need and overhangs
# the middle tier (frames 000745-000805: its parapet overhangs the middle tier); the IT03 portals become vomitories that
# cut the rows they pass through. The _blockout rows override the build; the earlier rows stay as they were.
SC = "blender/renders/seat_count_01/README.md; blender/renders/tier_section_01/README.md"
add("bowl.tier_upper.t0_blockout", 0.54, "fraction", SC + "; JWNowpO44rw 000745.000, 000747.000", "2026-10-23",
    "32 rows (derived) at a tread of 0.75-0.89 m round the bowl (front-to-back depth 52.1-61.9 m, mean 57.3 m): t0 = 1 - 32 x 0.82 / 57.3",
    "+-0.03", "estimated (tread from the brief's 0.7-0.9 m range; overhang seen in 000745-000805)", "blender/build_blockout.py tiers",
    "replaces 0.70 in the build; the upper front now overhangs the middle tier (t1 0.66) by 0.12 of the depth, about 7 m")
add("bowl.tier_upper.soffit_drop_blockout", 0.7, "m below the upper front row", SC, "2026-10-23",
    "flat soffit under the overhang at the foot of the dark upper tier band (IF17, 0.7 m deep)", "+-0.3 m", "estimated",
    "blender/build_blockout.py tiers", "clear height over the middle tier back row: about 2.8 m")
add("bowl.portals.cut_rows", "yes", "", SC + "; JWNowpO44rw 000945.200, 002320.200", "2026-10-23",
    "the IT03 portal mouths run back into the tier until its treads reach the portal head; no seat stands inside a mouth or within 0.25 m of its jambs",
    "", "estimated", "blender/build_bowl_detail.py seats, IT03 portals", "generic openings only; no signage or egress meaning (AGENTS.md rule 8)")

# Pass K (2026-10-24, engineering/cloud_pass_k_2026-10-24.md, K7): landmark corrections and pick rule, Enkang palette,
# south plaza (D02 camera solve), east approach lens island, training grass look, K5c generic cap.
add('context.landmark.ngando_flats', '-275,-433;4.5', 'm (app x,z centre; height)', 'gis/derived/near_ring_buildings.gpkg fid 8575 (unnamed); map pin -275,-424', '2026-10-24', 'correction row for row 454 (kept): position by pick() (pass K, K5a): nearest gpkg footprint of 100 m2 or more within 40 m of the pin; if it is lower than 12 m, the tallest footprint above 12 m within 80 m (then the largest area); if there is none, the nearest footprint stays; no footprint taller than 12 m within 80 m (tallest 10.0 m, fid 4247), so fid 8575 (4.5 m) stays', 'footprint +-5 m; pin +-25 m', 'estimated (low; question for the lead in blender/renders/pass_k_check_01/README.md)', 'blender/context/landmarks_pass_j.py', "replaces the words 'largest-area rule' of row 454, which pick() never used")
add('context.landmark.racecourse_gardens', '-472,-802;4.0', 'm (app x,z centre; height)', 'gis/derived/near_ring_buildings.gpkg fid 7113 (unnamed); map pin -468,-825', '2026-10-24', 'correction row (row kept): position by pick() (pass K, K5a): nearest gpkg footprint of 100 m2 or more within 40 m of the pin; if it is lower than 12 m, the tallest footprint above 12 m within 80 m (then the largest area); if there is none, the nearest footprint stays; no footprint taller than 12 m within 80 m (tallest 6.5 m), so fid 7113 (4.0 m, default_by_area) stays', 'footprint +-5 m; pin +-25 m', 'estimated (low; question for the lead in blender/renders/pass_k_check_01/README.md)', 'blender/context/landmarks_pass_j.py', '')
add('context.landmark.junction_0', '1357,-865;17.0', 'm (app x,z centre; height)', 'gis/derived/near_ring_buildings.gpkg fid 9846 (The Junction Mall)', '2026-10-24', 'correction row for row 461 (kept): The Junction shows at the right edge of D02 (blender/renders/landmarks_pass_j_01/README.md, D02); it is not outside all hero cameras', 'footprint +-5 m; pin +-25 m', 'estimated (medium; named footprints; visible in D02)', 'blender/context/landmarks_pass_j.py', "corrects the text 'outside all hero cameras, live twin only'")
add('context.landmark.junction_1', '1442,-869;11.0', 'm (app x,z centre; height)', 'gis/derived/near_ring_buildings.gpkg fid 14176 (The Junction Mall)', '2026-10-24', 'correction row for row 462 (kept): The Junction shows at the right edge of D02 (blender/renders/landmarks_pass_j_01/README.md, D02); it is not outside all hero cameras', 'footprint +-5 m; pin +-25 m', 'estimated (medium; named footprints; visible in D02)', 'blender/context/landmarks_pass_j.py', "corrects the text 'outside all hero cameras, live twin only'")
add('context.landmark.pick_rule', 'nearest; tall fallback 12 m within 80 m', 'rule', 'engineering/cloud_pass_k_2026-10-24.md K5a', '2026-10-24', 'pick() (pass K, K5a): nearest gpkg footprint of 100 m2 or more within 40 m of the pin; if it is lower than 12 m, the tallest footprint above 12 m within 80 m (then the largest area); if there is none, the nearest footprint stays', '', 'rule', 'blender/context/landmarks_pass_j.py pick(); blender/data/landmarks_pass_j.json tall_min_m, tall_radius_m', 'checked on every landmark: blender/renders/pass_k_check_01/README.md; no landmark changes footprint')
add('context.landmark.enkang_palette', 'wall #DCCBA6; strips #6E3530 every 8 m (28 %); parapet #4A2A25 1.5 m; roof core 7 x 5 x 3.2 m; 2 tanks', 'sRGB; m', 'JWNowpO44rw 000706.800, 000619.700', '2026-10-24', 'by eye: cream and ochre walls, brown-maroon vertical strips full height, regular window grid, darker roof parapet, roof plant; no pixels used', 'colours +-15 %; sizes +-50 %', 'estimated (by eye)', 'blender/data/landmarks_pass_j.json palettes.enkang; landmarks_pass_j.py mass(), roof_plant()', 'positions and heights unchanged (gpkg 38, 45.5, 47 m)')
add('site.south_plaza.outline', '-51.1,124.9;2.2,132.1;45.8,145.4;21,228.1;-5.1,254.6;-39.8,260.4;-64,254.8;-63.5,220', 'm (app x,z corners)', 'JWNowpO44rw 000714.767 (D02), 000716.317; camera solve as engineering/layout_audit_01/camera_estimates.json', '2026-10-24', 'pixels picked in D02, rays through the manifest pose on a flat plane y 6.12; the three north points are replaced by the outer edge of ge_apron_ring', '+-25 m (plane sensitivity 19.46 m)', 'estimated (estimate from a camera solve)', 'blender/context/plaza_south_k.py; blender/data/plaza_south_k.json', "finished state; Sol's audit centre 15,195 lies 33 m east of the solved bed; extent here about 110 x 135 m")
add('site.south_plaza.round_bed', '-15.7,206.1;9.5', 'm (app x,z centre; radius)', 'JWNowpO44rw 000714.767 (D02), 000716.317; camera solve as engineering/layout_audit_01/camera_estimates.json', '2026-10-24', 'bed centre and four edge points back-projected; radius from the edges (about 10 m)', '+-25 m centre; +-3 m radius', 'estimated (estimate from a camera solve)', 'blender/context/plaza_south_k.py', 'finished state')
add('site.south_plaza.axial_beds', 'north -11.4,158.2 to -12.7,193.1; south -17.4,218.7 to -19.6,251.5', 'm (app x,z centre line)', 'JWNowpO44rw 000714.767 (D02), 000716.317; camera solve as engineering/layout_audit_01/camera_estimates.json', '2026-10-24', 'bed end points back-projected; width 5 m by eye', '+-25 m', 'estimated (estimate from a camera solve)', 'blender/context/plaza_south_k.py', 'finished state')
add('site.south_plaza.finish', 'pale paving (fc_paving), kerbs 0.3 x 0.18 m, beds raised 0.3 m with 0.25 x 0.15 m kerbs', 'material', 'forecourt_layout.json north plaza pattern', '2026-10-24', 'same finish as the north plaza', '', 'inference', 'blender/context/plaza_south_k.py', 'finished state')
add('site.south_plaza.planting', 'round bed: 2 m murram ring round a planted centre; axial beds: murram', 'material', 'JWNowpO44rw 000714.767 (D02), 000716.317; camera solve as engineering/layout_audit_01/camera_estimates.json', '2026-10-24', 'by eye: dark red-brown beds, green centre in the round bed', '', 'inference', 'blender/context/plaza_south_k.py', 'finished state')
add('site.east_approach.island', 'tips 144,2 and 223,-1; lens 23 m wide at the middle, 32 points', 'm (app x,z)', 'JWNowpO44rw 000617.567 (D03); camera_estimates.json east_approach_island', '2026-10-24', 'correction row for the pass I island row (kept): the diamond becomes a long pointed lens (parabolic sides); tips are the solved tips; width from the solved width across the middle (about 24 m)', '+-20 m', 'estimated (estimate from a camera solve)', 'blender/context/layout_pass_i.py island_ring(); blender/data/layout_pass_i.json', 'lens outline itself: inference')
add('site.east_approach.island_kerb', '0.25', 'm', 'engineering/cloud_pass_k_2026-10-24.md K3', '2026-10-24', 'raised kerb round the island; not from the camera solve', '+-0.1 m', 'inference', 'blender/context/layout_pass_i.py', '')
add('site.east_approach.island_planting', 'murram bed with planted strips (lf_murram_bed)', 'material', 'engineering/cloud_pass_k_2026-10-24.md K3', '2026-10-24', 'planted top of the island; not from the camera solve', '', 'inference', 'blender/context/layout_pass_i.py', '')
add('site.training_grass.look', 'stripes #58763F/#5F7C46 (pitches only); patches #53703B-#6C8048 at 8-20 m; roughness 0.80-0.92; bump 0.15', 'sRGB; m', 'L07 check render against the Grass005 grass', '2026-10-24', 'saturation lowered from about 0.60 to 0.45 by eye against the other grass in the same render; world-space noise; no frame pixels', 'colours +-10 %', 'estimated (by eye)', 'blender/grass_look.py; build_site_detail.py; context/grass_k.py', 'no markings on the south-west lawn')
add('context.generic_cap.l07', '37 blocks lowered (by median 37, by footprint 0)', 'count', 'engineering/cloud_pass_k_2026-10-24.md K5c; gis/derived/near_ring_buildings.gpkg', '2026-10-24', 'background_b.py blocks (bg_midrise_near, bg_midrise_far) in the L07 view cone (camera half-angle + 5 deg) within 1,500 m of the bowl: a gpkg footprint under the block gives its height; otherwise the height is capped at the median gpkg height within 200 m; CBD, Upper Hill, Kilimani and Westlands untouched', '', 'rule', 'blender/context/landmarks_pass_j.py; blender/data/landmarks_pass_j.json generic_cap', 'the medians there are 4.0 to 4.5 m, so the lowered blocks read as one storey (question for the lead in blender/renders/pass_k_check_01/README.md); both states')
add('site.training_grass.look', 'stripes #5A7B39/#5F7F3E (pitches only); patches #527234-#788545 at 8-20 m; brightness +-25 %; roughness 0.80-0.92; bump 0.15', 'sRGB; m', 'L07 check renders: south-west lawn against the Grass005 lawns beside it', '2026-10-24', 'correction row for the K4 row above (kept): tuned on L07 crops; the lawn rendered at saturation 0.64 and nearly flat (std 1) before pass K, 0.48 at the first tuning, 0.53 now, against about 0.56 for the lawns beside it', 'colours +-10 %', 'estimated (render match by eye)', 'blender/grass_look.py; build_site_detail.py; context/grass_k.py', 'no markings on the south-west lawn')

# Web hero v2 order W0.2 (2026-10-24): the south plaza size, measured from blender/data/plaza_south_k.json and the built
# paving in step_FK. Correction row; the pass K row stays as it was.
add("site.south_plaza.outline", "110 x 135 (solved outline); 109 x 123 (built paving)", "m (x by z extent)",
    "blender/data/plaza_south_k.json outline; pk_south_plaza in step_FK", "2026-10-24",
    "axis-aligned extent: solved outline x -64.0 to 45.8, z 124.9 to 260.4; built paving x -64.0 to 45.0, z 136.6 to 260.0 (north edge on the outer edge of ge_apron_ring)",
    "+-25 m (plane sensitivity 19.46 m)", "estimated (estimate from a camera solve)", "blender/context/plaza_south_k.py",
    "correction: the solved outline is 110 x 135 m as the pass K row says; blender/renders/pass_k_check_01/README.md said 110 x 125 m and is corrected. Centres: round bed -15.7,206.1; built paving -17.5,195.2; both about 33 m west of Sol's audit centre 15,195, outside the 25 m uncertainty; position kept")

out = ROOT / "gis/parameter_ledger.csv"
with open(out, "w", newline="") as f:
    w = csv.DictWriter(f, COLS, lineterminator="\n"); w.writeheader(); w.writerows(rows)
from collections import Counter
print(out, len(rows), "rows", dict(Counter(r["status"] for r in rows)))
