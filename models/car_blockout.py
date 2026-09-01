"""Stage 1 of the build: body side profile, then wheels as cylinders.

Follows the stated build order — the side is the first surface, the wheels go
in immediately as plain cylinders so stance and proportion can be judged before
any detail exists. Front and rear are deliberately absent; they get modelled to
meet this side later.

Everything is driven from PROPORTIONS so the form can be pushed around across
iterations without touching construction code. Real-world scale, metres.
Car faces +X, up is +Z, mirrored across Y=0.
"""

import math
import bpy
import bmesh

PROPORTIONS = {
    # Plan
    "wheelbase":        2.65,
    "front_overhang":   0.90,
    "rear_overhang":    0.95,
    "half_width":       0.95,   # widest point of the body
    "panel_thickness":  0.04,

    # Wheels
    "wheel_radius":     0.34,
    "wheel_width":      0.28,
    "arch_radius":      0.40,   # wheel radius + gap
    "track_half":       0.81,   # wheel centreline from Y=0

    # Side elevation, as heights above ground
    "sill":             0.25,
    "nose_low":         0.30,
    "nose_high":        0.68,
    "hood_front":       0.80,
    "hood_rear":        0.92,
    "cowl":             0.98,
    "screen_top":       1.22,
    "roof_peak":        1.28,
    "roof_rear":        1.22,
    "backlight_base":   1.02,
    "decklid":          0.98,
    "tail_top":         0.86,
    "tail_low":         0.55,
    "rear_valance":     0.38,
}


def _axles(p):
    return p["wheelbase"] / 2, -p["wheelbase"] / 2


def _arch_arc(cx, cz, r, z_bottom, segments=14):
    """Half-arch opening: enters at the body's bottom edge, sweeps over the top,
    exits at the bottom edge again. Returned front-to-rear (decreasing x)."""
    # Where the arch circle meets the bottom edge of the body.
    sin_t = max(-1.0, min(1.0, (z_bottom - cz) / r))
    t0 = math.asin(sin_t)              # front side, just below centre height
    t1 = math.pi - t0                  # rear side, mirrored over the top
    return [
        (cx + r * math.cos(t0 + (t1 - t0) * i / segments),
         cz + r * math.sin(t0 + (t1 - t0) * i / segments))
        for i in range(segments + 1)
    ]


def side_profile(p):
    """Closed outline of the body side in the XZ plane, including wheel arches."""
    fx, rx = _axles(p)
    nose = fx + p["front_overhang"]
    tail = rx - p["rear_overhang"]
    sill = p["sill"]

    # Underside, running front to rear, interrupted by both arches.
    bottom = [(nose - 0.02, p["nose_low"])]
    bottom += _arch_arc(fx, p["wheel_radius"], p["arch_radius"], sill)
    bottom += [(0.30, sill), (-0.30, sill)]
    bottom += _arch_arc(rx, p["wheel_radius"], p["arch_radius"], sill)
    bottom += [(tail + 0.05, p["rear_valance"])]

    # Upper surface, running rear to front: tail, decklid, backlight, roof,
    # screen, hood, nose.
    top = [
        (tail,          p["tail_low"]),
        (tail,          p["tail_top"]),
        (rx - 0.73,     p["decklid"]),
        (rx - 0.28,     p["backlight_base"]),
        (rx + 0.37,     p["roof_rear"]),
        (rx + 0.88,     p["roof_peak"]),
        (fx - 0.90,     p["screen_top"]),
        (fx - 0.62,     p["cowl"]),
        (fx - 0.20,     p["hood_rear"]),
        (fx + 0.42,     p["hood_front"]),
        (nose - 0.14,   p["nose_high"]),
        (nose,          0.52),
    ]
    return bottom + top


def _mesh_from_profile(name, points, y, thickness):
    """Turn the 2D outline into a solid panel by filling it and extruding in Y."""
    bm = bmesh.new()
    verts = [bm.verts.new((x, y, z)) for x, z in points]
    face = bm.faces.new(verts)
    bmesh.ops.triangulate(bm, faces=[face])           # concave outline needs it
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    ret = bmesh.ops.extrude_face_region(bm, geom=bm.faces[:])
    moved = [e for e in ret["geom"] if isinstance(e, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, verts=moved, vec=(0, thickness, 0))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()

    obj = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(obj)
    return obj


def _wheel(name, x, y, p):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=32,
        radius=p["wheel_radius"],
        depth=p["wheel_width"],
        location=(x, y, p["wheel_radius"]),
        rotation=(math.pi / 2, 0, 0),   # lay the axis along Y
    )
    obj = bpy.context.active_object
    obj.name = name
    return obj


def build(p=None):
    p = p or PROPORTIONS
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.unit_settings.system = 'METRIC'

    side = _mesh_from_profile(
        "body_side", side_profile(p),
        y=-p["half_width"], thickness=p["panel_thickness"],
    )
    mirror = side.modifiers.new("mirror", 'MIRROR')
    mirror.use_axis = (False, True, False)

    fx, rx = _axles(p)
    t = p["track_half"]
    for name, x, y in [
        ("wheel_FL", fx, -t), ("wheel_FR", fx, t),
        ("wheel_RL", rx, -t), ("wheel_RR", rx, t),
    ]:
        _wheel(name, x, y, p)

    length = p["wheelbase"] + p["front_overhang"] + p["rear_overhang"]
    bpy.ops.mesh.primitive_plane_add(size=length * 1.7, location=(0, 0, 0))
    bpy.context.active_object.name = "ground"

    return side


if __name__ == "__main__":
    build()
    print("blockout built")
