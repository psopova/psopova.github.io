import bpy, sys, numpy as np
sys.path.insert(0,"/home/claude/blender-addon/src"); sys.path.insert(0,"/home/claude/blender-addon/tests")
import organic as O, keytransfer as K, viz as V
from keytransfer_bench import apply_shape, SHAPES, arrays
OUT="/home/claude/blender-addon/out/"
bpy.ops.wm.read_factory_settings(use_empty=True)
donor,_,_ = O.character(arms_down=False, seed=1)
tgt=donor.copy(); tgt.data=donor.data.copy(); tgt.name="t"
bpy.context.scene.collection.objects.link(tgt)
bpy.context.view_layer.objects.active=tgt; tgt.select_set(True)
m=tgt.modifiers.new("R",'REMESH'); m.mode='VOXEL'; m.voxel_size=0.017
bpy.ops.object.modifier_apply(modifier=m.name)
Ps=arrays(donor.data); Pd=arrays(tgt.data)
scale=float(np.linalg.norm(Ps.max(0)-Ps.min(0)))
spec=SHAPES["head_turn"]
src_key=apply_shape(Ps,spec); truth=apply_shape(Pd,spec)
fields={}
fields["ours"]=np.linalg.norm(K.transfer(donor.data,src_key,tgt.data)-truth,axis=1)/scale*100
fields["base"]=np.linalg.norm(K.surface_deform_style(donor.data,src_key,tgt.data)-truth,axis=1)/scale*100
hi=float(max(f.max() for f in fields.values()))
print("shared colour scale max:", round(hi,4), "% of body height")
donor.hide_render=True
V.setup_camera(tgt)
bpy.context.scene.camera.data.ortho_scale=1.1
bpy.context.scene.camera.location=(0.0,-6.0,1.86)
for name,f in fields.items():
    v=np.clip(f/hi,0,1); v[0]=0.0; v[1]=1.0
    V.paint(tgt,v); V.render(f"{OUT}kt_{name}.png", 700, 760)
    print(f"kt_{name}.png  max err {f.max():.4f}%  mean {f.mean():.4f}%")
