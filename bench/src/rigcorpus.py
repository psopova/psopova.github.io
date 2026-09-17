"""Procedural rigged-character corpus + deformation metrics.
Reusable core: any skinning / LOD / weight product is judged by these numbers."""
import bpy, bmesh, math, random
from mathutils import Vector, Euler

BONES = [("pelvis",None,(0,0,1.0),(0,0,1.25)),("spine","pelvis",(0,0,1.25),(0,0,1.55)),
         ("chest","spine",(0,0,1.55),(0,0,1.75)),("neck","chest",(0,0,1.75),(0,0,1.85)),
         ("head","neck",(0,0,1.85),(0,0,2.05)),
         ("upperarm.L","chest",(0.18,0,1.72),(0.52,0,1.72)),("lowerarm.L","upperarm.L",(0.52,0,1.72),(0.82,0,1.72)),
         ("hand.L","lowerarm.L",(0.82,0,1.72),(0.98,0,1.72)),
         ("upperarm.R","chest",(-0.18,0,1.72),(-0.52,0,1.72)),("lowerarm.R","upperarm.R",(-0.52,0,1.72),(-0.82,0,1.72)),
         ("hand.R","lowerarm.R",(-0.82,0,1.72),(-0.98,0,1.72)),
         ("thigh.L","pelvis",(0.12,0,1.0),(0.12,0,0.55)),("shin.L","thigh.L",(0.12,0,0.55),(0.12,0,0.1)),
         ("foot.L","shin.L",(0.12,0,0.1),(0.12,-0.18,0.02)),
         ("thigh.R","pelvis",(-0.12,0,1.0),(-0.12,0,0.55)),("shin.R","thigh.R",(-0.12,0,0.55),(-0.12,0,0.1)),
         ("foot.R","shin.R",(-0.12,0,0.1),(-0.12,-0.18,0.02))]

def build_character(seed=0, subdiv=3, with_shapekeys=True):
    """One rigged humanoid, deterministic per seed. Returns (mesh_obj, armature_obj)."""
    rng = random.Random(seed)
    bpy.ops.object.armature_add(enter_editmode=True, location=(0,0,0))
    arm = bpy.context.object; arm.name = f"rig_{seed:03d}"
    eb = arm.data.edit_bones
    for b in list(eb): eb.remove(b)
    made = {}
    for name, parent, head, tail in BONES:
        b = eb.new(name); b.head = Vector(head); b.tail = Vector(tail)
        if parent: b.parent = made[parent]; b.use_connect = False
        made[name] = b
    bpy.ops.object.mode_set(mode='OBJECT')

    # body: a metaball-ish blob built from boxes, so topology varies with seed
    bpy.ops.object.mode_set(mode='OBJECT')
    bm = bmesh.new()
    segs = [((0,0,1.4),(0.20,0.13,0.40)),((0,0,1.95),(0.12,0.12,0.12)),
            ((0.55,0,1.72),(0.42,0.07,0.07)),((-0.55,0,1.72),(0.42,0.07,0.07)),
            ((0.12,0,0.55),(0.08,0.08,0.46)),((-0.12,0,0.55),(0.08,0.08,0.46))]
    for c,s in segs:
        jitter = 1.0 + rng.uniform(-0.12, 0.12)
        tmp = bmesh.new(); bmesh.ops.create_cube(tmp, size=2.0)
        for v in tmp.verts:
            v.co.x = v.co.x*s[0]*jitter + c[0]; v.co.y = v.co.y*s[1]*jitter + c[1]; v.co.z = v.co.z*s[2]*jitter + c[2]
        bmesh.ops.subdivide_edges(tmp, edges=tmp.edges[:], cuts=subdiv+rng.randint(1,3), use_grid_fill=True)
        me = bpy.data.meshes.new("t"); tmp.to_mesh(me); tmp.free()
        bm.from_mesh(me); bpy.data.meshes.remove(me)
    me = bpy.data.meshes.new(f"body_{seed:03d}"); bm.to_mesh(me); bm.free()
    obj = bpy.data.objects.new(f"char_{seed:03d}", me); bpy.context.scene.collection.objects.link(obj)

    obj.parent = arm
    m = obj.modifiers.new("Armature", 'ARMATURE'); m.object = arm
    bpy.context.view_layer.objects.active = arm
    obj.select_set(True); arm.select_set(True)
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')   # real heat-map skinning

    if with_shapekeys:
        obj.shape_key_add(name="Basis")
        for kn, axis in (("smile", 0), ("blink", 2)):
            k = obj.shape_key_add(name=kn)
            for i, v in enumerate(k.data):
                if v.co.z > 1.85: v.co[axis] += 0.02
    return obj, arm

TEST_POSES = [
    {"upperarm.L": (0, 0, -1.2), "upperarm.R": (0, 0, 1.2)},
    {"thigh.L": (-1.1, 0, 0), "shin.L": (0.9, 0, 0)},
    {"spine": (0.5, 0, 0), "chest": (0.3, 0.4, 0)},
    {"neck": (0, 0, 0.8), "head": (0.4, 0, 0)},
    {"lowerarm.L": (0, 0, -1.5), "lowerarm.R": (0, 0, 1.5), "thigh.R": (-0.8, 0, 0)},
]

def deformed_coords(obj, arm, pose):
    for pb in arm.pose.bones: pb.rotation_euler = Euler((0,0,0)); pb.rotation_mode='XYZ'
    for bone, rot in pose.items():
        pb = arm.pose.bones.get(bone)
        if pb: pb.rotation_mode='XYZ'; pb.rotation_euler = Euler(rot)
    dg = bpy.context.evaluated_depsgraph_get(); dg.update()
    ev = obj.evaluated_get(dg); me = ev.to_mesh()
    co = [v.co.copy() for v in me.vertices]
    ev.to_mesh_clear()
    return co
