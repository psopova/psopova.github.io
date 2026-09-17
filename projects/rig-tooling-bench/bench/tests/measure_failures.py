"""Where does Blender's bone-heat weighting actually fail, and by how much?
Bleed = torso vertices moving when only an ARM bone rotates. Pure weight error."""
import bpy, sys, json, time, statistics
sys.path.insert(0,"/home/claude/blender-addon/src")
import rigcorpus as rc, metrics as M, failcases as F

def torso_idx(obj):
    """vertices unambiguously in the chest/belly: an arm bone must never move these."""
    return [i for i,v in enumerate(obj.data.vertices)
            if abs(v.co.x) < 0.14 and 1.15 < v.co.z < 1.72]

def bleed(obj, arm, bone="upperarm.L", angle=1.2):
    ti = torso_idx(obj)
    if not ti: return None
    rest = rc.deformed_coords(obj, arm, {})
    posed = rc.deformed_coords(obj, arm, {bone: (0,0,-angle)})
    h = obj.dimensions.z or 1.0
    d = sorted(((posed[i]-rest[i]).length/h)*100.0 for i in ti)
    moved = sum(1 for x in d if x > 0.5)          # >0.5% of body height is visible
    return {"torso_verts": len(ti), "bled_verts": moved,
            "pct_bled": round(100*moved/len(ti),2),
            "max_bleed_pct": round(d[-1],3), "mean_bleed_pct": round(statistics.mean(d),3)}

SEEDS = range(6)
t0=time.time(); out={}
for variant, meta in F.VARIANTS.items():
    rows=[]; fails=0
    for s in SEEDS:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        obj, arm, failed = F.build(variant, seed=s)
        if failed: fails+=1; continue
        w = M.weight_report(obj, arm)
        b = bleed(obj, arm)
        rows.append({**w, **(b or {})})
    if not rows:
        out[variant]={"note":meta["note"],"hard_fail":f"{fails}/{len(SEEDS)}"}; continue
    tv=sum(r["verts"] for r in rows)
    out[variant]={"note":meta["note"],
      "hard_fail": f"{fails}/{len(SEEDS)}",
      "verts": tv,
      "pct_orphan_verts": round(100*sum(r["orphans"] for r in rows)/tv,2),
      "pct_torso_bled": round(statistics.mean(r["pct_bled"] for r in rows if "pct_bled" in r),2),
      "max_bleed_pct": round(max(r["max_bleed_pct"] for r in rows if "max_bleed_pct" in r),2)}

print(f"{'variant':>13} {'hardFail':>9} {'orphan%':>8} {'torsoBled%':>11} {'maxBleed%':>10}  note")
for k,v in out.items():
    if "verts" not in v: print(f"{k:>13} {v['hard_fail']:>9} {'-':>8} {'-':>11} {'-':>10}  {v['note']}"); continue
    print(f"{k:>13} {v['hard_fail']:>9} {v['pct_orphan_verts']:>8} {v['pct_torso_bled']:>11} {v['max_bleed_pct']:>10}  {v['note']}")
print(f"\n{len(F.VARIANTS)} variants x {len(list(SEEDS))} seeds in {time.time()-t0:.1f}s")
json.dump(out, open("/home/claude/blender-addon/failure_baseline.json","w"), indent=1)
