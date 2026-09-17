"""Organic humanoid from metaballs, converted and voxel-remeshed to one welded surface."""
import bpy, random
from mathutils import Vector
import rigcorpus as rc

def _blobs(arms_down, rng):
    """BALL elements only. ELLIPSOID with small size values fails to tessellate."""
    j = lambda a=0.07: 1.0 + rng.uniform(-a, a)
    B = []
    # torso: chest -> waist -> hips, tapering
    for z, r, sx, sy in ((1.66,0.175,1.35,0.72),(1.52,0.165,1.30,0.70),(1.38,0.150,1.15,0.66),
                         (1.24,0.145,1.05,0.64),(1.12,0.160,1.20,0.70),(1.02,0.165,1.25,0.74)):
        B.append(((0, 0, z), r*1.78*j(), (sx, sy, 1.0)))
    B += [((0,0,1.80), 0.085*1.9*j(), (0.8,0.8,1.0)),
          ((0,0.01,1.96), 0.145*1.62*j(), (1.0,1.05,1.1))]
    for sx in (1,-1):
        if arms_down:
            pts = [(sx*0.185,0,1.66,0.105),(sx*0.205,0,1.50,0.092),(sx*0.212,0,1.34,0.082),
                   (sx*0.215,0,1.20,0.075),(sx*0.215,0,1.08,0.070),(sx*0.215,-0.01,0.98,0.072)]
        else:
            pts = [(sx*0.28,0,1.71,0.105),(sx*0.44,0,1.72,0.092),(sx*0.60,0,1.72,0.082),
                   (sx*0.74,0,1.72,0.075),(sx*0.86,0,1.72,0.070),(sx*0.95,0,1.72,0.072)]
        for x,y,z,r in pts: B.append(((x,y,z), r*1.46*j(0.05), (1,1,1)))
        for z,r in ((0.92,0.125),(0.78,0.115),(0.62,0.100),(0.46,0.092),(0.30,0.082),(0.14,0.078)):
            B.append(((sx*0.125,0,z), r*1.46*j(0.05), (1,1,1)))
        B.append(((sx*0.115,-0.06,0.06), 0.115, (1,1,1)))
    return B

def build(arms_down=False, seed=0, voxel=0.022):
    rng = random.Random(seed)
    mb = bpy.data.metaballs.new("mb"); mb.resolution = 0.025; mb.render_resolution = 0.025
    ob = bpy.data.objects.new("mb", mb); bpy.context.scene.collection.objects.link(ob)
    for co, rad, sz in _blobs(arms_down, rng):
        e = mb.elements.new(type='BALL')
        e.co = Vector(co); e.radius = rad
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg), depsgraph=dg)
    bpy.data.objects.remove(ob, do_unlink=True)
    if len(me.vertices) == 0: raise RuntimeError("metaball produced no geometry")
    obj = bpy.data.objects.new(f"body_{seed}", me)
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj; obj.select_set(True)
    m = obj.modifiers.new("Remesh",'REMESH'); m.mode='VOXEL'; m.voxel_size=voxel; m.use_smooth_shade=True
    bpy.ops.object.modifier_apply(modifier=m.name)
    return obj

def character(arms_down=False, seed=0):
    import realchar as RC
    arm = RC.rig(arms_down); obj = build(arms_down, seed)
    obj.parent = arm; obj.modifiers.new("Armature",'ARMATURE').object = arm
    bpy.context.view_layer.objects.active = arm; obj.select_set(True); arm.select_set(True)
    failed = False
    try: bpy.ops.object.parent_set(type='ARMATURE_AUTO')
    except Exception: failed = True
    return obj, arm, failed
