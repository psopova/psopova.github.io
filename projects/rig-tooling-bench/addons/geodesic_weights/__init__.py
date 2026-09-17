bl_info = {"name": "Geodesic Weights", "author": "Arminas", "version": (0,1,0),
           "blender": (4,2,0), "location": "Object > Parent > Geodesic Weights",
           "description": "Bind a mesh to an armature using geodesic surface distance",
           "category": "Rigging"}
import bpy
from . import geoweight

class OBJECT_OT_geodesic_weights(bpy.types.Operator):
    bl_idname = "object.geodesic_weights"; bl_label = "Geodesic Weights"
    bl_options = {'REGISTER','UNDO'}
    cap: bpy.props.IntProperty(name="Max influences", default=4, min=1, max=8)
    falloff: bpy.props.FloatProperty(name="Falloff", default=10.0, min=1.0, max=32.0)
    smooth_iters: bpy.props.IntProperty(name="Smoothing", default=40, min=0, max=200)
    smooth_lambda: bpy.props.FloatProperty(name="Smooth strength", default=0.6, min=0.0, max=1.0)

    @classmethod
    def poll(cls, ctx):
        o = ctx.active_object
        return o and o.type=='MESH' and o.parent and o.parent.type=='ARMATURE'

    def execute(self, ctx):
        obj = ctx.active_object; arm = obj.parent
        try:
            w = geoweight.compute(obj, arm, cap=self.cap, falloff=self.falloff,
                                  exclusive_seeds=False, smooth_iters=self.smooth_iters,
                                  smooth_lambda=self.smooth_lambda)
            geoweight.apply_to(obj, w)
        except Exception as e:
            self.report({'ERROR'}, str(e)); return {'CANCELLED'}
        self.report({'INFO'}, f"bound {len(obj.data.vertices)} vertices to {len(w)} bones")
        return {'FINISHED'}

def menu(self, ctx): self.layout.operator(OBJECT_OT_geodesic_weights.bl_idname)
def register():
    bpy.utils.register_class(OBJECT_OT_geodesic_weights)
    bpy.types.VIEW3D_MT_object_parent.append(menu)
def unregister():
    bpy.types.VIEW3D_MT_object_parent.remove(menu)
    bpy.utils.unregister_class(OBJECT_OT_geodesic_weights)
if __name__ == "__main__": register()
