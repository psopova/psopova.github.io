"""How good is Blender's built-in UV packer, measured?
Packing efficiency = fraction of the 0..1 UV square actually covered by islands.
Wasted space is a number a product listing can advertise."""
import bpy, sys, numpy as np, statistics, time
sys.path.insert(0,"/home/claude/blender-addon/src")
import organic as O

def uv_coverage(obj, res=512):
    """Rasterise the UV layout and count covered texels. Exact, not an estimate."""
    me = obj.data
    me.calc_loop_triangles()
    uvl = me.uv_layers.active
    if uvl is None: return None
    uv = np.empty(len(me.loops)*2, dtype=np.float64); uvl.data.foreach_get("uv", uv)
    uv = uv.reshape(-1,2)
    grid = np.zeros((res,res), dtype=bool)
    for t in me.loop_triangles:
        p = uv[list(t.loops)] * res
        minx,miny = np.floor(p.min(axis=0)).astype(int); maxx,maxy = np.ceil(p.max(axis=0)).astype(int)
        minx=max(minx,0); miny=max(miny,0); maxx=min(maxx,res); maxy=min(maxy,res)
        if maxx<=minx or maxy<=miny: continue
        xs,ys = np.meshgrid(np.arange(minx,maxx)+0.5, np.arange(miny,maxy)+0.5)
        pts = np.stack([xs.ravel(),ys.ravel()],axis=1)
        a,b,c = p[0],p[1],p[2]
        v0,v1,v2 = c-a, b-a, pts-a
        d00,d01,d11 = v0@v0, v0@v1, v1@v1
        d20,d21 = v2@v0, v2@v1
        den = d00*d11-d01*d01
        if abs(den) < 1e-12: continue
        u = (d11*d20-d01*d21)/den; v = (d00*d21-d01*d20)/den
        inside = (u>=0)&(v>=0)&(u+v<=1)
        if inside.any():
            gi = pts[inside].astype(int)
            grid[np.clip(gi[:,1],0,res-1), np.clip(gi[:,0],0,res-1)] = True
    return grid.sum()/float(res*res)

def overlaps(obj):
    """Count loops whose UV falls outside 0..1, which is a hard packing failure."""
    me=obj.data; uvl=me.uv_layers.active
    uv=np.empty(len(me.loops)*2); uvl.data.foreach_get("uv",uv); uv=uv.reshape(-1,2)
    return int(((uv<-1e-6)|(uv>1+1e-6)).any(axis=1).sum())

rows=[]; t0=time.time()
for seed in range(4):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    obj,arm,_ = O.character(arms_down=False, seed=seed)
    bpy.context.view_layer.objects.active = obj; obj.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.002)
    bpy.ops.object.mode_set(mode='OBJECT')
    smart = uv_coverage(obj)
    # then ask Blender to pack it as tightly as it can
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.select_all(action='SELECT')
    try: bpy.ops.uv.pack_islands(rotate=True, margin=0.002, shape_method='CONCAVE')
    except TypeError: bpy.ops.uv.pack_islands(rotate=True, margin=0.002)
    bpy.ops.object.mode_set(mode='OBJECT')
    packed = uv_coverage(obj)
    rows.append((len(obj.data.polygons), smart, packed, overlaps(obj)))
    print(f"seed {seed}: {len(obj.data.polygons):>6} faces   smart_project {smart*100:>5.1f}%   after pack_islands {packed*100:>5.1f}%   out-of-bounds loops {overlaps(obj)}")

s=statistics.mean(r[1] for r in rows); p=statistics.mean(r[2] for r in rows)
print(f"\nBlender Smart UV Project:      {s*100:.1f}% of the UV square covered  ->  {100-s*100:.1f}% WASTED")
print(f"Blender pack_islands (concave): {p*100:.1f}% covered  ->  {100-p*100:.1f}% WASTED")
print(f"{len(rows)} characters in {time.time()-t0:.1f}s")
