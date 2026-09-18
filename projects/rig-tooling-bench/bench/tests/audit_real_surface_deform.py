"""Audit: run Blender's REAL Surface Deform modifier against the same ground truth."""
import bpy, sys, numpy as np, statistics, json
sys.path.insert(0,"/home/claude/blender-addon/src")
sys.path.insert(0,"/home/claude/blender-addon/tests")
import organic as O, keytransfer as K
from keytransfer_bench import SHAPES, apply_shape, arrays

def real_surface_deform(donor, tgt, src_key_cos):
    """Blender's own Surface Deform + shape key on the donor."""
    me = donor.data
    if me.shape_keys is None:
        donor.shape_key_add(name="Basis")
    kb = donor.shape_key_add(name="K")
    for i in range(len(src_key_cos)):
        kb.data[i].co = src_key_cos[i]
    kb.value = 0.0

    m = tgt.modifiers.new("SD", 'SURFACE_DEFORM')
    m.target = donor
    with bpy.context.temp_override(object=tgt, active_object=tgt, selected_objects=[tgt]):
        bpy.ops.object.surfacedeform_bind(modifier=m.name)
    bound = m.is_bound
    kb.value = 1.0
    dg = bpy.context.evaluated_depsgraph_get(); dg.update()
    ev = tgt.evaluated_get(dg); emesh = ev.to_mesh()
    out = np.array([tuple(v.co) for v in emesh.vertices])
    ev.to_mesh_clear()
    tgt.modifiers.remove(m)
    donor.shape_key_clear()
    return out, bound

N=4; rows=[]
for seed in range(N):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    donor,_,_ = O.character(arms_down=False, seed=seed)
    bpy.context.view_layer.objects.active = donor
    tgt = donor.copy(); tgt.data = donor.data.copy(); tgt.name="target"
    bpy.context.scene.collection.objects.link(tgt)
    bpy.context.view_layer.objects.active = tgt; tgt.select_set(True)
    m=tgt.modifiers.new("R",'REMESH'); m.mode='VOXEL'; m.voxel_size=0.017
    bpy.ops.object.modifier_apply(modifier=m.name)
    for mo in list(tgt.modifiers): tgt.modifiers.remove(mo)
    tgt.parent = None

    Ps=arrays(donor.data); Pd=arrays(tgt.data)
    scale=float(np.linalg.norm(Ps.max(0)-Ps.min(0)))
    for name,spec in SHAPES.items():
        src_key = apply_shape(Ps, spec)
        truth   = apply_shape(Pd, spec)
        ours    = K.transfer(donor.data, src_key, tgt.data)
        straw   = K.surface_deform_style(donor.data, src_key, tgt.data)
        real, bound = real_surface_deform(donor, tgt, src_key)
        eo=np.linalg.norm(ours-truth,axis=1)
        es=np.linalg.norm(straw-truth,axis=1)
        er=np.linalg.norm(real-truth,axis=1)
        rows.append({"seed":seed,"shape":name,"bound":bool(bound),
            "ours_mean":100*eo.mean()/scale,"ours_max":100*eo.max()/scale,
            "straw_mean":100*es.mean()/scale,"straw_max":100*es.max()/scale,
            "real_mean":100*er.mean()/scale,"real_max":100*er.max()/scale})
        print(f"  seed{seed} {name:>12} bound={bound} ours={100*eo.mean()/scale:.5f}% straw={100*es.mean()/scale:.5f}% REALSD={100*er.mean()/scale:.5f}%")
    bpy.data.objects.remove(tgt, do_unlink=True)

print("\n%13s %11s %11s %11s" % ("shape","ours","straw-man","REAL SurfDef"))
for name in SHAPES:
    r=[x for x in rows if x["shape"]==name]
    om=statistics.mean(x["ours_mean"] for x in r)
    sm=statistics.mean(x["straw_mean"] for x in r)
    rm=statistics.mean(x["real_mean"] for x in r)
    print(f"{name:>13} {om:>10.5f}% {sm:>10.5f}% {rm:>10.5f}%   ours vs REAL: {100*(rm-om)/rm:>6.1f}%")
OM=statistics.mean(x["ours_mean"] for x in rows)
SM=statistics.mean(x["straw_mean"] for x in rows)
RM=statistics.mean(x["real_mean"] for x in rows)
print(f"\nMEAN over {len(rows)} transfers:")
print(f"  ours              {OM:.5f}%")
print(f"  straw-man baseline{SM:.5f}%   -> published '{100*(SM-OM)/SM:.1f}% lower error'")
print(f"  REAL Surface Def  {RM:.5f}%   -> honest    '{100*(RM-OM)/RM:.1f}% lower error'")
OX=max(x["ours_max"] for x in rows); SX=max(x["straw_max"] for x in rows); RX=max(x["real_max"] for x in rows)
print(f"  worst case: ours {OX:.3f}%  straw {SX:.3f}% ({SX/OX:.2f}x)  REAL {RX:.3f}% ({RX/OX:.2f}x)")
print(f"  all bound: {all(x['bound'] for x in rows)}")
json.dump(rows, open("/tmp/claude-0/-home-claude/6ea3409c-e9cb-52ca-8bde-ae0066a3349f/scratchpad/audit/real_sd.json","w"), indent=1)
