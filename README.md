# Arminas

Blender add-ons for rigged characters, built and benchmarked headlessly.

**Site:** https://psopova.github.io/

Every number published here is produced by a benchmark rig that ships with the source, so any claim
can be re-derived rather than taken on trust. Results that went the wrong way are published alongside
the ones that did not.

An independent audit was run against these claims in September 2026. It retracted one product, corrected
a number that was 17x wrong, and showed that a set of checks presented as measurements were true by
construction. All of it is in [CORRECTIONS.md](CORRECTIONS.md), and the corrections are reflected above.

---

## Projects

### [Rig Tooling Bench](projects/rig-tooling-bench/) &mdash; Blender 4.2+, GPL-3.0

Two add-ons and the measurement rig behind them.

**Character LOD.** LOD chains from rigged, shape-keyed characters, to exact triangle budgets, with
vertex groups and blend shapes preserved. Blender's own Decimate refuses to apply to a mesh with shape
keys; this does it, hitting triangle budgets to within 1.6% with zero broken weights.

**Geodesic Weights.** Armature binding that measures distance along the mesh surface rather than
through the air, so weight does not leak across the gap between a limb and the body. Removes 26.5% of
the weight bleed left by Blender's own fix, at a cost in joint smoothness that is documented rather
than hidden.

Full write-up, benchmark tables and method: [projects/rig-tooling-bench/README.md](projects/rig-tooling-bench/README.md)

---

## Layout

```
docs/                       the site, served by GitHub Pages
projects/<name>/            one folder per project, self-contained
```

New projects are added as a folder under `projects/` and a section on the site.
