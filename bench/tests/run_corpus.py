import bpy, sys, time, json, statistics
sys.path.insert(0, "/home/claude/blender-addon/src")
import rigcorpus as rc, metrics as M

N = int(sys.argv[1]) if len(sys.argv) > 1 else 8
t0 = time.time(); rows = []
for seed in range(N):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    obj, arm = rc.build_character(seed=seed)
    h = obj.dimensions.z or 1.0
    w = M.weight_report(obj, arm)
    rest = rc.deformed_coords(obj, arm, {})
    errs = [M.deformation_error(rest, rc.deformed_coords(obj, arm, p), h) for p in rc.TEST_POSES]
    rows.append({"seed": seed, **w,
                 "pose_mean_pct": round(statistics.mean(e["mean_pct"] for e in errs), 3),
                 "pose_max_pct": round(max(e["max_pct"] for e in errs), 3)})

# --- invariants that must hold for the corpus to be usable as a benchmark ---
assert all(r["verts"] > 1000 for r in rows), "characters too coarse to be a real test"
assert all(r["orphans"] == 0 for r in rows), [r for r in rows if r["orphans"]]
assert all(r["max_influences"] >= 2 for r in rows), "auto-weights produced no blending"
assert all(r["pose_max_pct"] > 1.0 for r in rows), "poses do not actually move the mesh"
assert len({r["verts"] for r in rows}) > 1, "corpus is not varied"

print(f"{'seed':>4} {'verts':>6} {'maxInf':>6} {'overCap':>7} {'unnorm':>6} {'orphan':>6} {'poseMean%':>9} {'poseMax%':>8}")
for r in rows:
    print(f"{r['seed']:>4} {r['verts']:>6} {r['max_influences']:>6} {r['over_cap']:>7} {r['unnormalised']:>6} {r['orphans']:>6} {r['pose_mean_pct']:>9} {r['pose_max_pct']:>8}")
tv = sum(r["verts"] for r in rows)
print(f"\nCORPUS OK: {N} rigged characters, {tv:,} vertices, {N*len(rc.TEST_POSES)} pose evaluations, {time.time()-t0:.1f}s")
print(f"over-cap verts (>4 influences): {sum(r['over_cap'] for r in rows):,} of {tv:,}  = {100*sum(r['over_cap'] for r in rows)/tv:.1f}%")
json.dump(rows, open("/home/claude/blender-addon/corpus_baseline.json","w"), indent=1)
