"""Ground truth is exact, not estimated.

A shape is defined as an ANALYTIC function of position (a rotation about an axis,
falling off with height). Apply it to the donor to make its shape key; apply the SAME
function to the target to get the target's exact correct key. Then transfer donor->target
and measure the error against that exact answer. No circularity.
"""
import bpy, sys, numpy as np, statistics, time, json
sys.path.insert(0,"/home/claude/blender-addon/src")
import organic as O, keytransfer as K

def arrays(me):
    v=np.empty(len(me.vertices)*3); me.vertices.foreach_get("co",v); return v.reshape(-1,3)

def rot(axis, ang):
    axis=np.asarray(axis,float); axis/=np.linalg.norm(axis)
    x,y,z=axis; c,s=np.cos(ang),np.sin(ang); C=1-c
    return np.array([[c+x*x*C, x*y*C-z*s, x*z*C+y*s],
                     [y*x*C+z*s, c+y*y*C, y*z*C-x*s],
                     [z*x*C-y*s, z*y*C+x*s, c+z*z*C]])

# each shape carries real local ROTATION, which is what position blending gets wrong
SHAPES = {
 "jaw_open":   dict(axis=(1,0,0), ang=0.55, pivot=(0,0,1.90), lo=1.86, hi=2.06),
 "head_turn":  dict(axis=(0,0,1), ang=0.70, pivot=(0,0,1.80), lo=1.78, hi=2.10),
 "shoulder_up":dict(axis=(0,1,0), ang=0.45, pivot=(0,0,1.70), lo=1.55, hi=1.80),
 "spine_bend": dict(axis=(1,0,0), ang=0.40, pivot=(0,0,1.10), lo=1.05, hi=1.75),
}

def apply_shape(P, spec):
    R=rot(spec["axis"], 1.0); pivot=np.array(spec["pivot"],float)
    t=np.clip((P[:,2]-spec["lo"])/(spec["hi"]-spec["lo"]), 0, 1)
    t=t*t*(3-2*t)                                   # smoothstep falloff
    out=P.copy()
    for i in range(len(P)):
        if t[i] <= 0: continue
        Ri=rot(spec["axis"], spec["ang"]*t[i])
        out[i]=pivot + Ri @ (P[i]-pivot)
    return out

N=4; t0=time.time(); rows=[]
for seed in range(N):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    donor,_,_ = O.character(arms_down=False, seed=seed)
    # target: same character, different topology (finer remesh), so correspondence is non-trivial
    bpy.context.view_layer.objects.active = donor
    tgt = donor.copy(); tgt.data = donor.data.copy(); tgt.name="target"
    bpy.context.scene.collection.objects.link(tgt)
    bpy.context.view_layer.objects.active = tgt; tgt.select_set(True)
    m=tgt.modifiers.new("R",'REMESH'); m.mode='VOXEL'; m.voxel_size=0.017
    bpy.ops.object.modifier_apply(modifier=m.name)

    Ps=arrays(donor.data); Pd=arrays(tgt.data)
    scale=float(np.linalg.norm(Ps.max(0)-Ps.min(0)))
    for name,spec in SHAPES.items():
        src_key = apply_shape(Ps, spec)
        truth   = apply_shape(Pd, spec)              # exact answer on the target
        ours    = K.transfer(donor.data, src_key, tgt.data)
        base    = K.surface_deform_style(donor.data, src_key, tgt.data)
        eo=np.linalg.norm(ours-truth,axis=1); eb=np.linalg.norm(base-truth,axis=1)
        rows.append({"seed":seed,"shape":name,"src_v":len(Ps),"dst_v":len(Pd),
            "ours_mean":100*eo.mean()/scale,"ours_max":100*eo.max()/scale,
            "base_mean":100*eb.mean()/scale,"base_max":100*eb.max()/scale})
    bpy.data.objects.remove(tgt, do_unlink=True)

print(f"{'shape':>13} {'ours mean':>10} {'base mean':>10} {'ours max':>9} {'base max':>9} {'mean better by':>15}")
agg={}
for name in SHAPES:
    r=[x for x in rows if x["shape"]==name]
    om=statistics.mean(x["ours_mean"] for x in r); bm=statistics.mean(x["base_mean"] for x in r)
    ox=max(x["ours_max"] for x in r); bx=max(x["base_max"] for x in r)
    agg[name]={"ours_mean":round(om,4),"base_mean":round(bm,4),"ours_max":round(ox,3),"base_max":round(bx,3),
               "better_pct":round(100*(bm-om)/bm,1)}
    print(f"{name:>13} {om:>9.4f}% {bm:>9.4f}% {ox:>8.3f}% {bx:>8.3f}% {100*(bm-om)/bm:>14.1f}%")
OM=statistics.mean(x["ours_mean"] for x in rows); BM=statistics.mean(x["base_mean"] for x in rows)
print(f"\nACROSS ALL {len(rows)} TRANSFERS ({N} characters x {len(SHAPES)} shapes)")
print(f"  deformation-gradient : mean error {OM:.4f}% of body height")
print(f"  position blending    : mean error {BM:.4f}% of body height")
print(f"  -> {100*(BM-OM)/BM:.1f}% lower error")
print(f"  source {rows[0]['src_v']:,} verts -> target {rows[0]['dst_v']:,} verts (different topology)")
print(f"  {time.time()-t0:.1f}s")
json.dump({"per_shape":agg,"overall":{"ours":round(OM,4),"base":round(BM,4)}}, open("/home/claude/blender-addon/out/keytransfer.json","w"), indent=1)
