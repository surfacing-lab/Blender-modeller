"""Material preset matching the reference: deep blue metallic, dark glass.

Presentation only — nothing here changes geometry. Clay renders stay the way
to judge form; this is for seeing whether the thing reads like the design.
"""

import bpy


def _principled(name, base, roughness=0.4, metallic=0.0, transmission=0.0,
                coat=0.0):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    b = mat.node_tree.nodes.get("Principled BSDF")
    if b:
        b.inputs["Base Color"].default_value = base
        b.inputs["Roughness"].default_value = roughness
        b.inputs["Metallic"].default_value = metallic
        for key, value in (("Transmission Weight", transmission),
                           ("Coat Weight", coat)):
            if key in b.inputs:
                b.inputs[key].default_value = value
    return mat


def apply(body="body_side", canopy="glass_canopy"):
    paint = _principled("paint_blue", (0.012, 0.055, 0.20, 1.0),
                        roughness=0.16, metallic=0.85, coat=1.0)
    glass = _principled("glass_dark", (0.02, 0.025, 0.035, 1.0),
                        roughness=0.05, transmission=0.75)
    liner = _principled("arch_liner", (0.03, 0.03, 0.034, 1.0), roughness=0.75)
    targets = [(body, paint), (canopy, glass)]
    targets += [(o.name, liner) for o in bpy.data.objects
                if o.name.startswith("arch_")]
    for name, mat in targets:
        ob = bpy.data.objects.get(name)
        if ob:
            ob.data.materials.clear()
            ob.data.materials.append(mat)
    return {"paint": paint, "glass": glass}
