"""Prove the suite now rejects a bind that scores perfectly but does nothing."""
import bpy, sys, numpy as np, statistics
sys.path.insert(0,"/home/claude/blender-addon/src"); sys.path.insert(0,"/home/claude/blender-addon/tests")
import organic as O, geoweight as G, metrics as M, realchar as R
from tests_common import bleed_stats, motion_check

def jag(o,a,bone="lowerarm.L",ang=1.4):
    rest=R.rc.deformed_coords(o,a,{}); pos=R.rc.deformed_coords(o,a,{bone:(0,0,-ang)})
    h=o.dimensions.z or 1.0; d=[(pos[i]-rest[i]).length/h for i in range(len(rest))]
    return 100*float(np.percentile([abs(d[e.vertices[0]]-d[e.vertices[1]]) for e in o.data.edges],99))

def statue(obj, arm):
    """The cheat: every vertex 100% on the pelvis. Perfect scores, zero deformation."""
    for g in list(obj.vertex_groups): obj.vertex_groups.remove(g)
    g = obj.vertex_groups.new(name="pelvis")
    g.add(list(range(len(obj.data.vertices))), 1.0, 'REPLACE')

print(f"{'bind':>22} {'bled%':>7} {'jag':>6} {'limb moved%':>12} {'verdict':>10}")
LIMB_MIN = 1.0   # a real bind must move the limb by at least this much
for label, fn in (("Blender bone heat", None), ("geodesic (ours)", "geo"), ("CHEAT: pelvis statue", "statue")):
    B=[];J=[];LM=[]
    for s in range(3):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        o,a,f = O.character(arms_down=True, seed=s)
        if f: continue
        if fn=="geo": G.apply_to(o, G.compute(o,a,falloff=10.0,exclusive_seeds=False,smooth_iters=40,smooth_lambda=0.6))
        elif fn=="statue": statue(o,a)
        B.append(bleed_stats(o,a)["pct_bled"]); J.append(jag(o,a)); LM.append(motion_check(o,a)["limb_moved_pct"])
    b,j,lm = statistics.mean(B), statistics.mean(J), statistics.mean(LM)
    ok = lm >= LIMB_MIN
    print(f"{label:>22} {b:>7.2f} {j:>6.2f} {lm:>12.3f} {'PASS' if ok else 'REJECTED':>10}")
print(f"\nGate: a bind must move the limb at least {LIMB_MIN}% of body height.")
print("The statue wins on every previously published metric and is now rejected outright.")
