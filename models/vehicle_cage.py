"""Generic vehicle cage construction — the patch layout, reusable per vehicle.

A body side is described by a handful of named profile lines running the length
of the car: the centreline of the top surface, the top-surface edge, the
shoulder, the character line, the lower side, the sill, and the lip that turns
inboard into the wheel well. Each cross-section ("station") gives a (y, z) for
every line, and consecutive stations bridge into quads.

The part that matters is density. A uniform grid renders soft, because a hard
line carried by a single edge loop gets averaged away by Catmull-Clark. So
lines flagged hard get support loops generated either side of them, tight
against the line — the stacked parallel loops you see along a sill or around an
arch on a hand-built cage. Everywhere else the quads stay large.

Creases back the support loops up rather than replacing them. Support loops
alone soften under heavy subdivision; creases alone give an edge with no
shoulder to it. Real cages use both, which is why the crease values here are
moderate except on the open boundary.

Per-vehicle numbers live with the vehicle. Nothing here knows what car it is.
"""

import math
import bmesh

# Order matters: this is the run from the centreline of the top surface down
# the side to the wheel-well lip. `support` is the distance, in metres, at
# which to place a supporting loop either side of a hard line.
PROFILE_LINES = [
    {"name": "top_centre", "hard": False},
    {"name": "top_edge",   "hard": False},
    {"name": "shoulder",   "hard": True,  "support": 0.030, "crease": 0.35},
    {"name": "character",  "hard": True,  "support": 0.026, "crease": 0.30},
    {"name": "lower_side", "hard": False},
    {"name": "sill",       "hard": True,  "support": 0.022, "crease": 0.45},
    {"name": "lip_inner",  "hard": True,  "support": 0.018, "crease": 1.00},
]


def _offset(a, b, d):
    """Point at distance d from a, heading toward b."""
    vy, vz = b[0] - a[0], b[1] - a[1]
    length = math.hypot(vy, vz)
    if length < 1e-9:
        return a
    return (a[0] + vy / length * d, a[1] + vz / length * d)


def expand_rings(points, profile=None):
    """Insert support loops around the hard lines.

    Returns the expanded ring list and, for each hard line, the index its main
    loop ended up at — the creaser needs that after the list has grown.

    Support distance is clamped to a fraction of the gap to the neighbouring
    line. Unclamped, a support loop on a tightly compressed section (over an
    arch, where the whole side collapses into a few centimetres) overshoots its
    neighbour and the surface self-intersects.
    """
    profile = profile or PROFILE_LINES
    out, index_of = [], {}
    for i, pt in enumerate(points):
        spec = profile[i]
        support = spec.get("support", 0.0) if spec.get("hard") else 0.0

        if support and i > 0:
            gap = math.dist(pt, points[i - 1])
            out.append(_offset(pt, points[i - 1], min(support, gap * 0.45)))

        index_of[spec["name"]] = len(out)
        out.append(pt)

        if support and i < len(points) - 1:
            gap = math.dist(pt, points[i + 1])
            out.append(_offset(pt, points[i + 1], min(support, gap * 0.45)))

    return out, index_of


def check_folds(stations, rings_fn):
    """Rings must descend at every station. One that does not has folded back
    through itself — invisible in a render, fatal to the surface."""
    bad = []
    for row in stations:
        zs = [z for _, z in rings_fn(row)]
        if any(zs[i] < zs[i + 1] - 1e-9 for i in range(len(zs) - 1)):
            bad.append((row["x"], [round(z, 3) for z in zs]))
    return bad


def build_cage(stations, rings_fn, profile=None):
    """Loft the stations into an all-quad cage with support loops and creases."""
    profile = profile or PROFILE_LINES
    bm = bmesh.new()

    grid, index_of = [], None
    for row in stations:
        expanded, index_of = expand_rings(rings_fn(row), profile)
        grid.append([bm.verts.new((row["x"], y, z)) for y, z in expanded])

    for s in range(len(grid) - 1):
        for r in range(len(grid[0]) - 1):
            bm.faces.new((grid[s][r], grid[s][r + 1],
                          grid[s + 1][r + 1], grid[s + 1][r]))

    crease = bm.edges.layers.float.new("crease_edge")
    for spec in profile:
        value = spec.get("crease")
        if not value:
            continue
        ring = index_of[spec["name"]]
        for s in range(len(grid) - 1):
            edge = bm.edges.get((grid[s][ring], grid[s + 1][ring]))
            if edge is not None:
                edge[crease] = value

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm
