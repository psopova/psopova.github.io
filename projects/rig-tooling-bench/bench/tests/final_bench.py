import bpy, sys, statistics, json, numpy as np, time
sys.path.insert(0,"/home/claude/blender-addon/src"); sys.path.insert(0,"/home/claude/blender-addon/tests")
import organic as O, geoweight as G, metrics as M, realchar as R
from tests_common import bleed_stats

def profile(o,a):
    di=M.deform_group_indices(o,a); eff=[];rig=0;n=0
    for v in o.data.vertices:
        gs=sorted([g.weight for g in v.groups if g.group in di and g.weight>1e-4],reverse=True)
        if not gs: continue
        n+=1; eff.append(1.0/sum(w*w for w in gs))
        if gs[0]>0.98: rig+=1
    return statistics.mean(eff), 100*rig/max(n,1)
def jag(o,a,bone="lowerarm.L",ang=1.4):
    rest=R.rc.deformed_coords(o,a,{}); pos=R.rc.deformed_coords(o,a,{bone:(0,0,-ang)})
    h=o.dimensions.z or 1.0; d=[(pos[i]-rest[i]).length/h for i in range(len(rest))]
    return 100*float(np.percentile([abs(d[e.vertices[0]]-d[e.vertices[1]]) for e in o.data.edges],99))

N=5; t0=time.time(); res={}
for label, ad in (("t_pose",False),("arms_down",True)):
    for meth in ("heat","geo"):
        B=[];E=[];Rg=[];J=[];U=[];Ov=[];V=[]
        for s in range(N):
            bpy.ops.wm.read_factory_settings(use_empty=True)
            o,a,f=O.character(arms_down=ad, seed=s)
            if f: continue
            if meth=="geo": G.apply_to(o, G.compute(o,a,falloff=10.0,exclusive_seeds=False,smooth_iters=40,smooth_lambda=0.6))
            w=M.weight_report(o,a); e,r=profile(o,a)
            B.append(bleed_stats(o,a)["pct_bled"]); E.append(e); Rg.append(r); J.append(jag(o,a))
            U.append(w["unnormalised"]); Ov.append(w["over_cap"]); V.append(w["verts"])
        res[f"{label}/{meth}"]={"bled":round(statistics.mean(B),2),"eff_bones":round(statistics.mean(E),2),
            "rigid":round(statistics.mean(Rg),1),"jag":round(statistics.mean(J),2),
            "unnorm":sum(U),"over4":sum(Ov),"verts":sum(V),"chars":len(B)}

print(f"{'case':>18} {'bled%':>7} {'jag':>6} {'effBones':>9} {'unnorm':>8} {'over4':>6} {'verts':>8}")
for k,v in res.items():
    print(f"{k:>18} {v['bled']:>7} {v['jag']:>6} {v['eff_bones']:>9} {v['unnorm']:>8,} {v['over4']:>6,} {v['verts']:>8,}")
print(f"\n{2*2*N} character builds, full metrics, {time.time()-t0:.1f}s")
for label in ("t_pose","arms_down"):
    h=res[f"{label}/heat"]; g=res[f"{label}/geo"]
    print(f"{label}: bleed {h['bled']}% -> {g['bled']}%  ({round(100*(h['bled']-g['bled'])/h['bled'],1)}% fewer)   jag {h['jag']} -> {g['jag']}")
json.dump(res, open("/home/claude/blender-addon/out/final_bench.json","w"), indent=1)
