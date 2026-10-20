"""Render C06 once on the CPU without saving any Blender scene."""
import hashlib, json, os, sys, time, traceback
from pathlib import Path
import bpy

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'blender/renders/codex_suburbs'
SOURCE = ROOT / 'blender/out/talanta_site.blend'


def _digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''): h.update(chunk)
    return h.hexdigest()


try:
    before = _digest(SOURCE); before_stat = SOURCE.stat()
    OUT.mkdir(parents=True, exist_ok=True)
    # Use the frozen C06 camera and the existing morning lighting setup.
    path = ROOT / 'blender/render_cycles.py'
    setup = path.read_text().split('# ---- end of scene setup:')[0]
    setup = setup.replace('s = bpy.context.scene', '''s = bpy.context.scene
for image in bpy.data.images:
    prefix = '/home/user/talanta-twin/'
    if image.filepath.startswith(prefix):
        local = ROOT / image.filepath[len(prefix):]
        if not local.is_file(): raise FileNotFoundError(local)
        image.filepath = str(local)
''', 1)
    argv = sys.argv[:]
    sys.argv = [str(path), 'blender/renders/codex_suburbs', 'C06', 'morning', 'preview']
    env = {'__file__': str(path), '__name__': '__suburbs_test__'}
    exec(compile(setup, str(path), 'exec'), env)
    sys.argv = argv
    scene = bpy.context.scene
    sys.path.insert(0, str(ROOT / 'blender/context'))
    from suburbs import build, CLAIM, LIMIT
    t0 = time.perf_counter(); report = build(scene, ROOT); build_seconds = time.perf_counter() - t0
    collection = bpy.data.collections['suburbs_context']
    counted = 0
    for ob in collection.objects:
        assert ob.get('claim') == CLAIM, ob.name
        if ob.type == 'MESH':
            ob.data.calc_loop_triangles(); counted += len(ob.data.loop_triangles)
            assert len(ob.data.attributes['height_src'].data) == len(ob.data.polygons)
        elif ob.instance_type == 'COLLECTION':
            for child in ob.instance_collection.all_objects:
                assert child.get('claim') == CLAIM, child.name
                child.data.calc_loop_triangles(); counted += len(child.data.loop_triangles)
    assert counted == report['added_triangles'], (counted, report)
    assert 0 < counted <= LIMIT
    assert report['low_buildings'] > 0 and report['midrise_buildings'] > 0 and report['trees'] > 500
    print(f'SUBURBS_ASSERTIONS_OK: {counted} triangles including all collection instances', flush=True)
    scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'; scene.cycles.samples = 8
    scene.render.resolution_x = 480; scene.render.resolution_y = 270; scene.render.resolution_percentage = 100
    scene.render.threads_mode = 'FIXED'; scene.render.threads = 2
    if hasattr(scene.render, 'compositor_device'): scene.render.compositor_device = 'CPU'
    scene.render.image_settings.file_format = 'PNG'; scene.render.filepath = str(OUT / 'C06_suburbs.png')
    t0 = time.perf_counter(); bpy.ops.render.render(write_still=True); render_seconds = time.perf_counter() - t0
    assert (OUT / 'C06_suburbs.png').is_file()
    assert _digest(SOURCE) == before and SOURCE.stat().st_mtime_ns == before_stat.st_mtime_ns
    report.update(build_seconds=round(build_seconds, 3), render_seconds=round(render_seconds, 3), source_sha256=before, blend_unchanged=True)
    notes = '''Talanta Twin suburbs, 2026-10-17
Project: Talanta Twin, private internal reference.
Status: software test and artistic visualization. No physical measurements.
Source scene: blender/out/talanta_site.blend.
Sources: gis/derived/near_ring_buildings.gpkg and the existing buildings mesh.
Visual references: lead renders 06 and 07, and JWNowpO44rw at 07:04.
The references inform geometry and colors. No reference image becomes a texture.
The source scene stays intact. This test saves no Blender scene.

The module preserves source wall heights and assigns a height source to each detail face.
The building_sources property maps building_fid values to source IDs, heights, and height sources.
The source height defines the eave. Roof rise and parapets are additional estimates.
Floor counts use source heights divided by 3.2 m, rounded to the nearest floor.
Low buildings receive gable roofs clipped to their original roof triangles.
Mid-rise blocks receive parapets, window rows, and shared rooftop tanks.
The roof palette favors red-brown tile and rust iron sheet.
Mature trees use three shared collections north of Ngong Road.
Tree locations exclude building footprints and existing road surfaces.
Every added object carries the required claim property.
Triangle totals include every visible instance, including tanks and trees.

Camera: frozen C06, morning, 480x270, 8 samples, CPU Cycles, two threads.
The test remaps existing cloud texture paths in memory to local assets.
Command: /snap/blender/current/blender -b --factory-startup -t 2 -P blender/context/run_test.py

Integration before the save in blender/build_site_detail.py:
    import sys
    sys.path.insert(0, str(ROOT / "blender"))
    from context.suburbs import build as build_suburbs
    suburbs_report = build_suburbs(scene, ROOT)
No main.js integration is required. The cloud build owns the scene integration.
The build function accepts the repository root path and must run once per loaded scene.

Observed software results:
'''
    notes += json.dumps(report, indent=2) + '\n'
    (OUT / 'notes.txt').write_text(notes)
    print('SUBURBS_TEST ' + json.dumps(report), flush=True)
except Exception:
    traceback.print_exc(); sys.stdout.flush(); sys.stderr.flush(); os._exit(1)
# Avoid unrelated shutdown faults from the headless Blender installation.
sys.stdout.flush(); sys.stderr.flush(); os._exit(0)
