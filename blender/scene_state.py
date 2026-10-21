"""Surface state switch (replica plan 2026-10-20, pass C): one geometry, two surface states.

"finished": the mockup look (landing L06, L07 and the web bundle). The scene as built.
"asbuilt": the drone frames of early 2026 (D01-D03, F16, F32): the traced as-built ground (collection asbuilt_ground,
blender/context/asbuilt_ground.py: murram, bare earth, laterite, patchy grass, asphalt from asbuilt_trace.py) instead
of the finished surfaces, and no planted dressing (beds, shrubs, flowers, palms, young trees, car park markings), which
the frames do not show yet. Masts, lamp poles, the fence, buildings, the bowl and the context stay in both states.
Use: set_state(scene, "asbuilt" | "finished"); render_cycles.py reads TALANTA_STATE.
"""
import bpy

STATES = ("asbuilt", "finished")
ONLY_ASBUILT = {"asbuilt_ground"}  # collections shown only in the asbuilt state
ONLY_FINISHED = {"sport", "forecourt", "canopy_slots", "trace_sw_finished", "context_l07_visualization",
                 "people_visualization", "parked_cars_visualization"}  # whole collections hidden in asbuilt
# objects hidden in asbuilt inside collections that also hold kept objects: name prefixes per collection
ONLY_FINISHED_PREFIX = {
    "finish_plaza": ("fp_shrub", "fp_flower", "fp_tree", "fp_plaza", "fp_beds", "fp_paths"),
    "forecourt_context": ("palm_slot", "fc_central", "fc_axial", "fc_edge", "fc_path", "fc_bench", "fc_retained", "fc_planter"),
    "site": ("palms", "site_trees", "shrubs", "planters", "jets", "sign_frames", "entrance_canopies", "parking_lines", "bollards"),
    "site_layout_ge": ("ge_apron_ring", "ge_east_hardstanding", "ge_road_north_east_euc"),  # the euc row is not planted yet in the frames
}
EXACT_FINISHED = {"ge_road_north_east"}  # the road surface; its lamps and trees (ge_road_north_east_*) stay


def _finished_only(o):
    for c in o.users_collection:
        if c.name in ONLY_FINISHED: return True
        if o.name in EXACT_FINISHED: return True
        if any(o.name.startswith(p) for p in ONLY_FINISHED_PREFIX.get(c.name, ())): return True
    return False


def set_state(scene, state):
    if state not in STATES: raise ValueError(f"state must be one of {STATES}")
    asb = state == "asbuilt"
    for o in scene.objects:
        if "state_hide_render" not in o.keys(): o["state_hide_render"] = o.hide_render  # as built, once
        base = bool(o["state_hide_render"])
        if any(c.name in ONLY_ASBUILT for c in o.users_collection): o.hide_render = base or not asb
        elif _finished_only(o): o.hide_render = base or asb
        else: o.hide_render = base
    scene["talanta_state"] = state
    return state
