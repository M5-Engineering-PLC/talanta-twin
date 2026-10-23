"""Write the proposed plan and comparison table from reviewed evidence."""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
E = {r['id']:r for r in json.loads((OUT/'camera_estimates.json').read_text())}
LF = json.loads((ROOT/'blender/data/layout_final.json').read_text())
GE = json.loads((ROOT/'blender/data/site_layout_ge.json').read_text())
FC = json.loads((ROOT/'blender/data/forecourt_layout.json').read_text())
SP = json.loads((ROOT/'blender/data/site_plan.json').read_text())
FRAMES = {Path(r['file']).name:r for r in json.loads((OUT/'source_frames.json').read_text())}
features=[]

def frame(s):
    return ('JWNowpO44rw_'+s if '_' not in s else s)+'.jpg'

def add(ident,typ,state,centre,size,source,now,seen,verdict,confidence,refs,basis='frame evidence',ring=None,line=None,hold=None):
    ev=[]
    for s in refs:
        n=frame(s);r=FRAMES[n]
        ev.append(dict(file=r['file'],timestamp_s=float(r['timestamp_s']),state=r['state']))
    f=dict(id=ident,type=typ,state=state,approx_centre_m=centre,size_m=size,
       confidence=confidence,evidence=ev,finding_label=basis,
       geometry_note='Approximate software plan. No physical measurement.',
       model_source=source,model_now=now,frames_show=seen,verdict=verdict)
    if ring:f['ring_m']=ring
    if line:f['centreline_m']=line
    if hold:f['questions_for_lead']=hold
    features.append(f)

add('west_road','road','asbuilt',None,None,'layout_final.json:west_road',
 '21 m divided road, x about -156, z -236 to 700.',
 'West apron and work yards are visible. No continuous divided road is established. Ngong Road is the northern divided road.',
 'unknown','low',['000617.567','000714.767','OB0OE-PAAVg_000012.345'],hold='Q1/Q2. Model corridor is not an observed centreline.')
add('railway','railway','finished',[-204,0],None,'layout_final.json:railway',
 'Two tracks on 11 m ballast, x about -204.',
 'No track alignment is resolved in these views. Vegetation and work yards obscure parts of the corridor.',
 'unknown','low',['000617.567','000714.767'],basis='inference',hold='Q1/Q2. Centre is the disputed model location only. Do not build from it.')
add('station','station','finished',[-192,-80],{'platform_model_only':[8.5,240]},'layout_final.json:station',
 '8.5 x 240 m platform and two canopies.',
 'No railway platform is established. Visible roofs alone do not identify a station.',
 'unknown','low',['000617.567','000714.767'],basis='inference',hold='Q1/Q2. Centre and size describe the disputed model only.')
add('footbridge','footbridge','finished',[-175,-146],{'model_span':79},'layout_final.json:footbridge',
 '79 m elevated crossing across new road and railway.',
 'No matching crossing is established. These frames do not prove a later crossing absent.',
 'unknown','low',['000645.000','000714.767'],basis='inference',hold='Q1/Q2. Centre and size describe the disputed model only.')
west=next(e['polygon'] for e in FC['elements'] if e['id']=='west_lawn')
west=[[x,-y] for x,y in west]
add('carpark_north_west','lawn','asbuilt',[-91,-190],{'east_west':68,'north_south':95},'layout_final.json:carpark_north_west',
 'Asphalt over west forecourt, 318 illustrative cars. Lawn and paths hidden.',
 'Grass and red crossed paths west of the north plaza. No car park on this observed lawn.',
 'unknown','high',['000645.000','000659.633','mJJ4Qkl858k_000014.000'],ring=west,
 hold='Q1. Observed lawn is high confidence. Its final retention remains unresolved.')
add('spine_beds','planting','asbuilt',[-58,-190],{'east_west':6,'north_south':66},'layout_final.json:spine_beds',
 '12 m strip at x -64 to -52, z -228 to -148.',
 'Planting borders a lawn and path network. A car park spine is not established.',
 'unknown','medium',['000645.000','000659.633'],hold='Q1. Preserve observed lawn edges until final layout authority is clear.')
add('carpark_south_west','lawn','asbuilt',[-112,178],{'east_west':73,'north_south':106},'layout_final.json:carpark_south_west',
 '72 x 96 m asphalt lot, 207 illustrative cars, pitch and small stand hidden.',
 'A grass rectangle lies inside a paved loop beside a stand. No bays appear on the grass. Sport markings are not resolved.',
 'unknown','high',['000714.767','000716.317','001246.333'],basis='estimate from a camera solve',ring=E['south_west_grass']['ring_m'],
 hold='Q1/Q3. Grass footprint is clear. Finished use and pitch markings need evidence.')
add('road_between_pitches','paved approach','finished',[208,-6],{'width_range':[40,50],'length':165},'layout_final.json:road_between_pitches',
 '8 m asphalt ribbon from [252,-12] to [128,-2]. No central island.',
 'A broad pale approach lies between the eastern sport areas. A long central island splits its surface. It joins the outer apron.',
 'resize','medium',['000617.567','000454.933'],basis='estimate from a camera solve',ring=E['east_approach_envelope']['ring_m'],line=[[290,-13],[220,0],[130,2]],
 hold='Q4. Finished use and vehicle lanes remain unresolved. This is the total paved envelope.')
add('track_ring_ne','track','asbuilt',[171,-120],{'length':166,'width':87},'layout_final.json:track_ring_ne',
 'Dark asphalt track surface in finished state.',
 'The near curved strip is dark while the infield contains soil and equipment. Earlier footage shows red track sections.',
 'unknown','medium',['000617.567','000645.000','LhY5-yDuhfc_000020.000'],hold='Q5. Do not infer final track material from temporary works.')
add('apron_ring','apron','finished',[0,0],{'outward_offset_model':18},'site_layout_ge.json:apron_ring',
 '18 m pale ring outside the plinth.',
 'A continuous pale apron surrounds the bowl. Its width varies at plazas and sport areas.',
 'keep','medium',['000617.567','000714.767'],basis='inference')
T=GE['transform']
def px(pts):return [[round((x-T['px0'])/T['px_per_m'],1),round((z-T['py0'])/T['px_per_m'],1)] for x,z in pts]
add('ge_road_north_east','road','finished',[217,-175],{'width_range':[7,10]},'site_layout_ge.json:roads[0]',
 '9 m road curves north of the track, then follows its east side to z 73.',
 'A curved peripheral route skirts the track and joins the eastern paved approach. It does not run through the north plaza.',
 'keep','medium',['000617.567','000641.633','LhY5-yDuhfc_000020.000'],basis='inference',line=px(GE['roads'][0]['px']))
for i,refs in [(0,['000617.567']),(1,['000617.567','000714.767'])]:
 b=GE['buildings'][i];line=px(b['px_axis']);c=[round(sum(p[k] for p in line)/2,1) for k in [0,1]]
 add(b['name'],'building','asbuilt',c,{'width_model':b['width_m'],'height_model':7},f'site_layout_ge.json:buildings[{i}]',
  f"Plain roof mass, {b['width_m']} m wide and 7 m high.",
  'Long low roofs stand east of the approach. The views support roof masses, but not exact wall heights or final function.',
  'keep','medium',refs,basis='inference',line=line)
add('ge_east_hardstanding','hardstanding','asbuilt',[363,-54],{'east_west_model':163,'north_south_model':259},'site_layout_ge.json:car_parks[0]',
 'Striped asphalt car park with illustrative cars and planted rows.',
 'The east area contains roofs and work space. No complete final bay layout is resolved.',
 'unknown','low',['000617.567','001246.333','000506.533'],ring=px(GE['car_parks'][0]['px']),
 hold='Q6. A filmed design model supports parking intent, not current bay positions.')
add('east_training_pitch','pitch','finished',[189,89],{'east_west':73,'north_south':125},'site_plan.json:pitch_se',
 'Pitch centre [187.6,96.0], footprint 81.5 x 126.1 m.',
 'A rectangular graded sport area lies south of the eastern approach. The filmed design model shows a marked green pitch.',
 'keep','medium',['000617.567','000606.233'],basis='estimate from a camera solve',ring=E['east_training_rectangle']['ring_m'])
add('north_east_track_footprint','track footprint','finished',[171,-120],{'east_west':87,'north_south':166},'site_plan.json:tracks[0]',
 'Track and infield northeast of bowl.',
 'The track location and north-south orientation agree. Construction material covers the infield.',
 'keep','medium',['000617.567','000645.000'],basis='inference')
add('south_west_loop','road','finished',[-112,180],{'width_range':[7,10]},'layout_final.py:KEEP / sw_loop_road',
 'Existing loop survives. Pass F fills its grass interior with cars.',
 'A rounded rectangular paved loop surrounds grass. It bends into the west apron beside the stand.',
 'keep','medium',['000714.767','000716.317'],basis='inference',line=[[-155,238],[-165,180],[-141,116],[-76,123],[-67,185],[-73,240]])
add('south_west_stand','stand','asbuilt',[-180,180],{'length_range':[80,110]},'layout_final.py:hide_finished / sw_stand prefix',
 'Small stand hidden in finished state.',
 'A long roofed stand lies west of the grass rectangle and loop. It is visible in D02.',
 'unknown','medium',['000714.767','000716.317'],hold='Q1/Q3. Do not erase the observed stand without final-state evidence.')
add('north_plaza','plaza','finished',[2,-205],{'east_west_approx':95,'north_south_approx':110},'forecourt_layout.json:elements[id=plaza_edge]',
 'Pale plaza with central round bed and two axial beds.',
 'A pale oval plaza contains a dark circular bed and two long beds. Pedestrian access connects toward Ngong Road.',
 'keep','high',['000645.000','000659.633','mJJ4Qkl858k_000014.000'],basis='inference')
add('south_plaza','plaza','finished',[15,195],{'east_west_range':[80,100],'north_south_range':[100,130]},'ground context visible in step_FF/step_FH renders',
 'Pale plaza and central bed remain.',
 'D02 shows a pale elongated plaza east of the grass loop. It contains a round bed and axial beds.',
 'keep','high',['000714.767','000716.317'],basis='inference')
add('forecourt_paths','path network','finished',[0,-195],{'width_range':[3,5]},'forecourt_layout.json:elements with path_ prefix / layout_final.py:fp_paths',
 'Red paths. West paths hidden below the new car park.',
 'Crossed red paths divide the north lawns. They reach the plaza and skirt the track. The design model also shows these paths.',
 'keep','medium',['000645.000','000659.633','000441.933'],basis='inference',hold='Q1. West paths depend on the disputed car park.')
add('east_approach_island','island','finished',[187,1],{'length':79,'width_range':[20,25]},'no dedicated island in layout_final.json:road_between_pitches',
 'Absent from the 8 m ribbon.',
 'D03 shows a pointed elongated island along the centre of the broad approach.',
 'add','medium',['000617.567'],basis='estimate from a camera solve',ring=E['east_approach_island']['ring_m'])
add('east_approach_flared_join','paved junction','finished',[285,-13],{'envelope_width_range':[40,50]},'layout_final.py:ribbon / lf_road_between_pitches',
 'Constant-width strip stops at [252,-12].',
 'The eastern mouth spreads across the frontage. It joins a peripheral route around the sport areas.',
 'add','medium',['000617.567'],basis='inference',hold='Q4. This is paved connectivity, not a vehicle traffic plan.')
add('apron_approach_join','paved junction','finished',[130,2],{'envelope_width_range':[40,50]},'layout_final.py:ribbon / lf_road_between_pitches',
 '8 m strip ends abruptly against the apron.',
 'The pale approach merges into the outer apron. No road enters the internal arena in this view.',
 'resize','medium',['000617.567','000454.933'],basis='inference')
add('north_frontage','road','asbuilt',[10,-309],{'model_total_width':44.8},'site_plan.json:ngong / road_lines.json:name=Ngong Road',
 'Four lanes each way, 3.3 m each, 2 m median, plus edge and pedestrian strips.',
 'Ngong Road is divided and carries traffic along the north boundary. Perspective does not settle all lane counts or total width.',
 'unknown','medium',['000645.000','HU3J94fa8_c_000650.000'],hold='Q7. Keep existing centreline. Do not certify the four-lane count from this audit.')
add('external_vehicle_access','vehicle access','asbuilt',None,None,'road_lines.json:Cemetery Road / layout_final.json:west_road',
 'Pass F road ends at Ngong Road. The data does not supply a joined final junction.',
 'Footage shows frontage works beside a live road. It does not continuously show a completed turn from Ngong Road into the site.',
 'unknown','low',['HU3J94fa8_c_001334.000','HU3J94fa8_c_001822.000','000645.000'],
 hold='Q7. Relative position: north and west frontage. No final junction coordinates established.')
add('drop_off','drop-off area','finished',None,None,'not identified in layout_final.json or site_layout_ge.json',
 'No dedicated drop-off is specified.',
 'Vehicles and equipment appear on work surfaces. No marked final drop-off or lay-by is resolved.',
 'unknown','low',['000617.567','h--Jmi7SwBs_000058.000'],hold='Q4/Q7. Do not invent a bus loop, lay-by or final stopping point.')
add('west_hardstanding','hardstanding','asbuilt',[-185,45],{'extent_approx':[90,130]},'layout_final.json:west_road / railway / station overlap this region',
 'Straight transport corridor replaces parts of the west context.',
 'D02 shows broad paved work areas northwest of the grass loop. Temporary use does not establish permanent parking.',
 'unknown','medium',['000714.767','OB0OE-PAAVg_000012.345'],hold='Q1/Q2/Q6. Bay layout and finished transport corridor remain unresolved.')
add('forest_belt','tree belt','finished',[0,350],{'depth_range':[40,100]},'site_plan.json:trees / existing context',
 'Southern forest context remains, with generic tree crowns.',
 'A dense forest belt borders the south side. It frames D02 and the L07 foreground.',
 'keep','high',['000714.767','001232.600'],basis='inference')
add('roadside_trees','tree belt','finished',[258,-110],{'row_spacing_model_range':[11,16]},'site_layout_ge.py:road verge tree loop',
 'Two tall tree rows on both verges of the northeast road.',
 'The filmed design model shows regular roadside trees. Live footage shows uneven young planting and mature boundary trees.',
 'unknown','medium',['000612.433','000617.567','KEOmkVfjhu8_001330.000'],hold='Q8. Treat the regular mature avenue as design intent only.')
add('east_lawns_beds','lawn and planting','finished',[82,-220],{'east_west_approx':50,'north_south_approx':155},'forecourt_layout.json:elements[id=east_lawn] / fp_beds',
 'Green lawn panels, red paths and planted beds.',
 'The north-east lawn panels contain grass and triangular red soil beds. The final planting density is unknown.',
 'keep','medium',['000645.000','000659.633','000441.933'],basis='inference')
add('far_track','track','finished',None,None,'absent; layout_final_01/README.md gap 5',
 'No additional far track beyond the eastern pitch.',
 'The design model shows two track ovals in total. A third distant track appears only in the disputed dusk photo.',
 'unknown','low',['000454.933','000617.567'],hold='Q1/Q9. Relative position in photo: beyond eastern sport areas. No supported site coordinates.')

plan=dict(project='Talanta Twin',date='2026-10-23',status='partial finished plan; lead decisions remain',
 evidence_class='software',coordinate_frame='metres; x east, z south; origin W1b pitch centre as in app/cameras/manifest.json',
 coordinate_note='No camera positions are reproduced. Asbuilt entries record observed construction geometry. Finished entries are explicit inferences or unresolved model placeholders.',
 uncertainty=dict(camera_estimates_east_m=20,camera_estimates_south_west_m=25,inherited_ge_trace_m=10,pass_F_near_m=15,pass_F_far_m=30),
 authority_note='No inspected frame establishes the full completed site. A filmed design model is not the finished site. The dusk photo has unresolved provenance.',
 features=features)
(OUT/'layout_plan.json').write_text(json.dumps(plan,indent=2)+'\n')
rows=['| Feature | Model now | Drone frames show | Verdict | Confidence | Evidence |','|---|---|---|---|---|---|']
for f in features:
 ev=[]
 for e in f['evidence']:
  n=Path(e['file']).name;t=e['timestamp_s'];ev.append(f'{n} ({int(t//60):02}:{t%60:06.3f})')
 rows.append('| '+ ' | '.join([f['id']+' / '+f['model_source'],f['model_now'],f['finding_label']+': '+f['frames_show'],f['verdict'],f['confidence'],'<br>'.join(ev)])+' |')
(OUT/'comparison_table.md').write_text('\n'.join(rows)+'\n')
print('SOFTWARE:',len(features),'plan features; 14 mandatory model features covered.')
