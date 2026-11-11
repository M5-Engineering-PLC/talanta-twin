import bpy,sys,os,pathlib,math
sys.path.insert(0,os.path.abspath('blender/people'))
from retarget import anatomical_frame
args = sys.argv[sys.argv.index('--') + 1:]
if len(args) < 2: raise SystemExit('Usage: blender --background --python retarget_test.py -- <prototype.blend> <source.glb> [target names...]')
p = pathlib.Path(args[0]); names = args[2:] or ['Female_Adult_01', 'Male_Adult_01']
bpy.ops.wm.open_mainfile(filepath=str(p));scene=bpy.context.scene
before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(pathlib.Path(args[1])));source, = (obj for obj in set(bpy.data.objects)-before if obj.type == 'ARMATURE')
for name in names:
 target=bpy.data.objects[name];target.animation_data.use_nla=False
 q=anatomical_frame(target,'Bip01 Pelvis','Bip01 Head','Bip01 L UpperArm','Bip01 R UpperArm')@anatomical_frame(source,'pelvis','Head','upperarm_l','upperarm_r').inverted()
 for clip in ['Idle_Loop','Sitting_Idle_Loop']:
  source.animation_data.action=bpy.data.actions[clip];target.animation_data.action=bpy.data.actions[name+'_'+clip]; end=round(source.animation_data.action.frame_range[1]);angles=[]; hand_positions=[]
  for f in [0,end//4,end//2,3*end//4,end]:
   scene.frame_set(f);bpy.context.view_layer.update();hand_positions.append(target.matrix_world@target.pose.bones['Bip01 L Hand'].head)
   for side,label in [('l','L'),('r','R')]:
    for a,b,x,y in [(f'upperarm_{side}',f'lowerarm_{side}',f'Bip01 {label} UpperArm',f'Bip01 {label} Forearm'),(f'lowerarm_{side}',f'hand_{side}',f'Bip01 {label} Forearm',f'Bip01 {label} Hand')]:
     sd=(source.matrix_world@source.pose.bones[b].head-source.matrix_world@source.pose.bones[a].head).normalized();td=(target.matrix_world@target.pose.bones[y].head-target.matrix_world@target.pose.bones[x].head).normalized();angles.append(math.degrees((q@sd).angle(td)))
  motion=max((a-b).length for a in hand_positions for b in hand_positions)
  print(name,clip,'max_angle_deg',round(max(angles),3),'hand_range_m',round(motion,4));assert max(angles)<2;assert motion>.001
print(f'PASS {len(names) * 40} arm-direction samples across {len(names) * 2} target clips')
