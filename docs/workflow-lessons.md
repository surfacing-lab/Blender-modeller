# Workflow lessons — mirrored from the blender-car-modeler skill

Live copy is in the skill inside the session container, which is reclaimed
when the session ends. This mirror is the durable one.

---

# This user's workflow, conventions, and lessons learned

This file is the memory of everything learned working with this specific user in Blender. It starts mostly empty — that's expected on day one. The point isn't to fill it out in one sitting; it's to add one line whenever a real correction or preference actually comes up, so the next session doesn't repeat the same mistake or ask the same question twice.

**How to add to this file:** when the user corrects an approach, states a convention, or flags something as a repeated mistake, add a short, concrete line to the right section below — their words or a close paraphrase, not a long writeup. If a section starts getting cluttered with near-duplicate entries, consolidate them into one clearer line instead of letting it sprawl.

## Modeling conventions

**Build order (stated 2026-09-01, their core method):**
1. Body side first — the side profile/panel is the starting surface, not the hood or arches.
2. Wheels in early as simple cylinders, purely to judge proportion and stance.
3. Front, then back — modelled to meet the already-established side.
4. Once the form is good: duplicate the body and shrinkwrap it to make the
   windscreen. This is deliberate — glass that derives from the body surface
   gives a correct reflection sweep and preserves the intended overall form,
   rather than a separately-modelled screen that fights the body line.
5. As the design matures, add wheel detail and lamp data.
6. Basic interior, blocked in early so it can be iterated on later.

Expect several iterations — the form is refined in loops, not in one pass.

**Fewest possible edges — stated as general for ALL basic vehicles
(2026-09-01).** Crease the OUTLINE — wheel-arch lip, sill, the design lines —
and leave the surface between those outlines smooth and empty. Definition comes
from creasing, never from adding loops. The reason is editability: the fewer
points there are, the easier the form is to push around, and a form goes
through many iterations.

Corrected in the same session after getting this backwards: the stacked
parallel loops visible along the sill of their cage were read as support loops,
and support loops were added throughout. Measured afterwards, they bought
nothing — arch crown 0.702 with them, 0.703 without, for 2.6x the faces. Do not
add a loop to firm up an edge. Raise its crease.

Also delete stations that do not change the form, but measure before removing:
three came out of the PIX3L side with length, height and arch clearance
identical to the millimetre, while one that looked equally redundant was
carrying the canopy crown and cost 38mm of height when dropped.

**Low poly + Subdivision Surface + Mirror is the default, always.** Build a
light all-quad control cage and let Subsurf do the smoothing — do not model
dense geometry directly. Mirror across the centreline rather than modelling
both sides. Modifier order is Mirror then Subsurf, and the mirror needs
clipping on so the centreline seam welds instead of splitting open under
subdivision.

**Measure the hero image, do not just look at it (2026-09-02).** With the
references packed into the .blend they can be extracted and measured from
pixels. The ratio that mattered: WHEELBASE DIVIDED BY ROOF HEIGHT is 2.07 in
the hero image against 2.57 as modelled, which put the roof at 1051mm where the
reference implies 1304mm. That one number was most of the difference in feel —
a flat wedge instead of a tall muscular form.

Pick ratios whose endpoints are fully in frame. Overall length was NOT usable:
the image is cropped hard at the rear, so an aspect ratio of 2.95 measured from
it is meaningless, and a tyre-diameter check failed too because the dark body
above the wheel merges with the tyre. Two of three measurements had to be
thrown away — check what is actually in frame before trusting any of them.

To extract packed images: img.filepath_raw = path; img.file_format='PNG';
img.save(). Pixels come out via img.pixels.foreach_get into a numpy array,
which arrives bottom-up so needs flipping.

**THE section architecture (2026-09-02) — the single biggest thing missed.**
The reference is a NARROW CENTRAL TUB with WIDE FENDER FLARES bursting out at
the top, and the wheel sits in the gap between them. Measured at the front
axle: tub 0.56 half-width through the lower two thirds, flare 0.88 above it.
Between the axles the body fills out to ~0.85 with the side tucked IN to a
waist at mid-height (0.70 against 0.82 at the rocker).

A cage built at one width for every height is a slab, and cutting holes in a
slab does not make it a car. Neither profile tuning nor crease tuning nor
station pruning touches this — all of that was polishing the wrong object for
days. A wheel arch is the GAP BETWEEN the flare and the tub, not a scallop
lifted out of a sill line.

Diagnose this by sampling half-width at FIXED HEIGHTS across stations, on both
models. A section that reads the same width at every height is the tell.

**Also worth saying plainly:** a grey clay blockout will never "look like" a
finished hero render. Glass, wheels, lamps, materials and lighting carry most
of a car's visual identity. Compare blockout to blockout, and say so rather
than chasing a resemblance the medium cannot deliver.

**Cutting the openings SHRINKS the cage (2026-09-02, their point).** Once the
glass aperture, grille and side intake are cut, rings and stations that existed
only to shape those regions stop earning their place. Prune after cutting, not
before: 87 faces / 108 verts went to 58 / 79 with the envelope unchanged.

Prune by measuring one removal at a time — but envelope numbers alone cannot
settle it, because they are blind to a design line vanishing. The "shoulder"
ring measured as costing 1mm of width; it was only dropped after rendering with
and without and confirming the surface read the same. It sat 1.5% inboard of
the character line and the two were fighting each other.

**Their `body` object is an OPEN hard-surface shell, not a closed volume
(2026-09-02).** Rendered on its own it has huge see-through wheel-arch cutouts,
a thin blade sill, no roof — the canopy is separate `Glass` and
`FR_WINDSCREEN` objects — and hard creased facets throughout. Building the body
as a closed smooth lozenge and expecting it to read like the reference is
hopeless: the character comes from the openings and the panel edges. Model the
body with the cockpit open and the arches cut large, then add glass separately.

**Their crease values, recovered from the raw .blend (2026-09-02):** 45% of
edges creased, median 0.99, and 67% of creased edges at 0.90 or above, with a
long soft tail from 0.09 to 0.6. They crease FAR harder than first assumed —
the outline and the character line are effectively hard at 0.99/1.0, and only
secondary lines get partial values. Earlier defaults of 0.85/0.55/0.50 were far
too soft.

Recovering them needed the raw file: their Blender is newer, so bpy loads the
mesh with the crease attribute present but holding zero values, and the mesh
will not even allocate a replacement layer. The route that worked was
decompressing the .blend (zstd, multi-frame — needs read_across_frames) and
reading the float array after the "crease_edge" string, verified by its length
matching the edge count exactly. Rebuilding the mesh with from_pydata and
mapping creases by vertex-pair sidesteps the unallocatable layer.

**Measured off Concept_Model_WIP4.blend (2026-09-01) — their actual practice:**
- Canopy crowns at the MIDDLE of the wheelbase, not forward of it. Do not
  assume cab-forward on a mid-engine silhouette.
- Body pinches in through the cabin and bulges at both arches (0.824 against
  0.90 half-width), rather than running near-constant width.
- Wheel outer face sits flush with the widest point of the body.
- Their cage is NOT strictly all-quads: 177 faces carrying 2 triangles, 3
  pentagons and one 9-gon. All-quad is a preference, not a rule to enforce.
- Mirror clipping is OFF, with merge threshold 0.01. Subsurf runs 5/5.
- Windscreen is a separate 18-face patch: Mirror, then Subsurf 5/5 with
  boundary smoothing ALL (not preserve-corners), then Shrinkwrap onto `body`
  using NEAREST_SURFACEPOINT / ON_SURFACE with a 1mm offset. This is the
  "copy the body and shrinkwrap" step they described on day one.
- Their working envelope is 4026mm long on a 2702mm wheelbase with 732/593
  overhangs and a 1072mm roof — NOT the 4519mm Porsche envelope named earlier.
  Ask which governs when the two conflict.

## Recurring mistakes to avoid

- Do not build body panels as triangulated n-gons or extruded flat profiles.
  Corrected 2026-09-01: the first blockout attempt filled a closed outline and
  triangulated it, which is unusable under Subsurf. Build a quad cage instead.
- **Never model without reference.** Corrected 2026-09-01, and this was the
  worst error of the session: three commits of confident geometry were built on
  invented proportions (2650mm wheelbase against a real 911's 2450mm). Stating
  "here are my assumed proportions" is NOT a substitute for reference. Ask for
  reference images, or pull real published dimensions, before the first vertex.
- Sample reference geometry in a WHEELBASE-CENTRED frame. Their file's origin
  is not at the wheelbase centre (axles at -1.471/+1.231, midpoint -0.120), so
  sampling against assumed axle positions shifted an entire profile 120mm along
  the car relative to its own wheels.
- Author ring heights as fractions of the span between the top surface and the
  sill, never as fixed absolute heights. Fixed heights fold the cage wherever
  the sill lifts into an arch — it happened twice, and both times check_folds
  caught what the render did not.
- Do not react to a render before checking the numbers. Twice on day one a
  render was misread as a geometry bug when the geometry measured correct
  (unlit cavities reading as holes, a cropped frame reading as a rotation).
  Measure, then judge.

## Preferences & workflow

- Works in iterative loops and expects refinement passes, not one-shot results.
- **Udin Optic is a generative design tool that ships as a Blender ADDON**,
  backed by a subscription (udinbv.com / optic.udinbv.com). It is not an API
  and never will be something Claude calls: it runs in a Blender GUI, on their
  machine, under their subscription, and their tenant
  (toyota-au.udinbv.com/optic/) sits behind Toyota SSO. The domain is also
  blocked by this environment's egress allowlist. Do not ask again how to
  "reach Udin" — the answer is that only they can run it.
  The working loop: Claude builds and renders the blockout, they run the render
  through Optic, they paste the generated design back into chat, Claude
  executes it as geometry. tools/preview.py already emits clay views suitable
  as Optic input.
- End goal is animation via Higgsfield, so models should be built ready to hand
  off for animation.
- Sends reference as images pasted into chat — this works well and is the main
  reference channel. Claude cannot fetch images from the web (egress blocked,
  WebFetch is text-only), but CAN look up published dimensions via search.
- Their Blender is NEWER than the bpy in this container (502.44 vs 5.0.1), so
  their files open with "expect loss of data" and edge crease values arrive
  empty — the attribute exists but holds 0 values against 412 edges. Topology,
  proportions, modifiers and shrinkwrap settings all read fine. Ask them to run
  tools/dump_creases.py and paste the output when crease values matter.
- Anchors original designs to a real car's dimensions ("make this with roughly
  the Porsche dimensions") — take the envelope from the real car, the styling
  from the reference.

## Concept-mode notes

*(Specific psychedelic/sci-fi/sacred-geometry choices this user tends to favor once they're established — particular color combinations, motifs they gravitate to or avoid, past concept pieces worth remembering the direction of.)*
