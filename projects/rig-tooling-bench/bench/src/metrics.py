"""The numbers. Every claim we publish must come out of here."""
import bpy

def deform_group_indices(obj, arm):
    names = {b.name for b in arm.data.bones if b.use_deform}
    return {g.index for g in obj.vertex_groups if g.name in names}

def weight_report(obj, arm, cap=4, eps=1e-5):
    di = deform_group_indices(obj, arm)
    over = unnorm = orphan = 0; worst_sum = 0.0; max_inf = 0
    for v in obj.data.vertices:
        gs = [g for g in v.groups if g.group in di and g.weight > 0.0]
        n = len(gs); s = sum(g.weight for g in gs)
        max_inf = max(max_inf, n)
        if n > cap: over += 1
        if n == 0: orphan += 1
        elif abs(s - 1.0) > eps: unnorm += 1; worst_sum = max(worst_sum, abs(s-1.0))
        
    return {"verts": len(obj.data.vertices), "max_influences": max_inf,
            "over_cap": over, "unnormalised": unnorm, "orphans": orphan,
            "worst_sum_error": round(worst_sum, 6)}

def deformation_error(coords_a, coords_b, scale):
    """mean / p99 / max displacement, as a percentage of character height."""
    assert len(coords_a) == len(coords_b), (len(coords_a), len(coords_b))
    d = sorted(((a-b).length / scale) * 100.0 for a, b in zip(coords_a, coords_b))
    n = len(d)
    return {"mean_pct": round(sum(d)/n, 4), "p99_pct": round(d[int(n*0.99)], 4), "max_pct": round(d[-1], 4)}
