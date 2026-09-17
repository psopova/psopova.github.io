bl_info = {"name":"Shape Key Transfer","author":"Arminas","version":(0,1,0),"blender":(4,2,0),
           "location":"Object > Shape Key Transfer","category":"Object",
           "description":"Transfer a shape key set between meshes with different topology, through deformation gradients"}
import bpy, numpy as np
from . import keytransfer

class OBJECT_OT_shapekey_transfer(bpy.types.Operator):
    bl_idname="object.shapekey_transfer"; bl_label="Shape Key Transfer"; bl_options={'REGISTER','UNDO'}
    neighbours: bpy.props.IntProperty(name="Neighbour triangles", default=6, min=1, max=24)
    falloff: bpy.props.FloatProperty(name="Falloff", default=0.05, min=0.005, max=0.5)

    @classmethod
    def poll(cls, ctx):
        sel=[o for o in ctx.selected_objects if o.type=='MESH']
        return len(sel)==2 and ctx.active_object in sel

    def execute(self, ctx):
        dst=ctx.active_object
        src=[o for o in ctx.selected_objects if o.type=='MESH' and o is not dst][0]
        if not src.data.shape_keys:
            self.report({'ERROR'}, f"{src.name} has no shape keys"); return {'CANCELLED'}
        kb=src.data.shape_keys.key_blocks
        basis=np.array([tuple(p.co) for p in kb[0].data])
        if not dst.data.shape_keys: dst.shape_key_add(name="Basis")
        made=0
        for k in kb[1:]:
            cos=np.array([tuple(p.co) for p in k.data])
            try:
                out=keytransfer.transfer(src.data, cos, dst.data, k=self.neighbours, sigma_frac=self.falloff)
            except Exception as e:
                self.report({'ERROR'}, f"{k.name}: {e}"); return {'CANCELLED'}
            nk=dst.data.shape_keys.key_blocks.get(k.name) or dst.shape_key_add(name=k.name)
            nk.slider_min, nk.slider_max = k.slider_min, k.slider_max
            for i in range(len(out)): nk.data[i].co = out[i]
            made+=1
        self.report({'INFO'}, f"transferred {made} shape keys from {src.name} to {dst.name}")
        return {'FINISHED'}

def menu(self, ctx): self.layout.operator(OBJECT_OT_shapekey_transfer.bl_idname)
def register():
    bpy.utils.register_class(OBJECT_OT_shapekey_transfer)
    bpy.types.VIEW3D_MT_object.append(menu)
def unregister():
    bpy.types.VIEW3D_MT_object.remove(menu)
    bpy.utils.unregister_class(OBJECT_OT_shapekey_transfer)
