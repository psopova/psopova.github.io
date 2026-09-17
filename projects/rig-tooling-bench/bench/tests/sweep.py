import bpy, sys, time, statistics, itertools, json
sys.path.insert(0,"/home/claude/blender-addon/src"); sys.path.insert(0,"/home/claude/blender-addon/tests")
import metrics as M, failcases as F, geoweight as G
from tests_common import bleed_stats
SEEDS=range(5); t0=time.time(); res={}
base={}
for v in ("clean","arms_down","ngon_dense"):
    acc=[]
    for s in SEEDS:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        o,a,f=F.build(v,seed=s)
        if not f: acc.append(bleed_stats(o,a))
    base[v]=(round(statistics.mean(x["pct_bled"] for x in acc),2), round(max(x["max_bleed_pct"] for x in acc),2))
print("bone heat baseline:", base)
grid=list(itertools.product([True,False],[0.0,0.15],[3.0,5.0,8.0]))
print(f"\n{'excl':>5} {'bias':>5} {'falloff':>7} " + " ".join(f"{v:>12}" for v in base))
for excl,bias,fo in grid:
    row=[]
    for v in ("clean","arms_down","ngon_dense"):
        acc=[]
        for s in SEEDS:
            bpy.ops.wm.read_factory_settings(use_empty=True)
            o,a,f=F.build(v,seed=s)
            if f: continue
            G.apply_to(o, G.compute(o,a, falloff=fo, exclusive_seeds=excl, euclid_bias=bias))
            acc.append(bleed_stats(o,a))
        row.append(round(statistics.mean(x["pct_bled"] for x in acc),2))
    res[f"{excl}/{bias}/{fo}"]=row
    print(f"{str(excl):>5} {bias:>5} {fo:>7} " + " ".join(f"{x:>12}" for x in row))
best=min(res.items(), key=lambda kv: kv[1][1])
print(f"\nbest on arms_down: {best[0]} -> {best[1][1]}%  (bone heat {base['arms_down'][0]}%)")
print(f"reduction: {round(100*(base['arms_down'][0]-best[1][1])/base['arms_down'][0],1)}%")
print(f"{time.time()-t0:.1f}s")
json.dump({"baseline":base,"grid":res}, open("/home/claude/blender-addon/sweep.json","w"), indent=1, default=str)
