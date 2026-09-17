"""A single WELDED continuous body surface, built from metaballs then remeshed.
Box unions have disconnected shells, which makes geodesic distance meaningless
and any benchmark built on them worthless."""
import bpy, random
from mathutils import Vector
import rigcorpus as rc

def _mb(name, blobs, res=0.045):
    mb = bpy.data.metaballs.new(name); mb.resolution = res; mb.render_resolution = res
    ob = bpy.data.objects.new(name, mb); bpy.context.scene.collection.objects.link(ob)
    for co, rad, sz in blobs:
        e = mb.elements.new(); e.co = Vector(co); e.radius = rad
        e.type = 'ELLIPSOID'; e.size_x, e.size_y, e.size_z = sz
    return ob

def build(arms_down=False, seed=0, voxel=0.030):
    """Box union, then VOXEL REMESH, which welds everything into ONE continuous
    manifold surface. That is what makes geodesic distance meaningful."""
    import bmesh, failcases as F
    rng = random.Random(seed)
    segs = F._segs(arm_down=arms_down)
    me = F._mesh_from_boxes(f"body_{seed}", segs, 2, rng)
    obj = bpy.data.objects.new(f"body_{seed}", me)
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    m = obj.modifiers.new("Remesh", 'REMESH')
    m.mode = 'VOXEL'; m.voxel_size = voxel; m.use_smooth_shade = False
    bpy.ops.object.modifier_apply(modifier=m.name)
    return obj

def rig(arms_down=False):
    bpy.ops.object.armature_add(enter_editmode=True, location=(0,0,0))
    arm = bpy.context.object; arm.name="rig"; eb = arm.data.edit_bones
    for b in list(eb): eb.remove(b)
    made={}
    for name,parent,head,tail in rc.BONES:
        b=eb.new(name); b.head=Vector(head); b.tail=Vector(tail)
        if parent: b.parent=made[parent]; b.use_connect=False
        made[name]=b
    if arms_down:
        for side,sx in (("L",1),("R",-1)):
            made[f"upperarm.{side}"].head=Vector((sx*0.16,0,1.70)); made[f"upperarm.{side}"].tail=Vector((sx*0.21,0,1.40))
            made[f"lowerarm.{side}"].head=Vector((sx*0.21,0,1.40)); made[f"lowerarm.{side}"].tail=Vector((sx*0.21,0,1.12))
            made[f"hand.{side}"].head=Vector((sx*0.21,0,1.12));     made[f"hand.{side}"].tail=Vector((sx*0.21,0,0.99))
    bpy.ops.object.mode_set(mode='OBJECT')
    return arm

def character(arms_down=False, seed=0):
    arm = rig(arms_down); obj = build(arms_down, seed)
    obj.parent = arm; obj.modifiers.new("Armature",'ARMATURE').object = arm
    bpy.context.view_layer.objects.active = arm; obj.select_set(True); arm.select_set(True)
    failed=False
    try: bpy.ops.object.parent_set(type='ARMATURE_AUTO')
    except Exception: failed=True
    return obj, arm, failed
