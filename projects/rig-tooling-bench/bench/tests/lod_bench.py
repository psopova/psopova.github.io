import bpy, sys, numpy as np, statistics, json, time
sys.path.insert(0,"/home/claude/blender-addon/src")
import organic as O, lodgen as L, metrics as M, rigcorpus as rc
from scipy.spatial import cKDTree

LEVELS=[("LOD1",0.50),("LOD2",0.25),("LOD3",0.12)]
USE_BUDGET=True
POSES=rc.TEST_POSES[:3]

def add_keys(o):
    o.shape_key_add(name="Basis")
    for nm,ax,zc in (("bulge",1,1.4),("taper",0,0.9),("lift",2,1.8)):
        k=o.shape_key_add(name=nm)
        for i,v in enumerate(k.data):
            if v.co.z>zc: v.co[ax]+= 0.04
    return o

def deform_err(base_obj, base_arm, lod_obj, h):
    """Nearest-point displacement difference between LOD0 and LODk, across poses.

    The KD-tree MUST be rebuilt for every pose. Building it once from pose 0 and
    reusing it compares later poses against the wrong base geometry, which inflated
    this figure 17x in the first version and hid the real degradation between levels.
    An independent audit caught it."""
    errs=[]
    for p in POSES:
        b=rc.deformed_coords(base_obj, base_arm, p)
        l=rc.deformed_coords(lod_obj, base_arm, p)
        b=np.array([tuple(x) for x in b]); l=np.array([tuple(x) for x in l])
        tree=cKDTree(b)                      # rebuilt per pose
        d,_=tree.query(l, k=1)
        errs.append(100*float(np.mean(d))/h)
    return round(statistics.mean(errs),3)

t0=time.time(); rows=[]; blender_fail=0
for s in range(4):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    o,a,f=O.character(arms_down=True, seed=s)
    if f: continue
    add_keys(o)
    o.data.calc_loop_triangles(); src_tris=len(o.data.loop_triangles); src_polys=len(o.data.polygons); src_keys=len(o.data.shape_keys.key_blocks); src_groups=len(o.vertex_groups)
    h=o.dimensions.z or 1.0

    # what Blender itself does
    try:
        bpy.context.view_layer.objects.active=o
        m=o.modifiers.new("D",'DECIMATE'); m.ratio=0.5
        bpy.ops.object.modifier_apply(modifier=m.name)
    except Exception:
        blender_fail+=1
        o.modifiers.remove(o.modifiers["D"])

    for name,ratio in LEVELS:
        lod=L.build_lod(o,a,target_tris=int(src_tris*ratio))
        lod.data.calc_loop_triangles()
        w=M.weight_report(lod,a)
        sk=lod.data.shape_keys
        rows.append({"seed":s,"level":name,"target":int(src_tris*ratio),"polys":len(lod.data.loop_triangles),
            "groups":len(lod.vertex_groups),"keys":len(sk.key_blocks) if sk else 0,
            "unnorm":w["unnormalised"],"over4":w["over_cap"],"orphan":w["orphans"],
            "err":deform_err(o,a,lod,h)})
        bpy.data.objects.remove(lod, do_unlink=True)

FAILED=[]
def check(cond, msg):
    if not cond: FAILED.append(msg)

for r in rows:
    check(abs(r["polys"]-r["target"])/r["target"] < 0.05, f"{r['level']} seed{r['seed']}: budget missed by >5%")
    check(r["unnorm"]==0 and r["over4"]==0 and r["orphan"]==0, f"{r['level']} seed{r['seed']}: broken weights")
    check(r["keys"]==4 and r["groups"]==17, f"{r['level']} seed{r['seed']}: lost groups or keys")
    check(r["err"] < 1.0, f"{r['level']} seed{r['seed']}: deform error {r['err']}% too high")
# levels must actually degrade; if they do not, the metric is not measuring anything
byl={n:[x["err"] for x in rows if x["level"]==n] for n,_ in LEVELS}
check(statistics.mean(byl["LOD3"]) > statistics.mean(byl["LOD1"])*1.3,
      "LOD3 error not meaningfully worse than LOD1: the metric is probably broken")
print(f"ASSERTIONS: {len(FAILED)} failed" + ("" if not FAILED else " -> " + "; ".join(FAILED[:4])))
assert not FAILED, FAILED[:4]

print(f"Blender's own Decimate on a shape-keyed character: FAILED on {blender_fail}/4 (it refuses outright)\n")
print(f"{'level':>6} {'tgt tris':>9} {'got tris':>9} {'budget err':>11} {'groups':>7} {'keys':>5} {'unnorm':>7} {'over4':>6} {'orphan':>7} {'deform err %':>13}")
agg={}
for name,_ in LEVELS:
    r=[x for x in rows if x["level"]==name]
    be=statistics.mean(abs(x["polys"]-x["target"])/x["target"] for x in r)*100
    a_={"target":int(statistics.mean(x["target"] for x in r)),"polys":int(statistics.mean(x["polys"] for x in r)),
        "budget_err":round(be,1),"groups":min(x["groups"] for x in r),"keys":min(x["keys"] for x in r),
        "unnorm":sum(x["unnorm"] for x in r),"over4":sum(x["over4"] for x in r),"orphan":sum(x["orphan"] for x in r),
        "err":round(statistics.mean(x["err"] for x in r),3)}
    agg[name]=a_
    print(f"{name:>6} {a_['target']:>8,} {a_['polys']:>8,} {a_['budget_err']:>10.1f}% {a_['groups']:>7} {a_['keys']:>5} {a_['unnorm']:>7} {a_['over4']:>6} {a_['orphan']:>7} {a_['err']:>13}")
print(f"\nsource: 4 characters, 4 shape keys and 17 vertex groups each")
print(f"{len(rows)} LOD builds with full metrics in {time.time()-t0:.1f}s")
json.dump({"blender_fail":blender_fail,"levels":agg}, open("/home/claude/blender-addon/out/lod_bench.json","w"), indent=1)
