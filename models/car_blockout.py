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
    "wheelbase":        2.450,
    "front_overhang":   0.880,
    "rear_overhang":    1.189,
    "half_width":       0.926,

    "wheel_r_front":    0.340,
    "wheel_r_rear":     0.355,
    "wheel_w_front":    0.300,
    "wheel_w_rear":     0.340,
    "track_half_front": 0.775,
    "track_half_rear":  0.755,

    "sill":             0.20,
    "arch_front":       (0.46, 0.53),   # half-width along X, height above sill
    "arch_rear":        (0.46, 0.56),

    # The fender turning inboard into the wheel well, so the arch has thickness
    # rather than ending on a bare edge.
    "lip_inboard":      0.060,
    "lip_rise":         0.030,

    "subdiv_viewport":  2,
    "subdiv_render":    4,
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


def _S(x, top, edge, shoulder, character, w_sill):
    return {"x": x, "top_centre": (0.0, top), "top_edge": edge,
            "shoulder": shoulder, "character": character, "w_sill": w_sill}


# x, top-centre height, then (half-width, height) per line. Sill and lip
# heights are computed from the arch, so the sill gives only its width.
#
# Stations only exist where they change the form. Three more were tried and
# removed — at x = 1.900, 0.500 and -2.050 — because dropping them left length,
# height and both arch clearances identical to the millimetre. The station at
# x = -0.250 looks equally redundant but is not: it carries the canopy crown,
# and without it overall height drops by 38mm.
STATIONS = [
    _S( 2.105, 0.48, (0.26, 0.46),  (0.55, 0.42),  (0.66, 0.34),  0.58),
    _S( 1.685, 0.72, (0.46, 0.70),  (0.82, 0.62),  (0.91, 0.46),  0.84),
    _S( 1.455, 0.79, (0.50, 0.775), (0.88, 0.745), (0.925, 0.715), 0.86),
    _S( 1.225, 0.84, (0.52, 0.830), (0.89, 0.805), (0.926, 0.775), 0.86),
    _S( 0.995, 0.88, (0.54, 0.860), (0.90, 0.780), (0.926, 0.710), 0.86),
    _S( 0.765, 0.92, (0.56, 0.90),  (0.91, 0.74),  (0.926, 0.52), 0.85),
    _S( 0.200, 1.22, (0.46, 1.16),  (0.88, 0.80),  (0.910, 0.54), 0.83),
    _S(-0.250, 1.27, (0.48, 1.21),  (0.90, 0.82),  (0.920, 0.55), 0.83),
    # Character line pulled inboard of the shoulder here and at the next
    # station — the side undercutting, which is what makes the scoop read.
    _S(-0.600, 1.22, (0.50, 1.16),  (0.91, 0.82),  (0.880, 0.56), 0.82),
    _S(-0.765, 1.16, (0.52, 1.10),  (0.92, 0.82),  (0.850, 0.56), 0.82),
    _S(-0.995, 1.08, (0.54, 1.02),  (0.90, 0.860), (0.925, 0.760), 0.87),
    _S(-1.225, 1.05, (0.56, 1.00),  (0.90, 0.885), (0.925, 0.830), 0.87),
    _S(-1.455, 0.99, (0.55, 0.95),  (0.90, 0.850), (0.925, 0.770), 0.87),
    _S(-1.685, 0.95, (0.53, 0.92),  (0.88, 0.80),  (0.900, 0.56), 0.82),
    _S(-2.414, 0.86, (0.44, 0.83),  (0.74, 0.70),  (0.760, 0.52), 0.68),
]


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
    w = row["w_sill"]
    return [
        row["top_centre"],
        (-row["top_edge"][0],  row["top_edge"][1]),
        (-row["shoulder"][0],  row["shoulder"][1]),
        (-row["character"][0], row["character"][1]),
        (-w, sill_z),
        (-(w - p["lip_inboard"]), sill_z + p["lip_rise"]),
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
