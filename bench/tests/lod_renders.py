import bpy, sys, numpy as np
sys.path.insert(0,"/home/claude/blender-addon/src")
import organic as O, lodgen as L, viz as V
OUT="/home/claude/blender-addon/out/"

def wire_material(obj, base=(0.16,0.19,0.26), wire=(0.95,0.55,0.22)):
    mat=bpy.data.materials.new("w"); mat.use_nodes=True
    nt=mat.node_tree; nt.nodes.clear()
    out=nt.nodes.new("ShaderNodeOutputMaterial")
    mix=nt.nodes.new("ShaderNodeMixShader")
    d=nt.nodes.new("ShaderNodeEmission"); d.inputs[0].default_value=(*base,1); d.inputs[1].default_value=1.0
    e=nt.nodes.new("ShaderNodeEmission"); e.inputs[0].default_value=(*wire,1); e.inputs[1].default_value=1.6
    w=nt.nodes.new("ShaderNodeWireframe"); w.use_pixel_size=True; w.inputs[0].default_value=1.1
    nt.links.new(w.outputs[0], mix.inputs[0]); nt.links.new(d.outputs[0], mix.inputs[1])
    nt.links.new(e.outputs[0], mix.inputs[2]); nt.links.new(mix.outputs[0], out.inputs[0])
    obj.data.materials.clear(); obj.data.materials.append(mat)

bpy.ops.wm.read_factory_settings(use_empty=True)
src,arm,_ = O.character(arms_down=True, seed=2)
src.shape_key_add(name="Basis")
k=src.shape_key_add(name="bulge")
for i,v in enumerate(k.data):
    if v.co.z>1.35: v.co.y+=0.055
src.data.calc_loop_triangles(); st=len(src.data.loop_triangles)
V.setup_camera(src)
counts=[]
for i,(label,frac) in enumerate([("LOD0",1.0),("LOD1",0.5),("LOD2",0.25),("LOD3",0.10)]):
    for o in list(bpy.context.scene.objects):
        if o.name.endswith("_LOD"): bpy.data.objects.remove(o, do_unlink=True)
    if frac==1.0:
        tgt=src; src.hide_render=False
    else:
        tgt=L.build_lod(src,arm,target_tris=int(st*frac)); src.hide_render=True; tgt.hide_render=False
    tgt.data.calc_loop_triangles(); n=len(tgt.data.loop_triangles); counts.append((label,n))
    wire_material(tgt)
    V.render(f"{OUT}lod_{i}.png", 520, 940)
    if frac!=1.0: tgt.hide_render=True
    print(f"{label}: {n:,} tris")
print("COUNTS", counts)
import json; json.dump(counts, open(OUT+"lod_counts.json","w"))
