import bpy, sys, time, statistics, itertools, json
sys.path.insert(0,"/home/claude/blender-addon/src"); sys.path.insert(0,"/home/claude/blender-addon/tests")
import metrics as M, realchar as R, geoweight as G
from tests_common import bleed_stats
SEEDS=range(5); t0=time.time()

base={}
for ad,label in ((False,"t_pose"),(True,"arms_down")):
    acc=[]; ws=[]
    for s in SEEDS:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        o,a,f=R.character(arms_down=ad, seed=s)
        if f: continue
        acc.append(bleed_stats(o,a)); ws.append(M.weight_report(o,a))
    tv=sum(w["verts"] for w in ws)
    base[label]={"pct_bled":round(statistics.mean(x["pct_bled"] for x in acc),2),
                 "max_bleed":round(max(x["max_bleed_pct"] for x in acc),2),
                 "verts":tv,"unnorm":sum(w["unnormalised"] for w in ws),"over4":sum(w["over_cap"] for w in ws)}
print("BLENDER BONE HEAT, 5 welded characters each:")
for k,v in base.items(): print(f"  {k:>10}: {v['pct_bled']:>6}% torso bled, worst {v['max_bleed']}%, {v['unnorm']:,}/{v['verts']:,} unnormalised, {v['over4']} over 4 influences")

print(f"\n{'excl':>5} {'falloff':>7} {'t_pose':>9} {'arms_down':>10} {'unnorm':>7} {'over4':>6}")
best=None
for excl,fo in itertools.product([True,False],[3.0,6.0,10.0,16.0]):
    row={}; un=ov=0
    for ad,label in ((False,"t_pose"),(True,"arms_down")):
        acc=[]
        for s in SEEDS:
            bpy.ops.wm.read_factory_settings(use_empty=True)
            o,a,f=R.character(arms_down=ad, seed=s)
            if f: continue
            G.apply_to(o, G.compute(o,a, falloff=fo, exclusive_seeds=excl, euclid_bias=0.0))
            acc.append(bleed_stats(o,a)); w=M.weight_report(o,a); un+=w["unnormalised"]; ov+=w["over_cap"]
        row[label]=round(statistics.mean(x["pct_bled"] for x in acc),2)
    print(f"{str(excl):>5} {fo:>7} {row['t_pose']:>9} {row['arms_down']:>10} {un:>7} {ov:>6}")
    if best is None or row["arms_down"]<best[1]["arms_down"]: best=((excl,fo),row)

print(f"\nBEST: exclusive_seeds={best[0][0]}, falloff={best[0][1]}")
for k in ("t_pose","arms_down"):
    b=base[k]["pct_bled"]; g=best[1][k]
    print(f"  {k:>10}: bone heat {b}%  ->  geodesic {g}%   ({round(100*(b-g)/b,1)}% fewer bleeding vertices)")
print(f"\n{time.time()-t0:.1f}s")
json.dump({"baseline":base,"best":{"params":list(best[0]),"result":best[1]}}, open("/home/claude/blender-addon/real_ab.json","w"), indent=1)
