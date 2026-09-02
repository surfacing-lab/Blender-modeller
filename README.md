# Blender-modeller

Learning and recording a specific way of modelling in Blender, and building
reusable tooling around it.

## Environment (verified, not assumed)

This runs **headless Blender via the `bpy` PyPI module** — no GUI, no viewport.

| | |
|---|---|
| Blender | 5.0.1 (`pip install bpy`) |
| Python | 3.11 |
| Cores | 4 |

Verified working: mesh creation, `bmesh` topology operations, modifiers,
evaluated (post-modifier) geometry, `.blend` save/load, and Cycles rendering.

### Two constraints worth knowing before you write code here

**EEVEE is unavailable.** It needs a GPU context (`libEGL.so.1`) that this
container doesn't have. It does not raise a catchable exception — it aborts
the process — so a `try/except` around it will not save you. Use `CYCLES`
with `device = 'CPU'`.

**Engine identifiers changed in 5.0.** `BLENDER_EEVEE_NEXT` no longer exists;
the valid set is `BLENDER_EEVEE`, `BLENDER_WORKBENCH`, `CYCLES`.

Render cost at 720x540 / 32 samples on 4 CPU cores is roughly 3-7s per frame,
so iterating visually is cheap.

## tools/preview.py

Renders the scene so work can be *looked at* rather than asserted correct.

```python
from tools import preview

preview.render("out.png", angle="three_quarter")        # single view
preview.render("topo.png", wireframe=True)              # edge flow
preview.contact_sheet("model")                          # front + side + 3/4
```

- Auto-frames the subject from its bounding sphere using the real camera FOV,
  fitting the narrower image axis.
- 85mm lens by default — long enough that perspective distortion doesn't lie
  about proportion.
- Clay override by default: form gets judged on silhouette and shading, not
  on material.
- `wireframe=True` adds a dark wire in its own material slot. It needs the
  separate slot; a wire in clay grey against clay grey is invisible.

`angle` accepts `front`, `side`, `top`, `three_quarter`, or an
`(azimuth, elevation)` pair in degrees.

## The design loop

Udin Optic is the design director. It is a Blender addon on a subscription, so
it runs on their machine, not here — and its Toyota tenant is behind SSO and
this environment's egress allowlist besides. The loop is therefore:

1. Build and render the blockout here; `tools/preview.py` emits the clay views
   Optic takes as input.
2. They run it through Optic in their Blender.
3. They paste the generated design back into chat.
4. Execute it as geometry.

## tools/inspect_blend.py

Reads a .blend and reports what its meshes are actually made of — face counts
and whether they are all quads, the modifier stack with its settings in order,
every crease value present and how many edges carry it, vertex valence, and
overall dimensions.

```bash
python3 tools/inspect_blend.py path/to/file.blend --poles
```

Use it to learn from someone else's file precisely rather than by eye: run it
on theirs and on ours, and the differences are the lesson. Note that
`dimensions_mm` is the bounding-box extent, not height above ground, and that
it reads the base mesh — not the subdivided result.

## models/vehicle_cage.py — the cage layout

Generic, per the note that this structure suits all basic vehicles. Nothing in
it knows what car it is.

A body side is a set of named profile lines running the length of the car —
top centre, top edge, shoulder, character, sill, and the lip that turns inboard
into the wheel well. Each station gives a (y, z) per line and consecutive
stations bridge into quads.

The governing rule is **as few edges as possible**. Definition comes from
creasing the outline; the surface between outlines is left smooth and empty.
Loops are not how an edge is held sharp — a crease is. Extra loops buy nothing
a crease does not already give, and they make the cage much harder to push
around later, which is what actually matters across the iterations a form goes
through.

Measured on this body: the wheel arch crowned at 0.702 with support loops
either side of every hard line, and 0.703 without them — for 2.6x the face
count. Stations get the same treatment: keep only the ones that change the
form, and check by measuring rather than by eye.

## models/car_blockout.py — PIX3L concept

Mid-engine supercar, body side blocked out. Styling from the supplied
reference: cab-forward canopy, long rear deck over the engine, high haunches,
intake scoop ahead of the rear arch, squared arches under a hard shoulder.

Dimensions are anchored to a Porsche 911 (992), not invented:

| | Target | Built |
|---|---|---|
| Length | 4519 mm | 4519 mm |
| Width | 1852 mm | 1848 mm |
| Wheelbase | 2450 mm | 2450 mm |
| Height | — | 1233 mm |

Overhangs are split mid-engine (880 front / 1189 rear) rather than the 911's.
Wheels are staggered front to rear. Front and rear bodywork are not modelled
yet — they get built to meet this side.

`blend/pix3l_blockout.blend` is the saved working file; `renders/` holds the
current views.

```python
from models import car_blockout
body = car_blockout.build()
car_blockout.check_folds()          # must be empty
car_blockout.poly_report(body)      # cage faces, all-quad check, subdivided total
car_blockout.arch_clearance(body)   # does the wheel actually fit its opening
```

Low poly cage + Mirror + Subsurf. 80 quads in the cage, all quads. Modifier
order is Mirror then Subsurf, mirror clipping on.

Detail lines are creases, not extra loops — see `CREASE_LINES`. The sill and
arch lip are hard, the character line and beltline partial.

**`check_folds()` earns its place.** The lower rings must descend past the arch
lip; author them ignoring the arch and the surface folds back through itself.
It renders as a plausible car and measures 175mm of arch crown missing, which
sends you hunting for a subdivision problem that isn't there.
