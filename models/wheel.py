"""Parametric wheel — tyre, rim barrel, spoked face, brake disc.

Low poly with Subsurf doing the rounding, as everywhere else. The tyre is a
revolved profile; the spoke gaps are cut the same way the body's openings are,
by omitting sectors of an annulus rather than by booleaning holes.

Axis runs along Y, matching the car. Real-world scale, metres.
"""

import math
import bmesh
import bpy

# (radius, y) around the tyre's cross-section, outboard to inboard. The tread
# stays at full radius across its width; the sidewalls tuck in to the bead.
TYRE_PROFILE = [
    (0.238, -0.075), (0.262, -0.098), (0.305, -0.104),
    (0.334, -0.088), (0.334,  0.000), (0.334,  0.088),
    (0.305,  0.104), (0.262,  0.098), (0.238,  0.075),
]

# Radius of each ring across the rim face, hub outwards, with how far each sits
# outboard. The face dishes: the hub sits deeper than the lip.
FACE_RINGS = [(0.070, -0.020), (0.130, -0.045), (0.190, -0.062), (0.232, -0.074)]

SECTORS_PER_SPOKE = 4      # of which the first two carry material
SPOKES = 5


def _revolve(bm, profile, segments, crease_at=(), crease=0.0):
    """Revolve a (radius, y) profile about the Y axis into a quad tube."""
    rings = []
    for i in range(segments):
        a = 2 * math.pi * i / segments
        c, s = math.cos(a), math.sin(a)
        rings.append([bm.verts.new((r * c, y, r * s)) for r, y in profile])
    for i in range(segments):
        j = (i + 1) % segments
        for k in range(len(profile) - 1):
            bm.faces.new((rings[i][k], rings[i][k + 1],
                          rings[j][k + 1], rings[j][k]))
    if crease and crease_at:
        layer = bm.edges.layers.float.get("crease_edge") or \
                bm.edges.layers.float.new("crease_edge")
        for i in range(segments):
            j = (i + 1) % segments
            for k in crease_at:
                e = bm.edges.get((rings[i][k], rings[j][k]))
                if e:
                    e[layer] = crease
    return rings


def _spoked_face(bm, rings_spec, spokes, per_spoke):
    """An annulus with sectors left out, which is what makes the spokes."""
    segments = spokes * per_spoke
    grid = []
    for i in range(segments):
        a = 2 * math.pi * i / segments
        c, s = math.cos(a), math.sin(a)
        grid.append([bm.verts.new((r * c, y, r * s)) for r, y in rings_spec])
    made = []
    for i in range(segments):
        # Two sectors of every four carry material; the rest are the gaps.
        if i % per_spoke >= 2:
            continue
        j = (i + 1) % segments
        for k in range(len(rings_spec) - 1):
            made.append(bm.faces.new((grid[i][k], grid[i][k + 1],
                                      grid[j][k + 1], grid[j][k])))
    return made


def build(name="wheel", segments=16, radius_scale=1.0, width_scale=1.0,
          subdiv=(2, 3)):
    bm = bmesh.new()
    profile = [(r * radius_scale, y * width_scale) for r, y in TYRE_PROFILE]
    # Crease the tread shoulders so the tyre keeps a defined edge rather than
    # rounding off into a doughnut.
    _revolve(bm, profile, segments, crease_at=(3, 5), crease=0.6)

    # Rim barrel, bead to bead, behind the tyre.
    barrel = [(0.236 * radius_scale, -0.074 * width_scale),
              (0.236 * radius_scale,  0.074 * width_scale)]
    _revolve(bm, barrel, segments)

    face_rings = [(r * radius_scale, y * width_scale) for r, y in FACE_RINGS]
    _spoked_face(bm, face_rings, SPOKES, SECTORS_PER_SPOKE)

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    # Slot 0 is the tyre, slot 1 the rim. The tyre revolve is laid down first,
    # so its faces are the leading run and everything after is rim.
    tyre_faces = segments * (len(profile) - 1)
    bm.faces.ensure_lookup_table()
    for i, f in enumerate(bm.faces):
        f.material_index = 0 if i < tyre_faces else 1

    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))

    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    sub = ob.modifiers.new("subsurf", 'SUBSURF')
    sub.levels, sub.render_levels = subdiv
    sub.boundary_smooth = 'PRESERVE_CORNERS'
    return ob


def materials(ob, tyre=(0.035, 0.035, 0.038, 1.0), rim=(0.62, 0.44, 0.22, 1.0)):
    """Two slots, matching the reference's dark rubber and bronze rims."""
    for slot_name, colour, rough, metal in (("tyre", tyre, 0.85, 0.0),
                                            ("rim", rim, 0.28, 1.0)):
        mat = bpy.data.materials.get(slot_name) or bpy.data.materials.new(slot_name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = colour
            bsdf.inputs["Roughness"].default_value = rough
            bsdf.inputs["Metallic"].default_value = metal
        ob.data.materials.append(mat)
    return ob


def place(ob, x, y, z, mirror_y=False):
    ob.location = (x, y, z)
    if mirror_y:
        ob.scale = (1.0, -1.0, 1.0)
    return ob
