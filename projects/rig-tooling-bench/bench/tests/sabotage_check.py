"""Deliberately break the code and confirm the benchmark NOTICES.
A test suite that passes on broken code is not a test suite."""
import subprocess, shutil, sys, os, re
SRC="/home/claude/blender-addon/src/lodgen.py"
BAK=SRC+".sabotage.bak"

SABOTAGE = {
 "scramble transferred weights":
   ("    s = out.sum(axis=1); s[s==0] = 1.0", "    out = out[::-1]\n    s = out.sum(axis=1); s[s==0] = 1.0"),
 "drop the shape keys":
   ("    if newkeys:", "    newkeys = []\n    if newkeys:"),
 "ignore the triangle budget":
   ("        _, iters = _decimate_to_budget(new, int(target_tris))", "        _decimate(new, 0.9)"),
}
shutil.copy(SRC, BAK)
results=[]
for name,(old,new) in SABOTAGE.items():
    s=open(BAK).read()
    if old not in s: results.append((name,"PATCH FAILED")); continue
    open(SRC,"w").write(s.replace(old,new,1))
    r=subprocess.run([sys.executable,"tests/lod_bench.py"], capture_output=True, text=True,
                     cwd="/home/claude/blender-addon", timeout=900)
    out=r.stdout+r.stderr
    m=re.search(r"ASSERTIONS: (\d+) failed(.*)", out)
    caught = (r.returncode!=0) or (m and int(m.group(1))>0)
    detail = m.group(2).strip()[:90] if m else out.strip().splitlines()[-1][:90]
    results.append((name, "CAUGHT" if caught else "MISSED", detail))
shutil.copy(BAK, SRC); os.remove(BAK)

print(f"{'sabotage':>32}  {'result':>7}  detail")
for r in results:
    print(f"{r[0]:>32}  {r[1]:>7}  {r[2] if len(r)>2 else ''}")
missed=[r for r in results if r[1]!="CAUGHT"]
print(f"\n{len(results)-len(missed)}/{len(results)} sabotages caught")
