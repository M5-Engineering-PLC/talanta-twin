"""Internal layout audit. Uses indexed images and JSON. Does not import Blender."""
import csv
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
ROWS = list(csv.DictReader((ROOT / 'research/video_index/MASTER_INDEX.csv').open()))
INDEX = {Path(r['file']).name: r for r in ROWS}
CAMS = {c['id']: c for c in json.loads((ROOT / 'app/cameras/manifest.json').read_text())['cameras']}
FONT = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 16)
MAIN = 'JWNowpO44rw_'
GROUPS = [
 ('01_main.jpg', ['000454.933','000501.933','000506.533','000517.300']),
 ('02_main.jpg', ['000617.567','000641.633','000645.000','000659.633']),
 ('03_main.jpg', ['000714.767','000716.317','001246.333','000612.433']),
 ('04_other.jpg', ['OB0OE-PAAVg_000012.345','_SnnNoRfzkA_000024.000','zb4ISsX7Pa0_000000.000','3ZiiGojVM70_000618.000']),
 ('05_other.jpg', ['LhY5-yDuhfc_000020.000','mJJ4Qkl858k_000014.000','020A-X2A2V4_000103.159','HU3J94fa8_c_000332.000']),
 ('06_other.jpg', ['h--Jmi7SwBs_000058.000','9I1korKNjig_000034.000','KEOmkVfjhu8_001330.000','cyNgbyZv6BM_000152.000']),
 ('10_followup.jpg', ['HU3J94fa8_c_000650.000','HU3J94fa8_c_000958.000','HU3J94fa8_c_001334.000','HU3J94fa8_c_001822.000']),
 ('11_followup.jpg', ['h--Jmi7SwBs_000414.000','h--Jmi7SwBs_000728.000','020A-X2A2V4_000248.000','020A-X2A2V4_000326.000']),
 ('12_followup.jpg', ['000441.933','000606.233','OB0OE-PAAVg_000035.034','001232.600'])]


def name(s):
    return (MAIN + s if s[0].isdigit() and '_' not in s else s) + '.jpg'


def frame_state(r):
    if r['video_id'] == 'JWNowpO44rw' and 280 <= float(r['timestamp_s']) < 375:
        return 'finished design model; not completed site'
    if r['video_id'] == '020A-X2A2V4':
        return 'asbuilt night lighting; full completion unknown'
    return 'asbuilt construction; capture date unknown'


def sheets():
    records = []
    for dest, names in GROUPS:
        out = Image.new('RGB', (1600, 1060), '#202020')
        draw = ImageDraw.Draw(out)
        for j, n in enumerate(names):
            r = INDEX[name(n)]
            assert r['video_id'] not in ('oL3wsPsx4Jw', 'PWj9s_v3G6U')
            assert 'nyayo' not in r['subject'].lower()
            im = Image.open(ROOT / r['file'])
            im.thumbnail((790, 445))
            x, y = j % 2 * 800, j // 2 * 530
            out.paste(im, (x, y))
            for dy, txt in [(450, name(n)), (475, frame_state(r)), (500, 'video ' + r['timestamp_s'] + ' s | INTERNAL ONLY')]:
                draw.text((x + 4, y + dy), txt, fill='white', font=FONT)
            records.append(dict(r, state=frame_state(r), sheet='sheets/' + dest))
        out.save(OUT / 'sheets' / dest, quality=90)
    (OUT / 'source_frames.json').write_text(json.dumps(records, indent=2) + '\n')


def backproject(cid, uv, ground_y=6.12):
    c = CAMS[cid]
    p = np.array(c['position'], dtype=float)
    f = np.array(c['target']) - p
    f /= np.linalg.norm(f)
    r = np.cross(f, [0, 1, 0]); r /= np.linalg.norm(r)
    u = np.cross(r, f)
    a = math.radians(c.get('roll_deg', 0))
    r, u = r * math.cos(a) + u * math.sin(a), u * math.cos(a) - r * math.sin(a)
    v = math.tan(math.radians(c['vfov_deg']) / 2)
    ray = f + r * ((uv[0] / 1280 * 2 - 1) * v * 1280 / 720) + u * ((1 - uv[1] / 720 * 2) * v)
    q = p + ray * ((ground_y - p[1]) / ray[1])
    return [round(float(q[0]), 2), round(float(q[2]), 2)]


def estimates():
    selections = [
      ('east_approach_envelope', 'D03', '000617.567', [(548,321),(663,321),(741,629),(546,680)]),
      ('east_training_rectangle', 'D03', '000617.567', [(198,354),(530,355),(522,479),(123,482)]),
      ('south_west_grass', 'D02', '000714.767', [(294,471),(524,468),(538,642),(110,680)]),
      ('east_approach_island', 'D03', '000617.567', [(603,340),(637,400),(606,472),(565,413)])]
    records = []
    for ident, cid, n, pixels in selections:
        pts = [backproject(cid,p) for p in pixels]
        sensitivity = max(math.dist(backproject(cid,p,0),q) for p,q in zip(pixels,pts))
        records.append(dict(id=ident, camera_solve=cid, evidence=MAIN+n+'.jpg',
            image_size_px=[1280,720], pixels=pixels, ring_m=pts,
            label='estimate from a camera solve', ground_plane_y_m=6.12,
            ground_plane_0_sensitivity_max_m=round(sensitivity,2),
            uncertainty_m=15, method='Pinhole rays through manifest pose and vfov. Flat plane only. Roll rotates image basis. No terrain fit.'))
    (OUT / 'camera_estimates.json').write_text(json.dumps(records, indent=2)+'\n')
    for r in records: print(r['id'],r['ring_m'],'plane sensitivity',r['ground_plane_0_sensitivity_max_m'])
    return {r['id']:r for r in records}


if __name__ == '__main__':
    sheets()
    estimates()
    print('SOFTWARE: 36 indexed frames in 9 evidence sheets; 4 camera estimates.')
