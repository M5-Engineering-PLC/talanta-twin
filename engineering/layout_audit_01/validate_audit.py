"""Acceptance tests for the audit artifacts. No Blender or network."""
import csv
import json
import math
import re
import subprocess
from pathlib import Path
from PIL import Image

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
plan=json.loads((OUT/'layout_plan.json').read_text())
f=plan['features']
assert len({x['id'] for x in f})==len(f)
report=(OUT/'LAYOUT_AUDIT.md').read_text()
rows=[l for l in report.splitlines() if l.startswith('| ') and ' / ' in l.split('|')[1]]
assert len(rows)==len(f),(len(rows),len(f))
lf=json.loads((ROOT/'blender/data/layout_final.json').read_text())
expected=set(lf)-{'_note','source'}
ge=json.loads((ROOT/'blender/data/site_layout_ge.json').read_text())
expected|={'apron_ring'}
expected|={x['name'] for group in ['roads','buildings','car_parks'] for x in ge[group]}
assert len(expected)==14
assert expected <= {x['id'] for x in f}
idx={r['file']:r for r in csv.DictReader((ROOT/'research/video_index/MASTER_INDEX.csv').open())}
valid_labels={'frame evidence','estimate from a camera solve','inference'}
for x in f:
 assert x['type'] and x['state'] in {'finished','asbuilt'}
 assert x['confidence'] in {'high','medium','low'}
 assert x['finding_label'] in valid_labels and x['evidence']
 assert any(x['id']+' / '+x['model_source'] in row for row in rows)
 for e in x['evidence']:
  r=idx[e['file']]
  assert (ROOT/e['file']).is_file()
  assert r['video_id'] not in {'oL3wsPsx4Jw','PWj9s_v3G6U'}
  assert 'nyayo' not in r['subject'].lower()
  assert math.isclose(float(r['timestamp_s']),e['timestamp_s'],abs_tol=.001)
  assert Path(e['file']).name in report
 if x['verdict']!='unknown':
  row=next(row for row in rows if x['id']+' / '+x['model_source'] in row)
  assert any(Path(e['file']).name in row for e in x['evidence'])
print(f'SOFTWARE PASS: {len(expected)}/14 required model features and {len(f)}/{len(f)} comparison rows.')
print(f'SOFTWARE PASS: {len(f)}/{len(f)} feature evidence lists, timestamps, states and evidence labels.')
selected=json.loads((OUT/'source_frames.json').read_text())
assert len(selected)==36 and len({x['file'] for x in selected})==36
for p in sorted((OUT/'sheets').glob('*.jpg')):
 with Image.open(p) as im:
  im.load();assert min(im.size)>500
assert len(list((OUT/'sheets').glob('*.jpg')))==13
print('SOFTWARE PASS: 36 unique indexed frames; 13 readable JPEG sheets.')
for p in OUT.glob('*.py'):compile(p.read_text(),str(p),'exec')
assert '*' not in report and '—' not in report
assert not re.search(r'\b(should|would|may|might|could)\b',report,re.I)
assert '# Questions for the lead' in report
assert all(q+':' in report for q in ['Q1','Q2','Q3','Q4','Q5','Q6','Q7','Q8','Q9'])
print('SOFTWARE PASS: Python syntax and bounded report style tests. No dictionary compliance claim.')
status=subprocess.check_output(['git','status','--porcelain','--untracked-files=all'],cwd=ROOT,text=True)
for line in status.splitlines():assert line[3:].startswith('engineering/layout_audit_01/'),line
branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()
assert branch=='lead/layout-audit-01',branch
print('SOFTWARE PASS: changed paths stay inside OWNS; branch lead/layout-audit-01.')
print('NOT VERIFIED: completed site, final vehicle operations, rail alignment, Blender geometry or new render.')
