"""Head to head: Blender bone heat vs geodesic weighting, same characters, same metric."""
import bpy, sys, time, json, statistics
sys.path.insert(0,"/home/claude/blender-addon/src")
import rigcorpus as rc, metrics as M, failcases as F, geoweight as G
from tests_common import bleed_stats

SEEDS=range(6); rows={"heat":[], "geo":[]}
t0=time.time()
for variant in ("clean","arms_down","ngon_dense"):
    for s in SEEDS:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        obj, arm, failed = F.build(variant, seed=s)
        if failed: continue
        b = bleed_stats(obj, arm); w = M.weight_report(obj, arm)
        rows["heat"].append({"variant":variant, **b, **w})
        G.apply_to(obj, G.compute(obj, arm))
        b2 = bleed_stats(obj, arm); w2 = M.weight_report(obj, arm)
        rows["geo"].append({"variant":variant, **b2, **w2})

print(f"{'variant':>12} {'method':>6} {'torsoBled%':>11} {'maxBleed%':>10} {'orphans':>8} {'unnorm':>7} {'>4infl':>7}")
summary={}
for variant in ("clean","arms_down","ngon_dense"):
    for k in ("heat","geo"):
        r=[x for x in rows[k] if x["variant"]==variant]
        if not r: continue
        m=(round(statistics.mean(x["pct_bled"] for x in r),2), round(max(x["max_bleed_pct"] for x in r),2),
           sum(x["orphans"] for x in r), sum(x["unnormalised"] for x in r), sum(x["over_cap"] for x in r))
        summary[f"{variant}/{k}"]=m
        print(f"{variant:>12} {k:>6} {m[0]:>11} {m[1]:>10} {m[2]:>8} {m[3]:>7} {m[4]:>7}")

print(f"\n{time.time()-t0:.1f}s")
print("HEADLINE, arms at the sides:")
h=summary["arms_down/heat"]; g=summary["arms_down/geo"]
print(f"  bone heat : {h[0]}% of torso vertices bleed, worst {h[1]}% of body height")
print(f"  geodesic  : {g[0]}% of torso vertices bleed, worst {g[1]}% of body height")
if h[0]>0: print(f"  reduction : {round(100*(h[0]-g[0])/h[0],1)}% fewer bleeding vertices")
json.dump(summary, open("/home/claude/blender-addon/ab_result.json","w"), indent=1, default=str)
