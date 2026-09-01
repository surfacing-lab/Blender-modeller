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

## models/car_blockout.py

Stage 1-2 of the build order: body side profile, then wheels as plain cylinders
for proportion. Front and rear are deliberately not modelled yet — they get
built to meet this side.

All dimensions live in `PROPORTIONS` (metres, real-world scale) so the form can
be pushed between iterations without editing construction code. The car faces
+X, up is +Z, and the side panel is mirrored across Y=0.

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
