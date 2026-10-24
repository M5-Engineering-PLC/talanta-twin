"""Pass K, K6: a day call after a dusk call in the same process must give the day values (runs without Blender).

Run: python3 -m pytest blender/test_hero_artistic_day_dusk.py  (or python3 blender/test_hero_artistic_day_dusk.py)
"""
import copy
import sys
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent

# stubs for the Blender modules hero_artistic.py imports at the top, and a lookdev with its own STRENGTHS
for name in ("bpy", "bmesh", "mathutils"):
    sys.modules.setdefault(name, types.ModuleType(name))
sys.modules["mathutils"].Vector = lambda *a: a
LOOKDEV_DAY = {
    "aerial_band_haze": {"horizon_band_1": 0.08, "horizon_band_2": 0.10, "horizon_band_3": 0.12, "horizon_band_4": 0.15,
                         "terrain_horizon": 0.18, "terrain_horizon_hills": 0.58, "terrain_horizon_far": 0.70},
    "aerial_far_tint": (0.85, 0.95), "glare": 0.0, "glare_threshold": 1.0,
}
lookdev = types.ModuleType("lookdev"); lookdev.STRENGTHS = copy.deepcopy(LOOKDEV_DAY)
sys.modules["lookdev"] = lookdev
sys.path.insert(0, str(HERE))
import hero_artistic as ha  # noqa: E402

# prepare() without a scene: the scene helpers become no-ops, only the look-layer values are under test
ha._render = lambda scene: None
ha._uplights = lambda scene, dusk: {}
ha._bevels_and_fins = lambda: {}
ha._cars = lambda scene: {}
ha._people = lambda scene: {}
SCENE = types.SimpleNamespace(objects=[])


def far(s):
    return {k: s["aerial_band_haze"][k] for k in ("terrain_horizon_hills", "terrain_horizon_far")}, tuple(s["aerial_far_tint"])


def test_day_values_match_lookdev_defaults():
    assert far(LOOKDEV_DAY) == (ha.SET["day_far_haze"], tuple(ha.SET["day_far_tint"]))


def test_day_after_dusk_gives_day_values():
    lookdev.STRENGTHS = copy.deepcopy(LOOKDEV_DAY)
    ha.prepare(SCENE, True)
    assert far(lookdev.STRENGTHS) == (ha.SET["dusk_far_haze"], tuple(ha.SET["dusk_far_tint"]))
    ha.prepare(SCENE, False)
    assert far(lookdev.STRENGTHS) == far(LOOKDEV_DAY)
    # the other bands are never touched
    assert {k: v for k, v in lookdev.STRENGTHS["aerial_band_haze"].items() if k.startswith("horizon_band")} == \
        {k: v for k, v in LOOKDEV_DAY["aerial_band_haze"].items() if k.startswith("horizon_band")}


def test_dusk_after_day_gives_dusk_values():
    lookdev.STRENGTHS = copy.deepcopy(LOOKDEV_DAY)
    ha.prepare(SCENE, False); ha.prepare(SCENE, True)
    assert far(lookdev.STRENGTHS) == (ha.SET["dusk_far_haze"], tuple(ha.SET["dusk_far_tint"]))


if __name__ == "__main__":
    for t in (test_day_values_match_lookdev_defaults, test_day_after_dusk_gives_day_values, test_dusk_after_day_gives_dusk_values):
        t(); print("ok", t.__name__)
