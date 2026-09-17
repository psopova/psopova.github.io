import sys, statistics
sys.path.insert(0,"/home/claude/blender-addon/src")
import rigcorpus as rc
def torso_idx(obj):
    return [i for i,v in enumerate(obj.data.vertices) if abs(v.co.x)<0.14 and 1.15<v.co.z<1.72]
def bleed_stats(obj, arm, bone="upperarm.L", angle=1.2):
    ti = torso_idx(obj)
    if not ti: return None
    rest = rc.deformed_coords(obj, arm, {}); posed = rc.deformed_coords(obj, arm, {bone:(0,0,-angle)})
    h = obj.dimensions.z or 1.0
    d = sorted(((posed[i]-rest[i]).length/h)*100.0 for i in ti)
    return {"pct_bled": round(100*sum(1 for x in d if x>0.5)/len(d),2),
            "max_bleed_pct": round(d[-1],3), "mean_bleed_pct": round(statistics.mean(d),3)}
