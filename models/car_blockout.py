"""PIX3L concept — mid-engine supercar, body side.

Styling from the supplied reference: cab-forward canopy well ahead of centre,
long rear deck over the engine, high haunches, an intake scoop carved in ahead
of the rear arch, squared arches under a hard shoulder, low pointed nose.

Dimensions are anchored to a Porsche 911 (992), not invented: wheelbase 2450,
width 1852, overall length 4519. The overhang split is mid-engine — shorter
front, longer rear deck — rather than the 911's own.

Construction lives in models/vehicle_cage.py and is generic. This file is only
the numbers: the envelope, and a (y, z) per profile line at each station.

Front and rear bodywork are still open; they get modelled to meet this side.

Real-world scale, metres. Car faces +X, up is +Z, mirrored across Y=0.
"""

import math
import bpy

from . import vehicle_cage

PROPORTIONS = {
    # Measured off Concept_Model_WIP4.blend rather than chosen. The earlier
    # "roughly the Porsche dimensions" envelope was 4519mm long; the actual
    # working model is 4026mm, on a longer 2702mm wheelbase with much shorter
    # overhangs and a far lower roof.
    "wheelbase":        2.702,
    "front_overhang":   0.732,
    "rear_overhang":    0.593,
    "half_width":       0.901,

    "wheel_r_front":    0.3335,
    "wheel_r_rear":     0.3335,
    "wheel_w_front":    0.208,
    "wheel_w_rear":     0.208,
    # Wheel outer face lands flush with the widest point of the body.
    "track_half_front": 0.797,
    "track_half_rear":  0.797,

    "sill":             0.091,
    "arch_front":       (0.500, 0.629),  # half-width along X, height above sill
    "arch_rear":        (0.500, 0.629),

    # The fender turning inboard into the wheel well, so the arch has thickness
    # rather than ending on a bare edge.
    "lip_inboard":      0.055,
    "lip_rise":         0.027,

    "subdiv_viewport":  2,
    "subdiv_render":    5,
}

# Ring order down the side, and how hard each is creased. The outline — the
# wheel-well lip and the sill — is hard. Design lines are moderate; a fully
# creased character line reads as damage rather than as a design line. Nothing
# else is creased, and nothing else exists: between the outlines the surface is
# a single smooth span.
RING = {"top_centre": 0, "top_edge": 1, "shoulder": 2,
        "character": 3, "sill": 4, "lip_inner": 5}

CREASES = {
    RING["lip_inner"]: 1.00,
    RING["sill"]:      0.85,
    RING["character"]: 0.55,
    RING["shoulder"]:  0.50,
    RING["top_edge"]:  0.30,
}


# Body profile measured off Concept_Model_WIP4.blend, not invented:
# x, top-surface height at the centreline, half-width of the top-surface edge,
# and half-width at the widest point. Axles sit at +/-1.351.
#
# Two things here were assumptions of mine that the file corrected. The canopy
# crowns at x = 0.00, the exact middle of the wheelbase, not forward of it. And
# the body pinches in through the cabin (0.824) while bulging at both arches
# (0.90), rather than running at near-constant width.
PROFILE = [
    ( 2.083, 0.579, 0.300, 0.700),
    ( 1.850, 0.713, 0.430, 0.898),
    ( 1.600, 0.785, 0.470, 0.893),
    ( 1.351, 0.799, 0.490, 0.893),
    ( 1.100, 0.800, 0.495, 0.894),
    ( 0.850, 0.786, 0.480, 0.855),
    ( 0.400, 1.051, 0.410, 0.825),
    ( 0.000, 1.063, 0.420, 0.824),
    (-0.400, 1.042, 0.430, 0.841),
    (-0.850, 0.920, 0.470, 0.896),
    (-1.100, 0.849, 0.500, 0.901),
    (-1.351, 0.833, 0.505, 0.899),
    (-1.600, 0.762, 0.490, 0.888),
    (-1.944, 0.680, 0.410, 0.760),
]

# Where the remaining lines sit between the top surface and the sill, as a
# fraction of the height available at that station. Fractions rather than
# absolute heights, so the lines stay clear of the arch automatically wherever
# the sill lifts — which is what folded the cage when the heights were fixed.
SHOULDER_F, CHARACTER_F, TOP_EDGE_F = 0.58, 0.30, 0.06
SHOULDER_W, SILL_W = 0.985, 0.930

STATIONS = [{"x": x, "top_z": tz, "edge_w": ew, "wide_w": ww}
            for x, tz, ew, ww in PROFILE]


def _axles(p):
    return p["wheelbase"] / 2, -p["wheelbase"] / 2


def sill_height(x, p):
    """Bottom edge of the body side, lifting into an elliptical opening over
    each axle. Elliptical so the arch meets the sill exactly, with no step."""
    fx, rx = _axles(p)
    for cx, (w, h) in ((fx, p["arch_front"]), (rx, p["arch_rear"])):
        dx = x - cx
        if abs(dx) < w:
            return p["sill"] + h * math.sqrt(1.0 - (dx / w) ** 2)
    return p["sill"]


def station_rings(row, p=None):
    """The (y, z) control points for one station, outboard side."""
    p = p or PROPORTIONS
    sill_z = sill_height(row["x"], p)
    top_z, wide = row["top_z"], row["wide_w"]
    span = max(top_z - sill_z, 1e-4)
    return [
        (0.0, top_z),
        (-row["edge_w"],       top_z - span * TOP_EDGE_F),
        (-wide * SHOULDER_W,   sill_z + span * SHOULDER_F),
        (-wide,                sill_z + span * CHARACTER_F),
        (-wide * SILL_W,       sill_z),
        (-(wide * SILL_W - p["lip_inboard"]), sill_z + p["lip_rise"]),
    ]


def check_folds(p=None):
    p = p or PROPORTIONS
    # The lip turns back up on purpose, so it is excluded from the descent test.
    return vehicle_cage.check_folds(STATIONS, lambda r: station_rings(r, p)[:-1])


def _wheel(name, x, y, radius, width):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=24, radius=radius, depth=width,
        location=(x, y, radius), rotation=(math.pi / 2, 0, 0))
    bpy.context.active_object.name = name


def build(p=None, ground=True):
    p = p or PROPORTIONS
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.unit_settings.system = 'METRIC'

    me = bpy.data.meshes.new("body_side")
    bm = vehicle_cage.build_cage(STATIONS, lambda r: station_rings(r, p), CREASES)
    bm.to_mesh(me)
    bm.free()

    body = bpy.data.objects.new("body_side", me)
    bpy.context.collection.objects.link(body)
    body.data.polygons.foreach_set("use_smooth", [True] * len(body.data.polygons))

    mirror = body.modifiers.new("mirror", 'MIRROR')
    mirror.use_axis = (False, True, False)
    mirror.use_clip = True
    mirror.merge_threshold = 1e-4

    subsurf = body.modifiers.new("subsurf", 'SUBSURF')
    subsurf.levels = p["subdiv_viewport"]
    subsurf.render_levels = p["subdiv_render"]
    subsurf.boundary_smooth = 'PRESERVE_CORNERS'

    fx, rx = _axles(p)
    _wheel("wheel_FL", fx, -p["track_half_front"], p["wheel_r_front"], p["wheel_w_front"])
    _wheel("wheel_FR", fx,  p["track_half_front"], p["wheel_r_front"], p["wheel_w_front"])
    _wheel("wheel_RL", rx, -p["track_half_rear"],  p["wheel_r_rear"],  p["wheel_w_rear"])
    _wheel("wheel_RR", rx,  p["track_half_rear"],  p["wheel_r_rear"],  p["wheel_w_rear"])

    if ground:
        length = p["wheelbase"] + p["front_overhang"] + p["rear_overhang"]
        bpy.ops.mesh.primitive_plane_add(size=length * 1.7, location=(0, 0, 0))
        bpy.context.active_object.name = "ground"

    return body


def poly_report(body):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = body.evaluated_get(dg).to_mesh()
    cage = len(body.data.polygons)
    quads = sum(1 for f in body.data.polygons if len(f.vertices) == 4)
    return {"cage_faces": cage, "cage_verts": len(body.data.vertices),
            "all_quads": quads == cage, "subdivided_faces": len(ev.polygons)}


def arch_clearance(body, p=None):
    p = p or PROPORTIONS
    dg = bpy.context.evaluated_depsgraph_get()
    ev = body.evaluated_get(dg).to_mesh()
    out = {}
    for label, cx, r in (("front", _axles(p)[0], p["wheel_r_front"]),
                         ("rear",  _axles(p)[1], p["wheel_r_rear"])):
        zs = [v.co.z for v in ev.vertices if abs(v.co.x - cx) < 0.06 and v.co.y < 0]
        crown = min(zs) if zs else float("nan")
        out[label] = {"crown": round(crown, 3), "clearance": round(crown - r * 2, 3)}
    return out


def dimensions(body, p=None):
    p = p or PROPORTIONS
    dg = bpy.context.evaluated_depsgraph_get()
    ev = body.evaluated_get(dg).to_mesh()
    xs = [v.co.x for v in ev.vertices]
    ys = [v.co.y for v in ev.vertices]
    zs = [v.co.z for v in ev.vertices]
    return {"length_mm": round((max(xs) - min(xs)) * 1000),
            "width_mm":  round((max(ys) - min(ys)) * 1000),
            "height_mm": round(max(zs) * 1000),
            "wheelbase_mm": round(p["wheelbase"] * 1000)}


if __name__ == "__main__":
    print("folded stations:", check_folds() or "none")
    b = build(ground=False)
    print(poly_report(b))
    print(arch_clearance(b))
    print(dimensions(b))
