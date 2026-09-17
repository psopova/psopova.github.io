bl_info = {"name":"Character LOD","author":"Arminas","version":(0,1,0),"blender":(4,2,0),
           "location":"Object > Character LOD","category":"Object",
           "description":"Generate LOD chains from rigged characters to exact triangle budgets, preserving vertex groups and shape keys"}
import bpy
from . import lodgen

class OBJECT_OT_character_lod(bpy.types.Operator):
    bl_idname="object.character_lod"; bl_label="Character LOD"; bl_options={'REGISTER','UNDO'}
    levels: bpy.props.IntProperty(name="Levels", default=3, min=1, max=6)
    ratio: bpy.props.FloatProperty(name="Reduction per level", default=0.5, min=0.05, max=0.95)
    cap: bpy.props.IntProperty(name="Max influences", default=4, min=1, max=8)

    @classmethod
    def poll(cls, ctx):
        o=ctx.active_object
        return o and o.type=='MESH'

    def execute(self, ctx):
        obj=ctx.active_object
        arm=obj.parent if obj.parent and obj.parent.type=='ARMATURE' else None
        obj.data.calc_loop_triangles()
        tris=len(obj.data.loop_triangles)
        made=[]
        try:
            for i in range(self.levels):
                tris=int(tris*self.ratio)
                lod=lodgen.build_lod(obj, arm, target_tris=tris, cap=self.cap)
                lod.name=f"{obj.name}_LOD{i+1}"
                lod.data.calc_loop_triangles()
                made.append((lod.name, len(lod.data.loop_triangles)))
        except Exception as e:
            self.report({'ERROR'}, str(e)); return {'CANCELLED'}
        self.report({'INFO'}, "; ".join(f"{n} {t} tris" for n,t in made))
        return {'FINISHED'}

def menu(self, ctx): self.layout.operator(OBJECT_OT_character_lod.bl_idname)
def register():
    bpy.utils.register_class(OBJECT_OT_character_lod)
    bpy.types.VIEW3D_MT_object.append(menu)
def unregister():
    bpy.types.VIEW3D_MT_object.remove(menu)
    bpy.utils.unregister_class(OBJECT_OT_character_lod)
