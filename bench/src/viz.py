"""Render weight maps and bleed maps. Vertex colours + flat emission = fast and legible."""
import bpy, numpy as np
from mathutils import Vector

RAMP = [(0.05,0.05,0.12),(0.10,0.25,0.65),(0.10,0.70,0.75),(0.55,0.85,0.30),(1.00,0.85,0.15),(1.00,0.35,0.10)]
def _ramp(t):
    t = float(np.clip(t,0,1))*(len(RAMP)-1); i=int(t); f=t-i
    a=RAMP[i]; b=RAMP[min(i+1,len(RAMP)-1)]
    return tuple(a[k]+(b[k]-a[k])*f for k in range(3))+(1.0,)

def paint(obj, values, name="viz"):
    v = np.asarray(values, dtype=float)
    lo, hi = float(v.min()), float(v.max())
    v = (v-lo)/(hi-lo) if hi>lo else v*0
    me = obj.data
    ca = me.color_attributes.get(name) or me.color_attributes.new(name=name, type='FLOAT_COLOR', domain='POINT')
    for i in range(len(me.vertices)): ca.data[i].color = _ramp(v[i])
    me.color_attributes.active_color = ca
    mat = bpy.data.materials.new("viz"); mat.use_nodes = True
    nt = mat.node_tree; nt.nodes.clear()
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    e = nt.nodes.new("ShaderNodeEmission"); e.inputs[1].default_value = 1.0
    c = nt.nodes.new("ShaderNodeVertexColor"); c.layer_name = name
    nt.links.new(c.outputs[0], e.inputs[0]); nt.links.new(e.outputs[0], o.inputs[0])
    obj.data.materials.clear(); obj.data.materials.append(mat)
    return lo, hi

def setup_camera(target, w=1200, h=600, front=True):
    s = bpy.context.scene
    s.render.engine = 'CYCLES'; s.cycles.samples = 24; s.cycles.use_denoising = True
    s.render.resolution_x = w; s.render.resolution_y = h
    s.render.film_transparent = False
    s.world = s.world or bpy.data.worlds.new("W"); s.world.use_nodes = True
    s.world.node_tree.nodes["Background"].inputs[0].default_value = (0.03,0.03,0.045,1)
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    s.collection.objects.link(cam); s.camera = cam
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = 2.6
    cam.location = (0.0, -6.0, 1.05) if front else (5.0,-5.0,2.0)
    cam.rotation_euler = (1.5708, 0, 0) if front else (1.15, 0, 0.785)
    return cam

def render(path, w=1200, h=600):
    s = bpy.context.scene
    s.render.resolution_x = w; s.render.resolution_y = h
    s.render.filepath = path; s.render.image_settings.file_format = 'PNG'
    bpy.ops.render.render(write_still=True)
