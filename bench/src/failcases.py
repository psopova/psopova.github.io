"""Realistic characters that break Blender's bone-heat weighting.
Each variant is a thing artists actually make, not a synthetic torture test."""
import bpy, bmesh, random
from mathutils import Vector
import rigcorpus as rc

def _mesh_from_boxes(name, segs, subdiv, rng):
    bm = bmesh.new()
    for c, s in segs:
        j = 1.0 + rng.uniform(-0.1, 0.1)
        t = bmesh.new(); bmesh.ops.create_cube(t, size=2.0)
        for v in t.verts:
            v.co.x = v.co.x*s[0]*j + c[0]; v.co.y = v.co.y*s[1]*j + c[1]; v.co.z = v.co.z*s[2]*j + c[2]
        bmesh.ops.subdivide_edges(t, edges=t.edges[:], cuts=subdiv, use_grid_fill=True)
        me = bpy.data.meshes.new("t"); t.to_mesh(me); t.free(); bm.from_mesh(me); bpy.data.meshes.remove(me)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); return me

# torso, head, two arms, two legs.  arm_y shifts arms toward/away from the body.
def _segs(arm_gap=0.0, arm_down=False):
    arms = ([((0.55, arm_gap, 1.72),(0.42,0.07,0.07)), ((-0.55, arm_gap, 1.72),(0.42,0.07,0.07))]
            if not arm_down else
            [((0.20, arm_gap, 1.35),(0.07,0.07,0.40)), ((-0.20, arm_gap, 1.35),(0.07,0.07,0.40))])
    return [((0,0,1.4),(0.20,0.13,0.40)), ((0,0,1.95),(0.12,0.12,0.12))] + arms + \
           [((0.12,0,0.55),(0.08,0.08,0.46)), ((-0.12,0,0.55),(0.08,0.08,0.46))]

VARIANTS = {
 "clean":        dict(note="T-pose, arms clear of the body"),
 "arms_down":    dict(note="arms at the sides, 0.08 from the torso. the single most common character pose"),
 "loose_parts":  dict(note="character plus a separate belt object, one mesh, two shells"),
 "open_mesh":    dict(note="faces deleted at the wrists, an open non-watertight mesh"),
 "ngon_dense":   dict(note="dense mesh with n-gons, as a sculpt retopo often is"),
}

def build(variant, seed=0):
    rng = random.Random(seed)
    bpy.ops.object.armature_add(enter_editmode=True, location=(0,0,0))
    arm = bpy.context.object; arm.name = "rig"
    eb = arm.data.edit_bones
    for b in list(eb): eb.remove(b)
    made = {}
    for name, parent, head, tail in rc.BONES:
        b = eb.new(name); b.head = Vector(head); b.tail = Vector(tail)
        if parent: b.parent = made[parent]; b.use_connect = False
        made[name] = b
    if variant == "arms_down":
        for side, sx in (("L",1),("R",-1)):
            made[f"upperarm.{side}"].head=Vector((sx*0.18,0,1.70)); made[f"upperarm.{side}"].tail=Vector((sx*0.20,0,1.40))
            made[f"lowerarm.{side}"].head=Vector((sx*0.20,0,1.40)); made[f"lowerarm.{side}"].tail=Vector((sx*0.20,0,1.10))
            made[f"hand.{side}"].head=Vector((sx*0.20,0,1.10));     made[f"hand.{side}"].tail=Vector((sx*0.20,0,0.98))
    bpy.ops.object.mode_set(mode='OBJECT')

    down = variant == "arms_down"
    me = _mesh_from_boxes("body", _segs(arm_down=down), 3 + rng.randint(0,1), rng)
    obj = bpy.data.objects.new("char", me); bpy.context.scene.collection.objects.link(obj)

    bm = bmesh.new(); bm.from_mesh(obj.data)
    if variant == "loose_parts":
        t = bmesh.new(); bmesh.ops.create_cube(t, size=2.0)
        for v in t.verts: v.co.x*=0.24; v.co.y*=0.17; v.co.z=v.co.z*0.05+1.02
        bmesh.ops.subdivide_edges(t, edges=t.edges[:], cuts=3, use_grid_fill=True)
        m2 = bpy.data.meshes.new("belt"); t.to_mesh(m2); t.free(); bm.from_mesh(m2); bpy.data.meshes.remove(m2)
    elif variant == "open_mesh":
        bm.faces.ensure_lookup_table()
        doomed = [f for f in bm.faces if abs(f.calc_center_median().x) > 0.85]
        bmesh.ops.delete(bm, geom=doomed, context='FACES')
    elif variant == "ngon_dense":
        bmesh.ops.dissolve_limit(bm, angle_limit=0.02, verts=bm.verts[:], edges=bm.edges[:])
        bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=1, use_grid_fill=True)
    bm.to_mesh(obj.data); bm.free()

    obj.parent = arm
    obj.modifiers.new("Armature", 'ARMATURE').object = arm
    bpy.context.view_layer.objects.active = arm
    obj.select_set(True); arm.select_set(True)
    try:
        bpy.ops.object.parent_set(type='ARMATURE_AUTO'); failed = False
    except Exception:
        failed = True
    return obj, arm, failed
