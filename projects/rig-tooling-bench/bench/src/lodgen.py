"""LOD generation for rigged, shape-keyed characters.

Blender refuses outright: "Modifier cannot be applied to a mesh with shape keys."
And when you strip them first, decimation wrecks the skin weights.
This carries vertex groups, shape keys and the influence cap through the reduction.
"""
import bpy, numpy as np
from scipy.spatial import cKDTree

def _verts(me):
    a = np.empty(len(me.vertices)*3, dtype=np.float64)
    me.vertices.foreach_get("co", a)
    return a.reshape(-1,3)

def _capture(obj, arm=None):
    """Read the weights and shape keys off the source before anything destructive."""
    me = obj.data
    names = [g.name for g in obj.vertex_groups]
    W = np.zeros((len(me.vertices), len(names)), dtype=np.float64)
    for i, v in enumerate(me.vertices):
        for g in v.groups:
            if g.group < len(names): W[i, g.group] = g.weight
    keys, basis = [], None
    if me.shape_keys:
        kb = me.shape_keys.key_blocks
        basis = np.array([tuple(p.co) for p in kb[0].data], dtype=np.float64)
        for k in kb[1:]:
            d = np.array([tuple(p.co) for p in k.data], dtype=np.float64) - basis
            keys.append((k.name, d, k.slider_min, k.slider_max))
    return names, W, keys, basis

def _strip_keys(obj):
    if obj.data.shape_keys:
        bpy.context.view_layer.objects.active = obj
        obj.shape_key_clear()

def _tri_count(obj):
    obj.data.calc_loop_triangles()
    return len(obj.data.loop_triangles)

def _decimate_to_budget(obj, target_tris, tol=0.02, max_iter=12):
    """Blender's Decimate ratio acts on TRIANGLES, so a ratio taken from a face
    count misses badly on quad or n-gon meshes. Binary-search the ratio until the
    triangle budget is actually hit. Game engines specify triangles, not ratios."""
    bpy.context.view_layer.objects.active = obj
    src = _tri_count(obj)
    if target_tris >= src: return src, 0
    lo, hi = 0.001, 1.0
    best = None
    for it in range(max_iter):
        mid = 0.5*(lo+hi)
        m = obj.modifiers.new("LOD", 'DECIMATE')
        m.decimate_type='COLLAPSE'; m.ratio=float(mid); m.use_collapse_triangulate=True
        dg = bpy.context.evaluated_depsgraph_get()
        ev = obj.evaluated_get(dg); me = ev.to_mesh()
        me.calc_loop_triangles(); got = len(me.loop_triangles)
        ev.to_mesh_clear(); obj.modifiers.remove(m)
        if best is None or abs(got-target_tris) < abs(best[1]-target_tris): best=(mid,got)
        if abs(got-target_tris) <= tol*target_tris: break
        if got > target_tris: hi = mid
        else: lo = mid
    ratio, got = best
    m = obj.modifiers.new("LOD", 'DECIMATE')
    m.decimate_type='COLLAPSE'; m.ratio=float(ratio); m.use_collapse_triangulate=True
    bpy.ops.object.modifier_apply(modifier=m.name)
    return _tri_count(obj), it+1

def _decimate(obj, ratio):
    bpy.context.view_layer.objects.active = obj
    m = obj.modifiers.new("LOD", 'DECIMATE'); m.decimate_type='COLLAPSE'; m.ratio=float(ratio)
    m.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier=m.name)

def _transfer(src_co, dst_co, W, keys, k=4, cap=4):
    """Inverse-distance blend from the k nearest source vertices. Smooth, and it
    cannot invent an influence that was not present nearby."""
    tree = cKDTree(src_co)
    d, idx = tree.query(dst_co, k=min(k, len(src_co)))
    if d.ndim == 1: d, idx = d[:,None], idx[:,None]
    w = 1.0/np.maximum(d, 1e-9)**2
    w /= w.sum(axis=1, keepdims=True)

    Wn = np.einsum('nk,nkg->ng', w, W[idx])
    keep = np.argsort(-Wn, axis=1)[:, :cap]
    out = np.zeros_like(Wn)
    np.put_along_axis(out, keep, np.take_along_axis(Wn, keep, axis=1), axis=1)
    s = out.sum(axis=1); s[s==0] = 1.0
    out /= s[:,None]

    newkeys = [(name, np.einsum('nk,nkc->nc', w, delta[idx]), lo, hi) for name, delta, lo, hi in keys]
    return out, newkeys

def build_lod(obj, arm, ratio=None, target_tris=None, cap=4, k=4):
    """Returns a NEW object: reduced to an exact triangle budget, weights
    transferred, shape keys rebuilt. Pass target_tris for a budget, ratio for a fraction."""
    names, W, keys, _ = _capture(obj, arm)
    src_co = _verts(obj.data)

    new = obj.copy(); new.data = obj.data.copy()
    new.name = f"{obj.name}_LOD"
    bpy.context.scene.collection.objects.link(new)
    for m in list(new.modifiers):
        if m.type == 'DECIMATE': new.modifiers.remove(m)
    _strip_keys(new)
    iters = 0
    if target_tris is not None:
        _, iters = _decimate_to_budget(new, int(target_tris))
    else:
        _decimate(new, ratio)
    new["lod_search_iters"] = iters

    dst_co = _verts(new.data)
    Wn, newkeys = _transfer(src_co, dst_co, W, keys, k=k, cap=cap)

    for g in list(new.vertex_groups): new.vertex_groups.remove(g)
    for j, name in enumerate(names):
        g = new.vertex_groups.new(name=name)
        nz = np.nonzero(Wn[:, j] > 1e-6)[0]
        for i in nz: g.add([int(i)], float(Wn[i, j]), 'REPLACE')

    if newkeys:
        new.shape_key_add(name="Basis")
        base = _verts(new.data)
        for name, delta, lo, hi in newkeys:
            kb = new.shape_key_add(name=name)
            kb.slider_min, kb.slider_max = lo, hi
            tgt = base + delta
            for i in range(len(tgt)): kb.data[i].co = tgt[i]
    return new
