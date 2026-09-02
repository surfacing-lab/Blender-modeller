"""Generic vehicle cage construction — the patch layout, reusable per vehicle.

A body side is described by a handful of named profile lines running the length
of the car, from the centreline of the top surface down to the lip that turns
inboard into the wheel well. Each cross-section ("station") gives a (y, z) for
every line, and consecutive stations bridge into quads.

The governing rule is **as few edges as possible**. Definition comes from
creasing the outline — the arch lip, the sill, the design lines — and the
surface between those outlines is left smooth and empty. Extra loops are not
how a line is held sharp; a crease is. Loops added to firm up an edge cost
nothing visually that a crease would not give, and they make the cage far
harder to push around afterwards, which is the thing that actually matters
across the iterations a form goes through.

So: no support loops, no subdividing to add control. If a line needs to be
harder, raise its crease. If a form needs to change, move the few points there
are.

Per-vehicle numbers live with the vehicle. Nothing here knows what car it is.
"""

import bmesh


def check_folds(stations, rings_fn):
    """Rings must descend at every station. One that does not has folded back
    through itself — invisible in a render, fatal to the surface."""
    bad = []
    for row in stations:
        zs = [z for _, z in rings_fn(row)]
        if any(zs[i] < zs[i + 1] - 1e-9 for i in range(len(zs) - 1)):
            bad.append((row["x"], [round(z, 3) for z in zs]))
    return bad


def build_cage(stations, rings_fn, creases, cap_ends=False, skip=None):
    """Loft the stations into an all-quad cage and crease the named lines.

    `creases` maps ring index to crease value. The outline — the boundary loop
    and the sill — wants to be hard; interior design lines want less, since a
    fully creased character line reads as damage rather than as a design line.
    """
    bm = bmesh.new()
    grid = [[bm.verts.new((row["x"], y, z)) for y, z in rings_fn(row)]
            for row in stations]

    for s in range(len(grid) - 1):
        for r in range(len(grid[0]) - 1):
            # `skip` leaves a hole rather than a surface — the cockpit
            # aperture. The reference body is an open shell, not a closed
            # volume: its character comes from the openings, and no amount of
            # profile tuning makes a closed lozenge read the same way.
            if skip and skip(stations[s]["x"], stations[s + 1]["x"], r):
                continue
            bm.faces.new((grid[s][r], grid[s][r + 1],
                          grid[s + 1][r + 1], grid[s + 1][r]))

    if cap_ends:
        # Close the nose and tail with a single n-gon each. Their own body
        # carries a 9-gon and a few pentagons, so n-gons in a flat cap are
        # within house style — and a cap costs far less than the pole a
        # converging fan would leave at each end.
        bm.faces.new(grid[0])
        bm.faces.new(list(reversed(grid[-1])))

    crease_layer = bm.edges.layers.float.new("crease_edge")
    for ring, value in creases.items():
        for s in range(len(grid) - 1):
            edge = bm.edges.get((grid[s][ring], grid[s + 1][ring]))
            if edge is not None:
                edge[crease_layer] = value

    loose = [v for v in bm.verts if not v.link_faces]
    if loose:
        bmesh.ops.delete(bm, geom=loose, context='VERTS')

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm
