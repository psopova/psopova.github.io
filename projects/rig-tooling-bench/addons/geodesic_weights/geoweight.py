"""Geodesic bone weighting.

Blender's bone heat diffuses through space, so when a limb sits near the torso the
heat leaks across the air gap. Distance measured ALONG THE SURFACE cannot leak:
the arm is 8 cm away through the air but ~60 cm away over the skin.
"""
import numpy as np, bmesh
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra
from mathutils import Vector

def _edge_graph(me):
    v = np.array([tuple(x.co) for x in me.vertices], dtype=np.float64)
    e = np.array([tuple(x.vertices) for x in me.edges], dtype=np.int64)
    if len(e) == 0: return v, csr_matrix((len(v), len(v)))
    w = np.linalg.norm(v[e[:,0]] - v[e[:,1]], axis=1)
    n = len(v)
    g = csr_matrix((np.concatenate([w,w]),
                    (np.concatenate([e[:,0],e[:,1]]), np.concatenate([e[:,1],e[:,0]]))), shape=(n,n))
    return v, g

def _seg_dist(p, a, b):
    ab = b - a; t = np.clip(((p - a) @ ab) / max(ab @ ab, 1e-12), 0.0, 1.0)
    return np.linalg.norm(p - (a + np.outer(t, ab)), axis=1)

def compute(obj, arm, cap=4, falloff=4.0, seed_frac=0.12, exclusive_seeds=True, euclid_bias=0.0,
            smooth_iters=0, smooth_lambda=0.5):
    """Returns {bone_name: np.array(weights)} normalised, capped, no orphans."""
    me = obj.data
    verts, graph = _edge_graph(me)
    mw = np.array(obj.matrix_world.to_4x4())
    world = (np.c_[verts, np.ones(len(verts))] @ mw.T)[:, :3]

    bones = [b for b in arm.data.bones if b.use_deform]
    amw = arm.matrix_world
    D = np.empty((len(bones), len(verts)), dtype=np.float64)
    for i, b in enumerate(bones):
        a = np.array(tuple(amw @ b.head_local)); c = np.array(tuple(amw @ b.tail_local))
        D[i] = _seg_dist(world, a, c)
    owner = np.argmin(D, axis=0)     # each vertex votes for exactly ONE bone

    geo = np.empty((len(bones), len(verts)), dtype=np.float64)
    for i, b in enumerate(bones):
        if exclusive_seeds:
            cand = np.nonzero(owner == i)[0]          # only vertices this bone actually owns
            if len(cand) == 0: cand = np.argsort(D[i])[:3]
            k = max(3, min(len(cand), int(len(verts) * seed_frac * 0.1)))
            seeds = cand[np.argsort(D[i][cand])[:k]]
        else:
            seeds = np.argsort(D[i])[:max(3, int(len(verts) * seed_frac * 0.1))]
        gd = dijkstra(graph, indices=seeds, directed=False, min_only=True)
        fin = np.isfinite(gd)
        gd = np.where(fin, gd, (np.nanmax(gd[fin]) * 4) if fin.any() else 1.0)
        geo[i] = gd + D[i] * euclid_bias
    scale = max(np.percentile(geo, 50), 1e-6)
    inv = 1.0 / np.power(geo / scale + 1e-4, falloff)

    # Laplacian smoothing of the weight field, ACROSS THE SURFACE ONLY.
    # This restores the gradual blend that bone heat gets right, and it cannot
    # reintroduce cross-gap bleed because weight can only flow along mesh edges.
    if smooth_iters:
        s0 = inv / np.maximum(inv.sum(axis=0), 1e-12)
        deg = np.asarray(graph.getnnz(axis=1)).ravel().astype(np.float64)
        deg[deg == 0] = 1.0
        adj = (graph > 0).astype(np.float64)
        for _ in range(smooth_iters):
            nb = (adj @ s0.T).T / deg
            s0 = (1.0 - smooth_lambda) * s0 + smooth_lambda * nb
        inv = s0

    keep = np.argsort(-inv, axis=0)[:cap]                # top-N bones per vertex
    out = np.zeros_like(inv)
    np.put_along_axis(out, keep, np.take_along_axis(inv, keep, axis=0), axis=0)
    s = out.sum(axis=0); s[s == 0] = 1.0
    out /= s
    return {b.name: out[i] for i, b in enumerate(bones)}

def apply_to(obj, weights):
    for g in list(obj.vertex_groups): obj.vertex_groups.remove(g)
    for name, w in weights.items():
        g = obj.vertex_groups.new(name=name)
        nz = np.nonzero(w > 1e-6)[0]
        for i in nz: g.add([int(i)], float(w[i]), 'REPLACE')
