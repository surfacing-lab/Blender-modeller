"""Background reference images, aligned to the model.

Image empties are viewport-only — they never appear in a render — which is what
makes them right for modelling reference and also means alignment cannot be
checked by rendering one. `report` prints where each image's edges land in
world space instead, so the fit can be verified as numbers.

Alignment needs two facts about each photograph that cannot be derived from the
model: how much of the frame the car fills, and where its centre sits. Those
are `span` and `centre`. Everything else follows from the car's own length.

Paths are stored relative to the .blend (Blender's `//` prefix), so dropping
the images into a `refs/` folder beside the file is all that is needed. An
image that is not there yet still gets its empty and its path, and resolves
as soon as the file appears.
"""

import math
import bpy

# local X -> world, local Y -> world, and the axis the image faces.
VIEWS = {
    # Seen from -Y. Car length runs along world X, height along world Z.
    "side":  {"euler": (math.pi / 2, 0.0, 0.0),            "along": "x"},
    # Seen from +X, looking back down the car. Width runs along world Y.
    "front": {"euler": (math.pi / 2, 0.0, math.pi / 2),    "along": "y"},
    # Seen from -X.
    "rear":  {"euler": (math.pi / 2, 0.0, -math.pi / 2),   "along": "y"},
    # Seen from above.
    "top":   {"euler": (0.0, 0.0, 0.0),                    "along": "x"},
}


def _image(name, filepath):
    """An image datablock pointing at filepath, whether or not it exists yet."""
    img = bpy.data.images.get(name)
    if img is None:
        img = bpy.data.images.new(name, 1, 1)
    img.source = 'FILE'
    img.filepath = filepath
    return img


def add_reference(view, filepath, extent, span=0.92, centre=(0.5, 0.5),
                  depth=0.0, opacity=0.35, name=None):
    """Place one reference image.

    view      side | front | rear | top
    filepath  where the image will live, e.g. "//refs/side.png"
    extent    the real-world size, in metres, that the car occupies in this
              view — its length for side and top, its width for front and rear
    span      fraction of the image's width the car fills
    centre    where the car's centre sits in the image, as (x, y) fractions
              measured from the bottom-left
    depth     how far to push the plane away along the viewing axis, so it sits
              behind the model rather than through it
    """
    spec = VIEWS[view]
    name = name or f"ref_{view}"

    bpy.ops.object.empty_add(type='IMAGE', location=(0, 0, 0))
    ob = bpy.context.active_object
    ob.name = name
    ob.data = _image(name, filepath)
    ob.rotation_euler = spec["euler"]

    # The empty spans `empty_display_size` across the image's width, so sizing
    # it by the fraction the car fills makes the car itself land at `extent`.
    ob.empty_display_size = extent / span
    # Offset is in image widths, and puts image point `centre` on the origin.
    ob.empty_image_offset = (-centre[0], -centre[1])

    ob.empty_image_depth = 'BACK'
    ob.use_empty_image_alpha = True
    ob.color[3] = opacity
    ob.show_empty_image_perspective = True
    ob.show_empty_image_orthographic = True
    # Only show each reference from the direction it was shot, so the side
    # image does not clutter the front view.
    ob.show_empty_image_only_axis_aligned = True

    if depth:
        axis = {"side": 1, "front": 0, "rear": 0, "top": 2}[view]
        sign = {"side": 1, "front": -1, "rear": 1, "top": -1}[view]
        ob.location[axis] = sign * depth

    ob.hide_select = True     # reference, not something to grab by accident
    return ob


def report(ob, view):
    """Where this image's edges land in world space, for checking the fit."""
    size = ob.empty_display_size
    ox, oy = ob.empty_image_offset
    lo, hi = size * ox, size * (ox + 1.0)
    axis = "X" if VIEWS[view]["along"] == "x" else "Y"
    return (f"{ob.name:10} spans {axis} {lo:+.3f} .. {hi:+.3f} m "
            f"(image width {size:.3f} m)")
