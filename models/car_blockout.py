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
    "arch_front":       (0.560, 0.640),  # half-width along X, height above sill
    "arch_rear":        (0.560, 0.640),

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
# Rings down the side, outboard from the centreline. ACTIVE_RINGS is what
# actually gets built — a ring can be dropped from it and the creases still
# resolve, because they are keyed by name rather than by index.
# "shoulder" is deliberately absent. Once the apertures were cut it measured as
# costing 1mm of width for 17 faces and 18 vertices, and rendering with and
# without confirmed the surface reads the same — better, in fact, since it sat
# only 1.5% inboard of the character line and the two were fighting. Envelope
# measurements alone would not have settled it: they cannot see a design line
# disappear, so the renders were compared before it went.
RING_ORDER = ["top_centre", "top_edge", "shoulder", "character", "sill", "lip_inner"]
ACTIVE_RINGS = ["top_centre", "top_edge", "character", "sill", "lip_inner"]

# Tuned against the crease values recovered from Concept_Model_WIP4.blend,
# which run far harder than first assumed: 45% of edges creased, median 0.99,
# and two thirds of the creased edges at 0.90 or above. Matching that profile
# means the outline AND the character line are effectively hard, with only the
# shoulder and top edge left partial.
# Apertures cut out of the shell. `rings` names the band(s) of faces to leave
# unbuilt, indexed by the ring below them: 0 spans centreline to top edge,
# 1 top edge to shoulder, 2 shoulder to character, 3 character to sill,
# 4 sill to the wheel-well lip.
#
# Cutting these REDUCES the cage. Stations and rings that existed only to
# shape a region which is now a hole stop earning their place, so the count
# should fall as the openings go in, not climb.
APERTURES = [
    # Canopy opening, so the glass can be a separate shrinkwrapped patch.
    {"name": "cockpit",     "x": (-0.90,  0.30), "rings": ("top_centre",)},
    # Lower front intake.
    {"name": "grille",      "x": ( 1.97,  2.05), "rings": ("character",)},
    # Scoop ahead of the rear arch.
    {"name": "side_intake", "x": (-1.11, -0.84), "rings": ("character",)},
]


def _skip(x0, x1, ring):
    """`ring` indexes the band of faces above ring index `ring`. Apertures name
    the ring BELOW their band by name, so they survive ring pruning."""
    for ap in APERTURES:
        lo, hi = ap["x"]
        if not (lo <= x0 <= hi and lo <= x1 <= hi):
            continue
        for name in ap["rings"]:
            if name in ACTIVE_RINGS and ACTIVE_RINGS.index(name) == ring:
                return True
    return False


CREASE_BY_NAME = {
    "lip_inner": 1.00,
    "sill":      0.99,
    "character": 0.99,
    "shoulder":  0.45,
    "top_edge":  0.33,
}


def creases():
    return {ACTIVE_RINGS.index(n): v for n, v in CREASE_BY_NAME.items()
            if n in ACTIVE_RINGS}


# Body profile sampled off Concept_Model_WIP4.blend:
#   x, top-surface height at the centreline, half-width of the top-surface
#   edge, half-width at the widest point, and the bottom edge.
#
# Sampled in a wheelbase-CENTRED frame. Their file's origin is not at the
# wheelbase centre — the axles sit at -1.471 and +1.231, midpoint -0.120 — so
# an earlier pass that sampled against +/-1.351 had the whole profile shifted
# 120mm along the car relative to its own wheels.
#
# Three features the measurements forced, all of which had been modelled wrong:
#   - the nose tapers to a narrow low prow (0.339 half-width, 0.059 at the top
#     edge), not the blunt round bulb it had become;
#   - the canopy is a separate narrow structure standing on a wide body. It
#     rises 290mm across the 100mm between x=0.35 and x=0.25 while the top edge
#     pinches from 0.775 to 0.394. Both stations are needed or it ramps;
#   - the tail bottom lifts to 0.460 for the diffuser cutaway, rather than
#     running to the sill.
PROFILE = [
    ( 2.079, 0.490, 0.059, 0.339, 0.120),   # prow, capped
    ( 2.040, 0.516, 0.370, 0.410, 0.114),
    ( 1.980, 0.549, 0.479, 0.511, 0.105),
    ( 1.850, 0.622, 0.720, 0.898, 0.091),
    ( 1.600, 0.755, 0.817, 0.893, 0.091),
    ( 1.351, 0.791, 0.828, 0.893, 0.091),   # front axle
    # Stations at x = 0.850 and -0.400 removed: both sat on smooth runs and
    # cost nothing measurable once tested one at a time.
    ( 1.100, 0.800, 0.797, 0.894, 0.091),
    ( 0.350, 0.759, 0.775, 0.826, 0.095),   # cowl, base of the screen
    ( 0.250, 1.049, 0.394, 0.824, 0.095),   # top of the screen
    ( 0.000, 1.063, 0.494, 0.818, 0.095),   # canopy crown, mid-wheelbase
    (-0.850, 0.970, 0.449, 0.875, 0.095),
    (-1.100, 0.870, 0.739, 0.900, 0.091),
    (-1.351, 0.844, 0.766, 0.900, 0.091),   # rear axle
    (-1.600, 0.793, 0.746, 0.893, 0.131),
    (-1.800, 0.707, 0.715, 0.835, 0.184),
    (-1.942, 0.658, 0.649, 0.712, 0.460),   # tail, capped, diffuser cutaway
]

# Where the remaining lines sit between the top surface and the sill, as a
# fraction of the height available at that station. Fractions rather than
# absolute heights, so the lines stay clear of the arch automatically wherever
# the sill lifts — which is what folded the cage when the heights were fixed.
SHOULDER_F, CHARACTER_F = 0.58, 0.30
TOP_EDGE_F, SHOULDER_W, SILL_W = 0.06, 0.985, 0.930

STATIONS = [{"x": x, "top_z": tz, "edge_w": ew, "wide_w": ww, "bottom_z": bz}
            for x, tz, ew, ww, bz in PROFILE]


def _axles(p):
    return p["wheelbase"] / 2, -p["wheelbase"] / 2


def _bottom_at(x):
    """Measured bottom edge, interpolated between stations. Carries the tail's
    diffuser cutaway, which a flat sill line cannot."""
    xs = [row[0] for row in PROFILE]
    if x >= xs[0]:
        return PROFILE[0][4]
    if x <= xs[-1]:
        return PROFILE[-1][4]
    for i in range(len(xs) - 1):
        if xs[i] >= x >= xs[i + 1]:
            t = (xs[i] - x) / (xs[i] - xs[i + 1])
            return PROFILE[i][4] + t * (PROFILE[i + 1][4] - PROFILE[i][4])
    return PROFILE[-1][4]


def sill_height(x, p):
    """Bottom edge of the body side: the measured bottom line, lifted into an
    elliptical opening over each axle. Elliptical so the arch meets the sill
    exactly, with no step. Whichever is higher wins, so the arch survives at
    the axles and the diffuser cutaway survives at the tail."""
    base = _bottom_at(x)
    fx, rx = _axles(p)
    for cx, (w, h) in ((fx, p["arch_front"]), (rx, p["arch_rear"])):
        dx = x - cx
        if abs(dx) < w:
            return max(base, p["sill"] + h * math.sqrt(1.0 - (dx / w) ** 2))
    return base


def station_rings(row, p=None):
    """The (y, z) control points for one station, outboard side."""
    p = p or PROPORTIONS
    sill_z = sill_height(row["x"], p)
    top_z, wide = row["top_z"], row["wide_w"]
    span = max(top_z - sill_z, 1e-4)
    full = {
        "top_centre": (0.0, top_z),
        "top_edge":   (-row["edge_w"],     top_z - span * TOP_EDGE_F),
        "shoulder":   (-wide * SHOULDER_W, sill_z + span * SHOULDER_F),
        "character":  (-wide,              sill_z + span * CHARACTER_F),
        "sill":       (-wide * SILL_W,     sill_z),
        "lip_inner":  (-(wide * SILL_W - p["lip_inboard"]), sill_z + p["lip_rise"]),
    }
    return [full[name] for name in ACTIVE_RINGS]


def check_folds(p=None):
    p = p or PROPORTIONS
    # The lip turns back up on purpose, so it is excluded from the descent test.
    return vehicle_cage.check_folds(STATIONS, lambda r: station_rings(r, p)[:-1])


def _wheel(name, x, y, radius, width):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=24, radius=radius, depth=width,
        location=(x, y, radius), rotation=(math.pi / 2, 0, 0))
    bpy.context.active_object.name = name


def add_references(p=None, depth=1.4):
    """Background reference images, sized to the car. Viewport only — they do
    not render. Drop the photographs into refs/ beside the .blend.

    `span` is how much of each frame the car fills, which cannot be derived
    from the model; adjust per image if the framing differs.
    """
    from tools import reference_images as ri
    p = p or PROPORTIONS
    length = p["wheelbase"] + p["front_overhang"] + p["rear_overhang"]
    width = p["half_width"] * 2
    return [ri.add_reference(view, f"//refs/{view}.png", extent, span=span,
                             depth=depth)
            for view, extent, span in (("side",  length, 0.92),
                                       ("front", width,  0.72),
                                       ("rear",  width,  0.78))]


def build(p=None, ground=True, references=False):
    p = p or PROPORTIONS
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.unit_settings.system = 'METRIC'

    me = bpy.data.meshes.new("body_side")
    bm = vehicle_cage.build_cage(STATIONS, lambda r: station_rings(r, p), creases(),
                                 cap_ends=True, skip=_skip)
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

    if references:
        add_references(p)

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
