"""PIX3L concept — mid-engine supercar, body side blocked out.

Styling comes from the reference images: cab-forward canopy pushed well ahead
of centre, long rear deck over the engine, high haunches, a deep intake scoop
carved in ahead of the rear arch, squared-off arches under a hard shoulder
line, low pointed nose, deep dark sill.

Dimensions are anchored to a Porsche 911 (992) rather than invented:
wheelbase 2450, width 1852, overall length 4519. The overhang split is
mid-engine (shorter front, longer rear deck) rather than the 911's own.

The cage is a loft through cross-sections, six rings each, running from the
centreline of the top surface out over the shoulder, down the side, to the arch
lip. Smoothness comes from Subsurf, not vertex count. Only the left half
exists; Mirror handles the rest, clipping on so the seam welds. Modifier order
is Mirror then Subsurf.

Around the wheel openings every ring lifts with the arch, so the fender rides
over the wheel and the side tucks under it. Rings authored at fixed heights
that ignore the arch fold the surface back through itself — see check_folds.

Front and rear are still open; they get modelled to meet this side next.

Real-world scale, metres. Car faces +X, up is +Z, mirrored across Y=0.
"""

import math
import bpy
import bmesh

PROPORTIONS = {
    # Envelope, from the 992.
    "wheelbase":        2.450,
    "front_overhang":   0.880,
    "rear_overhang":    1.189,   # long rear deck: mid-engine, not 911
    "half_width":       0.926,   # 1852mm overall

    # Staggered wheels, as in the reference.
    "wheel_r_front":    0.340,
    "wheel_r_rear":     0.355,
    "wheel_w_front":    0.300,
    "wheel_w_rear":     0.340,
    "track_half_front": 0.775,
    "track_half_rear":  0.755,

    "sill":             0.20,
    # Per-axle arch openings (half-width along X, height above the sill).
    "arch_front":       (0.46, 0.53),
    "arch_rear":        (0.46, 0.56),

    "subdiv_viewport":  2,
    "subdiv_render":    4,
}

# x, z_top, (w1,z1) top edge, (w2,z2) shoulder, (w3,z3) widest,
# (w4,z4) lower side, w5 at the arch/sill line (height computed).
STATIONS = [
    ( 2.105, 0.48, (0.26, 0.46), (0.55, 0.42), (0.66, 0.34), (0.64, 0.26), 0.58),
    ( 1.900, 0.62, (0.38, 0.60), (0.72, 0.54), (0.85, 0.42), (0.83, 0.28), 0.78),
    ( 1.685, 0.72, (0.46, 0.70), (0.82, 0.62), (0.91, 0.46), (0.89, 0.29), 0.84),
    ( 1.455, 0.79, (0.50, 0.775), (0.88, 0.745), (0.925, 0.715), (0.905, 0.690), 0.86),
    ( 1.225, 0.84, (0.52, 0.830), (0.89, 0.805), (0.926, 0.775), (0.906, 0.748), 0.86),
    ( 0.995, 0.88, (0.54, 0.860), (0.90, 0.780), (0.926, 0.710), (0.906, 0.675), 0.86),
    ( 0.765, 0.92, (0.56, 0.90), (0.91, 0.74), (0.926, 0.52), (0.900, 0.30), 0.85),
    ( 0.500, 1.02, (0.56, 0.99), (0.90, 0.76), (0.920, 0.52), (0.890, 0.30), 0.84),
    ( 0.200, 1.22, (0.46, 1.16), (0.88, 0.80), (0.910, 0.54), (0.880, 0.31), 0.83),
    (-0.250, 1.27, (0.48, 1.21), (0.90, 0.82), (0.920, 0.55), (0.890, 0.31), 0.83),
    (-0.600, 1.22, (0.50, 1.16), (0.91, 0.82), (0.880, 0.56), (0.840, 0.32), 0.82),
    (-0.765, 1.16, (0.52, 1.10), (0.92, 0.82), (0.850, 0.56), (0.820, 0.32), 0.82),
    (-0.995, 1.08, (0.54, 1.02), (0.90, 0.860), (0.925, 0.760), (0.905, 0.710), 0.87),
    (-1.225, 1.05, (0.56, 1.00), (0.90, 0.885), (0.925, 0.830), (0.905, 0.790), 0.87),
    (-1.455, 0.99, (0.55, 0.95), (0.90, 0.850), (0.925, 0.770), (0.905, 0.710), 0.87),
    (-1.685, 0.95, (0.53, 0.92), (0.88, 0.80), (0.900, 0.56), (0.870, 0.32), 0.82),
    (-2.050, 0.92, (0.50, 0.89), (0.84, 0.76), (0.860, 0.54), (0.830, 0.32), 0.78),
    (-2.414, 0.86, (0.44, 0.83), (0.74, 0.70), (0.760, 0.52), (0.730, 0.34), 0.68),
]

# The scoop ahead of the rear arch is the two stations where ring 3 pulls
# inboard of ring 2 (x = -0.600 and -0.765) — the side surface undercutting
# the shoulder, which is what makes the intake read.

CREASE_LINES = [
    {"name": "sill_and_arch_lip", "ring": 5, "crease": 1.00},
    {"name": "shoulder",          "ring": 2, "crease": 0.55},
    {"name": "character_line",    "ring": 3, "crease": 0.45},
]


def _axles(p):
    return p["wheelbase"] / 2, -p["wheelbase"] / 2


def sill_height(x, p):
    """Bottom edge of the body side, lifting into an elliptical opening over
    each axle. Elliptical so the arch meets the sill exactly, no step."""
    fx, rx = _axles(p)
    for cx, (w, h) in ((fx, p["arch_front"]), (rx, p["arch_rear"])):
        dx = x - cx
        if abs(dx) < w:
            return p["sill"] + h * math.sqrt(1.0 - (dx / w) ** 2)
    return p["sill"]


def station_rings(row, p):
    x, z_top, r1, r2, r3, r4, w5 = row
    return [(0.0, z_top), (-r1[0], r1[1]), (-r2[0], r2[1]),
            (-r3[0], r3[1]), (-r4[0], r4[1]), (-w5, sill_height(x, p))]


def check_folds(p=None):
    """Rings must descend at every station. One that does not is folded back
    through itself — invisible in a render, fatal to the surface."""
    p = p or PROPORTIONS
    bad = []
    for row in STATIONS:
        zs = [z for _, z in station_rings(row, p)]
        if any(zs[i] < zs[i + 1] - 1e-9 for i in range(len(zs) - 1)):
            bad.append((row[0], [round(z, 3) for z in zs]))
    return bad


def _cage(p):
    bm = bmesh.new()
    grid = [[bm.verts.new((row[0], y, z)) for y, z in station_rings(row, p)]
            for row in STATIONS]
    for s in range(len(grid) - 1):
        for r in range(len(grid[0]) - 1):
            bm.faces.new((grid[s][r], grid[s][r + 1],
                          grid[s + 1][r + 1], grid[s + 1][r]))

    crease = bm.edges.layers.float.new("crease_edge")
    for line in CREASE_LINES:
        lo, hi = line.get("x_range", (-1e9, 1e9))
        for s in range(len(grid) - 1):
            if not (lo <= STATIONS[s][0] <= hi and lo <= STATIONS[s + 1][0] <= hi):
                continue
            edge = bm.edges.get((grid[s][line["ring"]], grid[s + 1][line["ring"]]))
            if edge is not None:
                edge[crease] = line["crease"]

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


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
    bm = _cage(p)
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
    return {"cage_faces": cage, "cage_quads": quads,
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
    """Overall envelope of the finished body, to check against the target."""
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
