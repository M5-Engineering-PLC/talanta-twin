"""Bake Quaternius animation onto Rocketbox bodies for internal H1 evaluation.

World-space anatomical axes align the differently oriented rigs. Each mapped bone
receives its source global rest-to-pose rotation; target rest lengths are retained.
Output is a prototype, requiring pose, feet, and deformation review.
"""
import bpy
from mathutils import Matrix, Vector

BONES = {
    'pelvis': 'Bip01 Pelvis', 'spine_01': 'Bip01 Spine', 'spine_02': 'Bip01 Spine1',
    'spine_03': 'Bip01 Spine2', 'neck_01': 'Bip01 Neck', 'Head': 'Bip01 Head',
}
for side, label in [('l', 'L'), ('r', 'R')]:
    BONES.update({f'clavicle_{side}': f'Bip01 {label} Clavicle', f'upperarm_{side}': f'Bip01 {label} UpperArm',
                  f'lowerarm_{side}': f'Bip01 {label} Forearm', f'hand_{side}': f'Bip01 {label} Hand',
                  f'thigh_{side}': f'Bip01 {label} Thigh', f'calf_{side}': f'Bip01 {label} Calf',
                  f'foot_{side}': f'Bip01 {label} Foot', f'ball_{side}': f'Bip01 {label} Toe0'})
    for finger, index in [('thumb',0), ('index',1), ('middle',2), ('ring',3), ('pinky',4)]:
        for segment in range(1,4):
            suffix = str(index) if segment == 1 else f'{index}{segment-1}'
            BONES[f'{finger}_{segment:02}_{side}'] = f'Bip01 {label} Finger{suffix}'


def anatomical_frame(rig, pelvis, head, left, right):
    def point(name): return rig.matrix_world @ rig.data.bones[name].head_local
    up = (point(head) - point(pelvis)).normalized()
    across = (point(left) - point(right)).normalized()
    forward = across.cross(up).normalized()
    across = up.cross(forward).normalized()
    return Matrix((across, forward, up)).transposed().to_quaternion()


def retarget_actions(source_rig, target_rig, clips=('Idle_Loop', 'Sitting_Idle_Loop')):
    missing = [(s, t) for s, t in BONES.items() if s not in source_rig.data.bones or t not in target_rig.data.bones]
    if missing: raise ValueError(f'Missing mapped bones: {missing}')
    source_frame = anatomical_frame(source_rig, 'pelvis', 'Head', 'upperarm_l', 'upperarm_r')
    target_frame = anatomical_frame(target_rig, 'Bip01 Pelvis', 'Bip01 Head', 'Bip01 L UpperArm', 'Bip01 R UpperArm')
    align = target_frame @ source_frame.inverted()
    def rest_world(rig, name): return rig.matrix_world @ rig.data.bones[name].matrix_local
    source_rest = {s: rest_world(source_rig, s) for s in BONES}
    target_rest = {s: rest_world(target_rig, t) for s, t in BONES.items()}
    # FBX bone tail axes do not reliably point at their child joints. Align the
    # arm segments by joint-head directions, retaining the original bone roll.
    correction = {}
    for side, label in [('l', 'L'), ('r', 'R')]:
        for parent, child, target_parent, target_child in [
            (f'upperarm_{side}', f'lowerarm_{side}', f'Bip01 {label} UpperArm', f'Bip01 {label} Forearm'),
            (f'lowerarm_{side}', f'hand_{side}', f'Bip01 {label} Forearm', f'Bip01 {label} Hand'),
        ]:
            src_dir = (rest_world(source_rig, child).translation - source_rest[parent].translation).normalized()
            dst_dir = (rest_world(target_rig, target_child).translation - target_rest[parent].translation).normalized()
            correction[parent] = dst_dir.rotation_difference(align @ src_dir)

    src_height = (source_rest['Head'].translation - source_rest['pelvis'].translation).length
    dst_height = (target_rest['Head'].translation - target_rest['pelvis'].translation).length
    scale = dst_height / src_height
    # Assign parent bones first; Rocketbox hips are children of Spine rather than Pelvis.
    def depth(name):
        b = target_rig.data.bones[name]; n = 0
        while b.parent: n += 1; b = b.parent
        return n
    ordered = sorted(BONES.items(), key=lambda pair: depth(pair[1]))
    outputs = []
    source_rig.animation_data_create(); target_rig.animation_data_create()
    for clip in clips:
        action = bpy.data.actions.get(clip)
        if action is None: raise ValueError(f'Missing source action: {clip}')
        source_rig.animation_data.action = action
        target_rig.animation_data.action = None
        for pose in target_rig.pose.bones: pose.matrix_basis.identity()
        first, last = (round(v) for v in action.frame_range)
        for frame in range(first, last + 1):
            bpy.context.scene.frame_set(frame)
            for source_name, target_name in ordered:
                source_pose = source_rig.matrix_world @ source_rig.pose.bones[source_name].matrix
                delta = source_pose.to_quaternion() @ source_rest[source_name].to_quaternion().inverted()
                rotation = align @ delta @ align.inverted() @ correction.get(source_name, Matrix.Identity(3).to_quaternion()) @ target_rest[source_name].to_quaternion()
                pose = target_rig.pose.bones[target_name]
                current_world = target_rig.matrix_world @ pose.matrix
                location = current_world.translation.copy()
                if source_name == 'pelvis':
                    displacement = source_pose.translation - source_rest[source_name].translation
                    location = target_rest[source_name].translation + (align @ displacement) * scale
                pose.matrix = target_rig.matrix_world.inverted() @ Matrix.LocRotScale(location, rotation, current_world.to_scale())
                bpy.context.view_layer.update()
                pose.rotation_mode = 'QUATERNION'
                pose.keyframe_insert(data_path='rotation_quaternion', frame=frame, group=target_name)
                if source_name == 'pelvis': pose.keyframe_insert(data_path='location', frame=frame, group=target_name)
        baked = target_rig.animation_data.action
        baked.name = f'{target_rig.name}_{clip}'
        outputs.append(baked)
    return outputs
