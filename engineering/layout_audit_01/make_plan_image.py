"""Internal schematic from numeric model data and audit estimates."""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
P=json.loads((OUT/'layout_plan.json').read_text())
F={f['id']:f for f in P['features']}
M=json.loads((ROOT/'blender/data/layout_final.json').read_text())
I=Image.new('RGB',(1250,1330),'#f6f5ef');d=ImageDraw.Draw(I)
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
big=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',26)
orange='#bf6028';blue='#1469a0';grey='#666666'
def xy(p):return (round(390+p[0]*1.45),round(610+p[1]*1.45))
def ring(p,col,width=4):d.line([xy(q) for q in p+[p[0]]],fill=col,width=width)
def line(p,col,width=3):d.line([xy(q) for q in p],fill=col,width=width)
def label(p,s,col=grey):d.text(xy(p),s,font=font,fill=col)
d.text((28,20),'Talanta layout audit | schematic only | internal',font=big,fill='#222222')
d.text((28,60),'Orange: disputed pass F model. Blue: frame footprint or inferred continuation.',font=font,fill=grey)
d.text((28,88),'Blue does not establish a completed site. Transport corridor remains unresolved.',font=font,fill=grey)
for x in [-200,-100,0,100,200,300,400]:
 line([[x,-310],[x,330]],'#dddddd',1);label([x,-328],str(x))
for z in [-300,-200,-100,0,100,200,300]:
 line([[-240,z],[450,z]],'#dddddd',1);label([-263,z],str(z))
d.rounded_rectangle([xy([-107,-128]),xy([107,128])],radius=70,fill='#deded7',outline=grey,width=3)
d.rectangle([xy([-34,-52]),xy([34,52])],outline=grey,width=2)
label([-53,-20],'BOWL')
ring(M['carpark_north_west']['ring'],orange)
ring(M['carpark_south_west']['ring'],orange)
line(M['road_between_pitches']['centre'],orange,12)
line(M['west_road']['centre'][:5],orange,5)
line(M['railway']['centre'][:5],orange,3)
for k in ['carpark_north_west','carpark_south_west','road_between_pitches','east_approach_island','east_training_pitch']:
 ring(F[k]['ring_m'],blue)
line(F['ge_road_north_east']['centreline_m'],blue,4)
line(F['south_west_loop']['centreline_m']+[F['south_west_loop']['centreline_m'][0]],blue,3)
d.rounded_rectangle([xy([127,-203]),xy([215,-37])],radius=40,outline=blue,width=4)
line([[-225,-217],[30,-310]],grey,5)
label([-100,-286],'Ngong Road')
label([-134,-190],'1',blue);label([-120,168],'2',blue)
label([250,4],'3',blue);label([183,-4],'4',blue)
label([155,-115],'5',blue);label([175,90],'6',blue)
label([-237,10],'?',orange)
label([-220,300],'South forest belt')
label([420,-300],'N')
line([[430,-270],[430,-295]],grey,3)
line([[420,-283],[430,-295],[440,-283]],grey,3)
line([[285,300],[385,300]],grey,4);label([288,312],'100 m')
d.text((28,1120),'1 North-west lawn with crossed paths. Final car park decision: Q1.',font=font,fill=blue)
d.text((28,1150),'2 South-west grass inside loop. Sport markings unresolved. Final use: Q1/Q3.',font=font,fill=blue)
d.text((28,1180),'3 Broad east paved approach. 4 Central island. Vehicle lanes and drop-off: Q4.',font=font,fill=blue)
d.text((28,1210),'5 Northeast track footprint. 6 Eastern training rectangle.',font=font,fill=blue)
d.text((28,1240),'? West road, rail, station and crossing: unresolved. Do not use as final geometry.',font=font,fill=orange)
d.text((28,1280),'Coordinates: metres, x east, z south. Approximate plan. No physical measurement.',font=font,fill=grey)
I.save(OUT/'sheets/13_plan.jpg',quality=92)
print('SOFTWARE: schematic saved to sheets/13_plan.jpg')
