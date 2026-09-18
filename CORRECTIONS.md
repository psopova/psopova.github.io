# Corrections after independent audit, 17 September 2026

An independent auditor was given the source, told to run it and rewarded for breaking it.
It broke two of three claims. This file records what changed and why.

## Retracted entirely: Shape Key Transfer

**Published claim:** "66.7% lower error than position blending, 6 times better worst case."

**What was wrong:** the comparison baseline was written by the same person as the method.
It was inverse-distance blending over the six nearest source *vertices*. Blender's actual
Surface Deform modifier binds barycentrically to *polygons* and is substantially better.

Run on the identical benchmark with the real modifier, all 16 transfers bound successfully:

| | mean error |
|---|---|
| the add-on | 0.00373% |
| the straw-man baseline | 0.01098% |
| **Blender's real Surface Deform** | **0.00272%** |

**Blender's built-in has 37% less error than the add-on.** Worst case too: 0.279% against 0.329%.

A further attempt to fix it made it marginally worse. The frame construction is exact on
rigid rotation and insensitive to deformation along the surface normal, and all four test
shapes chosen happened to be rigid rotations, which is the one class it handles exactly.

**Action: the product is dropped.** It is worse than a built-in modifier that ships free.
The code stays in the repository, marked as a negative result.

## Corrected: Character LOD deformation error

**Published:** 2.70% / 2.78% / 2.86%.
**Honest:** **0.157% / 0.285% / 0.346%.**

The benchmark built its nearest-point KD-tree once from the first pose and reused it for the
other two, comparing later poses against the wrong base geometry. 17 times too large.

The bug was flattering in the way that matters: the wrong figure rose only 6% from LOD1 to
LOD3, which reads as "LOD3 is nearly as good as LOD1". The honest figure more than doubles.
The corrected benchmark now asserts that LOD3 must be at least 1.3x worse than LOD1, because
a degradation metric that does not degrade is not measuring anything.

## Relabelled: the LOD "preserved" checklist

"17 vertex groups, 4 shape keys, 0 unnormalised, 0 over the influence cap" was presented as a
measurement. It is **guaranteed by construction**. The auditor sabotaged the transfer three
ways and every column stayed identical.

The benchmark now carries assertions that can fail, and they were verified by deliberately
breaking the code: **3 of 3 sabotages caught**, including the auditor's own three.

## Corrected: a causal claim about Decimate

**Published:** decimating "leaves 2,712 of 2,895 vertices with weights that no longer sum to
1.0 ... the rig is broken."

Measured before and after: **94.9% unnormalised before any decimation, 93.7% after.** Decimate
slightly improved both rates. Blender's automatic weight bind broke the rig, not Decimate.
The counts were right; the attribution was wrong.

## Qualified: Geodesic Weights

The numbers survived. They reproduce exactly, hold on five seeds never used during tuning
(29.0% against a published 28.8%), are robust across bleed thresholds from 0.1% to 5.0%, and
the choice to compare against Blender's free two-operator fix rather than the untouched bind
was the harder comparison. The auditor also confirmed a far more flattering 92.6% result
existed in the files and was not published.

Three caveats were missing and are now stated:

1. **The stated mechanism is wrong for this corpus.** The claim was that an arm 8 cm from the
   body is 60 cm away across the skin, a 7.5x ratio. Measured on the actual meshes it is
   **1.10x median**: the voxel remesh fuses the arms into the torso, so there is no air gap.
   The effect is real, the explanation was not.
2. **About half the gain is not geodesic.** Replacing Dijkstra with plain Euclidean distance,
   everything else identical, gives 53.50% against 44.77%. Geodesic accounts for 8.7 of the
   18.1 point reduction; the rest is falloff, capping and smoothing.
3. **The anti-cheat guard did not work.** Jaggedness was described as the check that catches a
   method snapping every vertex to one bone. Binding every vertex to the pelvis scored
   **0.00% bleed and 0.00 jaggedness**, beating the add-on on every published metric, while
   the mesh did not move at all. A rigid bind is perfectly smooth, so jaggedness cannot see it.
   **An under-deformation gate has been added and rejects that cheat outright.**

Precision was also overstated: per-seed reduction runs 21.5 to 36.6 percent on five
near-duplicate characters. Three significant figures were not earned. The honest statement is
**about 29% fewer bleeding vertices than bone heat, roughly 21 to 36 percent at 95% confidence**.

Two results were computed and quietly dropped, and both are now published: the T-pose case is
**11.5%**, less than half the headline, and effective bones per vertex goes the wrong way,
1.80 for bone heat against 1.70 for the add-on.

## What changed in how this is built

The code, the benchmark and the grading were all written by the same author, which is the exact
failure this portfolio criticised in other people's listings. From here, code and its audit are
separated, and no number is published until something that did not write the code has tried to
break it.
