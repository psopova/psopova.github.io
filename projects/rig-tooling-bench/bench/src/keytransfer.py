"""Shape key transfer between meshes with unrelated topology.

Blender's path is Surface Deform + Apply as Shape Key. Surface Deform binds by
barycentric projection and interpolates POSITIONS, so any shape carrying local
rotation gets smeared. Blender's own tracker records this (#161807, #98891).

This transfers through each source triangle's local FRAME, which is that triangle's
deformation gradient, so rotation and scale come across exactly.
"""
import numpy as np
from scipy.spatial import cKDTree

def _tri_arrays(me):
    me.calc_loop_triangles()
    v = np.empty(len(me.vertices)*3); me.vertices.foreach_get("co", v); v = v.reshape(-1,3)
    t = np.array([tuple(lt.vertices) for lt in me.loop_triangles], dtype=np.int64)
    return v, t

def _frames(P, T):
    """Per-triangle frame: two edges plus the normal. Columns of a 3x3 matrix."""
    a, b, c = P[T[:,0]], P[T[:,1]], P[T[:,2]]
    e1, e2 = b-a, c-a
    n = np.cross(e1, e2)
    ln = np.linalg.norm(n, axis=1, keepdims=True)
    n = n / np.maximum(ln, 1e-12)
    F = np.stack([e1, e2, n], axis=2)          # (T,3,3)
    return a, F

def _safe_inv(F):
    det = np.linalg.det(F)
    bad = np.abs(det) < 1e-12
    if bad.any():
        F = F.copy()
        F[bad] += np.eye(3) * 1e-6
    return np.linalg.inv(F)

def transfer(src_me, src_key_cos, dst_me, k=6, sigma_frac=0.05):
    """src_key_cos: (V_src,3) positions of one shape key on the source.
    Returns (V_dst,3) positions for that key on the target."""
    Ps, T = _tri_arrays(src_me)
    Pd, _ = _tri_arrays(dst_me)
    if len(T) == 0: return Pd.copy()

    a0, F0 = _frames(Ps, T)                    # rest frames
    a1, F1 = _frames(src_key_cos, T)           # deformed frames
    F0inv = _safe_inv(F0)
    G = F1 @ F0inv                             # deformation gradient per triangle

    cent = Ps[T].mean(axis=1)
    tree = cKDTree(cent)
    kk = min(k, len(cent))
    d, idx = tree.query(Pd, k=kk)
    if d.ndim == 1: d, idx = d[:,None], idx[:,None]

    scale = np.linalg.norm(Ps.max(axis=0) - Ps.min(axis=0))
    sigma = max(scale * sigma_frac, 1e-6)
    w = np.exp(-(d/sigma)**2) + 1e-12
    w /= w.sum(axis=1, keepdims=True)

    # each neighbouring triangle predicts where this vertex goes, under ITS gradient
    rel = Pd[:,None,:] - a0[idx]                       # (V,k,3)
    pred = a1[idx] + np.einsum('vkij,vkj->vki', G[idx], rel)
    return (w[...,None] * pred).sum(axis=1)

def surface_deform_style(src_me, src_key_cos, dst_me, k=6):
    """The position-interpolating baseline, i.e. what Surface Deform does in spirit:
    blend the source's per-vertex displacement, ignoring rotation."""
    Ps, _ = _tri_arrays(src_me); Pd, _ = _tri_arrays(dst_me)
    delta = src_key_cos - Ps
    tree = cKDTree(Ps)
    kk = min(k, len(Ps))
    d, idx = tree.query(Pd, k=kk)
    if d.ndim == 1: d, idx = d[:,None], idx[:,None]
    w = 1.0/np.maximum(d,1e-9)**2; w /= w.sum(axis=1, keepdims=True)
    return Pd + np.einsum('vk,vkc->vc', w, delta[idx])
