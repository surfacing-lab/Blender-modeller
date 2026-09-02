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
RING_ORDER = ["top_centre", "top_edge", "flare", "waist", "rocker", "floor"]
ACTIVE_RINGS = list(RING_ORDER)

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
    {"name": "cockpit",    "x": (-0.90,  0.30), "rings": ("top_centre",)},
    # Wheel wells: the gap between the flare above and the tub inboard. This
    # is what a wheel arch actually is on the reference — not a scallop cut up
    # from a sill line, which is what it had been.
    {"name": "well_front", "x": ( 0.93,  1.77), "rings": ("flare",)},
    {"name": "well_rear",  "x": (-1.77, -0.93), "rings": ("flare",)},
    # Lower front intake, and the scoop ahead of the rear arch.
    {"name": "grille",     "x": ( 1.85,  2.00), "rings": ("waist",)},
    {"name": "side_scoop", "x": (-0.90, -0.55), "rings": ("waist",)},
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
    "floor":     1.00,   # bottom outline
    "flare":     0.99,   # the fender line — the hard edge the whole car hangs on
    "waist":     0.60,
    "top_edge":  0.33,
}


def creases():
    return {ACTIVE_RINGS.index(n): v for n, v in CREASE_BY_NAME.items()
            if n in ACTIVE_RINGS}


# Section widths sampled off Concept_Model_WIP4.blend at fixed heights:
#   x, top-surface height, then half-width of the top edge, the flare, the
#   waist, the rocker and the floor.
#
# The architecture this captures is the thing that was missing. The reference
# is a NARROW CENTRAL TUB with WIDE FENDER FLARES bursting out at the top, and
# the wheel sits in the gap between them — at the front axle the tub is 0.56
# half-width while the flare above it reaches 0.88. Between the axles the body
# fills out to about 0.85, with the side tucked IN to a waist at mid-height.
#
# Modelling it as one width at every height gives a slab with holes cut in it,
# which is what it was, and no amount of profile or crease tuning rescues that.
PROFILE = [
    ( 2.079, 0.58, 0.06, 0.33, 0.30, 0.30, 0.26),   # prow
    ( 1.900, 0.74, 0.45, 0.83, 0.83, 0.78, 0.62),
    ( 1.700, 0.82, 0.50, 0.85, 0.86, 0.88, 0.70),
    ( 1.500, 0.96, 0.52, 0.87, 0.57, 0.57, 0.50),   # tub narrows, flare stays
    ( 1.351, 0.97, 0.53, 0.88, 0.56, 0.58, 0.50),   # front axle
    ( 1.150, 0.97, 0.53, 0.89, 0.60, 0.67, 0.56),
    ( 0.900, 0.97, 0.54, 0.86, 0.88, 0.85, 0.70),
    ( 0.500, 0.92, 0.55, 0.80, 0.73, 0.79, 0.66),
    ( 0.150, 1.29, 0.42, 0.80, 0.70, 0.81, 0.68),   # screen
    (-0.150, 1.30, 0.44, 0.80, 0.70, 0.82, 0.68),   # canopy crown
    (-0.500, 1.27, 0.46, 0.81, 0.70, 0.83, 0.69),
    (-0.900, 1.14, 0.47, 0.85, 0.85, 0.85, 0.70),
    (-1.150, 1.03, 0.50, 0.84, 0.67, 0.69, 0.58),
    (-1.351, 1.01, 0.52, 0.86, 0.65, 0.66, 0.56),   # rear axle
    (-1.550, 0.96, 0.51, 0.88, 0.69, 0.69, 0.58),
    (-1.750, 0.87, 0.50, 0.81, 0.84, 0.81, 0.66),
    (-1.942, 0.80, 0.42, 0.60, 0.73, 0.50, 0.40),   # tail
]

# Heights scaled up by 1.241 above the floor line. Measured off the hero image:
# wheelbase divided by roof height is 2.07 there, against 2.57 as first built,
# which put the roof at 1051mm where the reference implies 1304mm. That single
# ratio is most of the difference in feel — the car was a flat wedge where the
# reference is tall and muscular. Both wheel centres and the roof are fully in
# frame so the ratio is trustworthy, unlike overall length: the image is
# cropped hard at the rear, so anything derived from car length is not.
#
# Heights of the lower rings. The flare rides just under the top surface but
# never above 0.72, so it stays put through the tall cabin instead of being
# dragged up with the canopy.
FLARE_Z_MAX, FLARE_GAP = 0.869, 0.075
WAIST_Z, ROCKER_Z, FLOOR_Z = 0.423, 0.187, 0.10

STATIONS = [{"x": x, "top_z": tz, "edge_w": ew, "flare_w": fw,
             "waist_w": ww, "rocker_w": rw, "floor_w": flw}
            for x, tz, ew, fw, ww, rw, flw in PROFILE]


def _axles(p):
    return p["wheelbase"] / 2, -p["wheelbase"] / 2


def sill_height(x, p):
    """Kept for the checks; the floor line is flat now that the wheel openings
    are apertures in the flare rather than a scallop lifted out of a sill."""
    return FLOOR_Z


def station_rings(row, p=None):
    """The (y, z) control points for one station, outboard side."""
    top_z = row["top_z"]
    flare_z = min(top_z - FLARE_GAP, FLARE_Z_MAX)
    full = {
        "top_centre": (0.0, top_z),
        "top_edge":   (-row["edge_w"],   top_z - FLARE_GAP * 0.5),
        "flare":      (-row["flare_w"],  flare_z),
        "waist":      (-row["waist_w"],  min(WAIST_Z, flare_z - 0.02)),
        "rocker":     (-row["rocker_w"], min(ROCKER_Z, WAIST_Z - 0.02)),
        "floor":      (-row["floor_w"],  FLOOR_Z),
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
