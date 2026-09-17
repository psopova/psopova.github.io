import bpy, sys, numpy as np, json
sys.path.insert(0,"/home/claude/blender-addon/src"); sys.path.insert(0,"/home/claude/blender-addon/tests")
import organic as O, geoweight as G, metrics as M, viz as V, realchar as R
OUT="/home/claude/blender-addon/out/"

def wmap(obj, bone):
    idx={g.name:g.index for g in obj.vertex_groups}.get(bone)
    w=np.zeros(len(obj.data.vertices))
    if idx is None: return w
    for i,v in enumerate(obj.data.vertices):
        for g in v.groups:
            if g.group==idx: w[i]=g.weight
    return w

def bleedmap(obj, arm, bone="upperarm.L", ang=1.2):
    rest=R.rc.deformed_coords(obj,arm,{}); pos=R.rc.deformed_coords(obj,arm,{bone:(0,0,-ang)})
    h=obj.dimensions.z or 1.0
    d=np.array([(pos[i]-rest[i]).length/h for i in range(len(rest))])
    torso=np.array([abs(v.co.x)<0.14 and 1.15<v.co.z<1.72 for v in obj.data.vertices])
    return np.where(torso,d,0.0)

SCALE = {}
for meth in ("heat","geo"):
    for kind in ("weight","bleed"):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        o,a,f=O.character(arms_down=True, seed=2)
        if meth=="geo":
            G.apply_to(o, G.compute(o,a,falloff=10.0,exclusive_seeds=False,smooth_iters=40,smooth_lambda=0.6))
        vals = wmap(o,"upperarm.L") if kind=="weight" else bleedmap(o,a)
        # fixed scale across both methods so the images are actually comparable
        key=kind
        if key not in SCALE: SCALE[key]=float(vals.max())
        vv=np.clip(vals/max(SCALE[key],1e-9),0,1)
        vv[0]=0.0; vv[1]=1.0            # pin the ramp
        V.paint(o, vv)
        V.setup_camera(o); V.render(f"{OUT}pf_{kind}_{meth}.png", 760, 1000)
        print(f"{kind}_{meth}: max={vals.max():.4f}  (scale {SCALE[key]:.4f})")
json.dump(SCALE, open(OUT+"render_scales.json","w"))
