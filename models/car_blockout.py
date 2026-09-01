"""Body side as a low-poly quad cage, driven by Subsurf and Mirror.

The cage is a loft: cross-sections ("stations") along the length of the car,
each a run of six rings from the centreline of the top surface, out over the
shoulder, down the side, to the arch lip. Consecutive stations bridge into
quads. Smoothness comes from the Subdivision Surface modifier, not from vertex
count — the cage stays in the low tens of faces.

Only the left half exists. Mirror handles the other side, with clipping on so
the centreline seam welds rather than tearing open under subdivision. Modifier
order is Mirror then Subsurf; reversed, the centreline is rounded before it is
welded and the body splits down the middle.

Around the wheel openings every ring lifts with the arch, so the fender rides
above the wheel and the side tucks under it. Ring heights that ignore the arch
put the lower rings *below* the arch lip, which folds the surface back through
itself — invisible in a render, and it makes the arch measure 175mm shallower
than authored.

Detail lines are held by creases rather than by extra loops: the arch lip and
sill hard, the character line and beltline partial. See CREASE_LINES.

Front and rear are left open — they are modelled to meet this side next, so the
nose and tail rings are the boundary for now.

Real-world scale, metres. Car faces +X, up is +Z, mirrored across Y=0.
"""

import math
import bpy
import bmesh

PROPORTIONS = {
    "wheelbase":        2.65,
    "front_overhang":   0.90,
    "rear_overhang":    0.95,

    "wheel_radius":     0.34,
    "wheel_width":      0.28,
    "track_half":       0.81,

    "sill":             0.25,
    "arch_half_width":  0.42,   # elliptical, so the arch meets the sill cleanly
    "arch_height":      0.49,   # crown lands at 0.74

    "subdiv_viewport":  2,
    "subdiv_render":    3,
}

# x, z_top, (w1,z1) top-surface edge, (w2,z2) shoulder, (w3,z3) widest,
# (w4,z4) lower side. The final ring sits at the arch/sill line, whose height
# is computed, with its width given by w5.
#
# Over the arches the rings compress into the thin band between the fender top
# and the arch lip — which is what a low car with big wheels actually looks
# like, and what keeps the surface from folding.
STATIONS = [
    ( 2.225, 0.62, (0.30, 0.60), (0.62, 0.52), (0.70, 0.42), (0.68, 0.32), 0.62),
    ( 1.980, 0.72, (0.42, 0.70), (0.80, 0.60), (0.88, 0.46), (0.86, 0.33), 0.80),
    ( 1.745, 0.78, (0.48, 0.76), (0.88, 0.66), (0.94, 0.50), (0.92, 0.34), 0.86),
    ( 1.535, 0.82, (0.50, 0.80), (0.90, 0.740), (0.95, 0.712), (0.93, 0.690), 0.88),
    ( 1.325, 0.85, (0.52, 0.83), (0.90, 0.800), (0.95, 0.775), (0.93, 0.755), 0.88),
    ( 1.115, 0.88, (0.54, 0.86), (0.91, 0.780), (0.95, 0.720), (0.93, 0.695), 0.88),
    ( 0.905, 0.92, (0.55, 0.90), (0.93, 0.74), (0.95, 0.54), (0.93, 0.36), 0.88),
    ( 0.600, 0.98, (0.58, 0.96), (0.94, 0.78), (0.95, 0.56), (0.93, 0.37), 0.88),
    ( 0.050, 1.26, (0.42, 1.22), (0.92, 0.88), (0.95, 0.60), (0.93, 0.40), 0.88),
    (-0.550, 1.28, (0.44, 1.24), (0.93, 0.90), (0.95, 0.62), (0.93, 0.41), 0.88),
    (-0.905, 1.22, (0.44, 1.18), (0.94, 0.88), (0.95, 0.60), (0.93, 0.40), 0.88),
    (-1.115, 1.12, (0.46, 1.08), (0.94, 0.840), (0.96, 0.740), (0.94, 0.700), 0.88),
    (-1.325, 1.04, (0.50, 1.00), (0.94, 0.860), (0.96, 0.790), (0.94, 0.762), 0.88),
    (-1.535, 1.00, (0.52, 0.96), (0.93, 0.820), (0.95, 0.735), (0.93, 0.700), 0.87),
    (-1.745, 0.98, (0.52, 0.94), (0.90, 0.76), (0.92, 0.56), (0.90, 0.38), 0.84),
    (-2.020, 0.94, (0.50, 0.90), (0.86, 0.72), (0.88, 0.54), (0.86, 0.38), 0.80),
    (-2.275, 0.86, (0.44, 0.82), (0.76, 0.66), (0.78, 0.52), (0.76, 0.38), 0.70),
]

# Ring-following edge loops to crease, marking the detail lines. Values below
# 1.0 give a defined but soft line, which is what a character line wants — a
# fully creased one reads as damage. x_range limits a line to part of the car.
CREASE_LINES = [
    {"name": "sill_and_arch_lip", "ring": 5, "crease": 1.00},
    {"name": "character_line",    "ring": 3, "crease": 0.55},
    {"name": "beltline",          "ring": 2, "crease": 0.40, "x_range": (-1.05, 0.75)},
]

RING_SILL = 5


def _axles(p):
    return p["wheelbase"] / 2, -p["wheelbase"] / 2


def sill_height(x, p):
    """Bottom edge of the body side at x, lifting into an elliptical opening
    over each axle. Elliptical rather than circular so the arch meets the sill
    exactly, leaving no step to smooth away."""
    w, h = p["arch_half_width"], p["arch_height"]
    for cx in _axles(p):
        dx = x - cx
        if abs(dx) < w:
            return p["sill"] + h * math.sqrt(1.0 - (dx / w) ** 2)
    return p["sill"]


def station_rings(row, p):
    """The six (y, z) ring positions for one station, outboard side."""
    x, z_top, r1, r2, r3, r4, w5 = row
    return [
        (0.0, z_top),                      # on the mirror plane
        (-r1[0], r1[1]),
        (-r2[0], r2[1]),
        (-r3[0], r3[1]),
        (-r4[0], r4[1]),
        (-w5, sill_height(x, p)),
    ]


def check_folds(p=None):
    """Every station's rings must descend. A station that does not is folded
    back through itself, which no amount of creasing or extra loops will fix."""
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
        ring = line["ring"]
        lo, hi = line.get("x_range", (-1e9, 1e9))
        for s in range(len(grid) - 1):
            if not (lo <= STATIONS[s][0] <= hi and lo <= STATIONS[s + 1][0] <= hi):
                continue
            edge = bm.edges.get((grid[s][ring], grid[s + 1][ring]))
            if edge is not None:
                edge[crease] = line["crease"]

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def _wheel(name, x, y, p):
    # Proportion placeholder, replaced once real wheel data goes in — no subdiv.
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=24, radius=p["wheel_radius"], depth=p["wheel_width"],
        location=(x, y, p["wheel_radius"]), rotation=(math.pi / 2, 0, 0),
    )
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
    # Keeps the open nose, tail and arch boundaries from being pulled inward.
    subsurf.boundary_smooth = 'PRESERVE_CORNERS'

    fx, rx = _axles(p)
    t = p["track_half"]
    for name, x, y in [("wheel_FL", fx, -t), ("wheel_FR", fx, t),
                       ("wheel_RL", rx, -t), ("wheel_RR", rx, t)]:
        _wheel(name, x, y, p)

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
    """Lowest body surface directly over each axle, versus the top of the
    wheel. Positive means the wheel actually fits in its opening."""
    p = p or PROPORTIONS
    dg = bpy.context.evaluated_depsgraph_get()
    ev = body.evaluated_get(dg).to_mesh()
    out = {}
    for label, cx in zip(("front", "rear"), _axles(p)):
        zs = [v.co.z for v in ev.vertices if abs(v.co.x - cx) < 0.06 and v.co.y < 0]
        crown = min(zs) if zs else float("nan")
        out[label] = {"crown": round(crown, 3),
                      "clearance": round(crown - p["wheel_radius"] * 2, 3)}
    return out


if __name__ == "__main__":
    folds = check_folds()
    print("folded stations:", folds or "none")
    b = build(ground=False)
    print(poly_report(b))
    print("intended crown:", round(PROPORTIONS["sill"] + PROPORTIONS["arch_height"], 3))
    print(arch_clearance(b))
