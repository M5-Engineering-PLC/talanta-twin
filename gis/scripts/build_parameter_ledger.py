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
# Accepted rows: leave-one-frame-out spread under 2 m (max - min over 8 runs). 001232.600 is left out: its camera
# could not be matched (junction error 150-180 px in every start). Rejected fits are kept as *.fit_* rows (not read).
PF = "JWNowpO44rw 000641.633, 000659.633, 001221.500, 001224.500, 001235.934, 001239.267, 001244.833, 001247.833"
PFU = "blender/build_blockout.py profile()"
def pf(n, v, u, spread, method, note=""):
    add(n, v, u, PF, "2026-10-18", method, f"+-{spread / 2:.1f} m", f"derived (8 frames, spread {spread:.1f} m)", PFU, note)
def pfr(n, v, u, spread, method):
    add(n, v, u, PF, "2026-10-18", method, f"spread {spread:.1f} m", f"estimated (frame fit, spread {spread:.1f} m, not accepted)", "", "not read by the build; the earlier estimate stays")
pf("bowl.profile.foot_inset", 0.74, "m", 0.99, "least squares on silhouette, roof opening, junction, foot and labelled shields; one focal length and k1 per lens", "wall foot inside the roof outer ring")
pf("bowl.profile.wall_bulge", -2.89, "m", 1.62, "least squares on silhouette, roof opening, junction, foot and labelled shields; one focal length and k1 per lens", "negative: the wall bows inward at mid height")
pf("bowl.profile.roof_sag", -2.74, "m", 1.60, "least squares on silhouette, roof opening, junction, foot and labelled shields; one focal length and k1 per lens", "negative: the roof rises between the crest and the opening")
pfr("bowl.profile.fit_wall_top_y", 46.37, "m", 2.86, "least squares on silhouette, roof opening, junction, foot and labelled shields; one focal length and k1 per lens")
pfr("bowl.profile.fit_shoulder_rh", 10.16, "m", 5.12, "least squares on silhouette, roof opening, junction, foot and labelled shields; one focal length and k1 per lens")
pfr("bowl.profile.fit_shoulder_rv", 4.65, "m", 3.46, "least squares on silhouette, roof opening, junction, foot and labelled shields; one focal length and k1 per lens")
pfr("bowl.profile.fit_opening_y", 51.09, "m", 4.07, "least squares on silhouette, roof opening, junction, foot and labelled shields; one focal length and k1 per lens")
pfr("bowl.profile.fit_shield_centre_y", 27.47, "m", 4.91, "least squares on silhouette, roof opening, junction, foot and labelled shields; one focal length and k1 per lens")
pfr("bowl.profile.fit_crest_y", 51.01, "m", 4.40, "least squares on silhouette, roof opening, junction, foot and labelled shields; one focal length and k1 per lens")
add("bowl.roof.cushion_bays", 30, "count", "JWNowpO44rw 001221.500, 001224.500", "2026-10-18", "topside rib seams against projected rib lines (30, 40, 60) with the solved cameras; both frames match 30", "+-2", "derived (2 frames)", "blender/build_blockout.py roof, roof_ribs", "the 60 underside primaries (bowl.roofsteel.ribs) carry a top rib on every other one")
add("bowl.roof.cushion_rows", 8, "count", "JWNowpO44rw 001232.600, 001235.934", "2026-10-18", "by eye: cushion rows from the rim to the opening in the front bays", "+-1", "estimated (frames 001232.600, 001235.934)", "blender/build_blockout.py roof")
add("bowl.roof.cushion_bulge", 0.45, "m", "JWNowpO44rw 001232.600, 001235.934", "2026-10-18", "by eye: highlight and shadow per cushion", "+-0.2 m", "estimated (frames 001232.600, 001235.934)", "blender/build_blockout.py roof")

out = ROOT / "gis/parameter_ledger.csv"
with open(out, "w", newline="") as f:
    w = csv.DictWriter(f, COLS, lineterminator="\n"); w.writeheader(); w.writerows(rows)
from collections import Counter
print(out, len(rows), "rows", dict(Counter(r["status"] for r in rows)))
