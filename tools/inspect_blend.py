"""Read a .blend and report what its meshes are actually made of.

The point is to learn from someone else's file precisely rather than by eye:
where the loops sit, which edges carry crease, how the modifier stack is
ordered, whether the cage is clean. Run it on their file and on ours, and the
differences are the lesson.
"""

import sys
from collections import Counter

import bpy


def modifier_stack(obj):
    out = []
    for m in obj.modifiers:
        entry = {"name": m.name, "type": m.type}
        if m.type == 'SUBSURF':
            entry.update(levels=m.levels, render=m.render_levels,
                         type_=m.subdivision_type, boundary=m.boundary_smooth)
        elif m.type == 'MIRROR':
            entry.update(axis=tuple(m.use_axis), clip=m.use_clip)
        elif m.type == 'SOLIDIFY':
            entry.update(thickness=round(m.thickness, 4))
        elif m.type == 'BEVEL':
            entry.update(width=round(m.width, 4), segments=m.segments)
        elif m.type == 'SHRINKWRAP':
            entry.update(target=getattr(m.target, "name", None), mode=m.wrap_method)
        out.append(entry)
    return out


def creases(mesh):
    """Crease values present, and how many edges carry each."""
    attr = mesh.attributes.get("crease_edge")
    if attr is None:
        return {}
    tally = Counter(round(d.value, 2) for d in attr.data if d.value > 0.0)
    return dict(sorted(tally.items(), reverse=True))


def poles(mesh):
    """Vertices by how many edges meet at them. Interior 5-poles and 3-poles are
    where subdivision pinches, so they are worth seeing."""
    valence = Counter()
    for v in mesh.vertices:
        valence[len([e for e in mesh.edges if v.index in e.vertices])] += 1
    return dict(sorted(valence.items()))


def report(mesh_obj, with_poles=False):
    me = mesh_obj.data
    counts = Counter(len(p.vertices) for p in me.polygons)
    dims = mesh_obj.dimensions
    out = {
        "object": mesh_obj.name,
        "verts": len(me.vertices),
        "faces": len(me.polygons),
        "face_sizes": {f"{k}-gon": v for k, v in sorted(counts.items())},
        "all_quads": set(counts) <= {4},
        "dimensions_mm": [round(d * 1000) for d in dims],
        "modifiers": modifier_stack(mesh_obj),
        "creases": creases(me),
    }
    if with_poles:
        out["valence"] = poles(me)
    return out


def inspect(path, with_poles=False):
    bpy.ops.wm.open_mainfile(filepath=path)
    return [report(o, with_poles) for o in bpy.data.objects if o.type == 'MESH']


if __name__ == "__main__":
    import json
    path = sys.argv[1]
    for r in inspect(path, with_poles="--poles" in sys.argv):
        print(json.dumps(r, indent=2))
