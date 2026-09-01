"""Headless preview rendering, so work can be inspected visually instead of asserted.

Cycles/CPU only in this container: EEVEE needs a GPU context (libEGL) that
isn't present, and it aborts the process rather than raising, so it must not
be selected at all.
"""

import math
import bpy
from mathutils import Vector

CLAY = (0.62, 0.62, 0.63, 1.0)
WIRE = (0.02, 0.02, 0.03, 1.0)


def _bounds(objects):
    """World-space bounding box centre and radius of the given mesh objects."""
    pts = [
        obj.matrix_world @ Vector(corner)
        for obj in objects
        for corner in obj.bound_box
    ]
    if not pts:
        return Vector((0, 0, 0)), 1.0
    lo = Vector((min(p[i] for p in pts) for i in range(3)))
    hi = Vector((max(p[i] for p in pts) for i in range(3)))
    centre = (lo + hi) / 2
    return centre, max((hi - lo).length / 2, 1e-4)


def _flat_material(name, colour, roughness=0.45):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = colour
        bsdf.inputs["Roughness"].default_value = roughness
    return mat


def _studio_light(centre, radius):
    """Three-point-ish setup scaled to the subject, so shading reads at any size."""
    specs = [
        ("Key", (1.4, -1.6, 1.5), 6.0),
        ("Fill", (-1.8, -1.0, 0.4), 1.6),
        ("Rim", (-0.6, 1.8, 1.2), 3.0),
    ]
    for name, direction, power in specs:
        data = bpy.data.lights.new(name, 'AREA')
        data.size = radius * 3
        # Inverse-square falloff means energy must scale with distance squared.
        data.energy = power * (radius ** 2) * 40
        light = bpy.data.objects.new(name, data)
        bpy.context.collection.objects.link(light)
        light.location = centre + Vector(direction) * radius * 3
        # Aim the light at the subject.
        light.rotation_euler = (centre - light.location).to_track_quat('-Z', 'Y').to_euler()


def render(
    filepath,
    angle="three_quarter",
    resolution=(720, 540),
    samples=32,
    clay=True,
    wireframe=False,
):
    """Render every mesh in the scene, auto-framed. Returns filepath.

    angle:     three_quarter | front | side | top, or an (azimuth, elevation)
               pair in degrees.
    clay:      override all materials with neutral grey, so form is judged by
               silhouette and shading rather than by texture.
    wireframe: overlay edges, for checking topology and edge flow.
    """
    scene = bpy.context.scene
    meshes = [o for o in scene.objects if o.type == 'MESH']
    centre, radius = _bounds(meshes)

    named = {
        "three_quarter": (45, 25),
        "front": (0, 0),
        "side": (90, 0),
        "top": (0, 89),
    }
    azimuth, elevation = named.get(angle, angle if angle in named.values() else named["three_quarter"]) \
        if isinstance(angle, str) else angle

    cam_data = bpy.data.cameras.new("__preview_cam")
    cam_data.lens = 85  # long-ish lens: less perspective distortion when judging proportion
    cam = bpy.data.objects.new("__preview_cam", cam_data)
    bpy.context.collection.objects.link(cam)

    # Distance so the subject's bounding sphere fits the *narrower* of the two
    # fields of view. Blender's sensor_width applies to the larger image
    # dimension, so the other axis is scaled by the aspect ratio.
    width, height = resolution
    fov_wide = 2 * math.atan(cam_data.sensor_width / (2 * cam_data.lens))
    fov_narrow = 2 * math.atan(math.tan(fov_wide / 2) * min(width, height) / max(width, height))
    distance = radius / math.sin(fov_narrow / 2) * 1.12  # 12% breathing room

    # Place the camera on a sphere around the subject.
    az, el = math.radians(azimuth), math.radians(elevation)
    offset = Vector((
        math.sin(az) * math.cos(el),
        -math.cos(az) * math.cos(el),
        math.sin(el),
    )) * distance
    cam.location = centre + offset
    cam.rotation_euler = (centre - cam.location).to_track_quat('-Z', 'Y').to_euler()
    scene.camera = cam

    _studio_light(centre, radius)

    if clay:
        mat = _flat_material("__clay", CLAY)
        for obj in meshes:
            obj.data.materials.clear()
            obj.data.materials.append(mat)

    if wireframe:
        # The wire needs its own dark slot, otherwise it renders in clay grey
        # against clay grey and the topology is invisible.
        wire_mat = _flat_material("__wire", WIRE, roughness=0.9)
        for obj in meshes:
            if len(obj.data.materials) == 0:
                obj.data.materials.append(_flat_material("__clay", CLAY))
            obj.data.materials.append(wire_mat)
            if "__wire" not in obj.modifiers:
                mod = obj.modifiers.new("__wire", 'WIREFRAME')
                mod.thickness = radius * 0.012
                mod.use_replace = False
                mod.material_offset = len(obj.data.materials) - 1

    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.05, 0.05, 0.06, 1)

    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.render.resolution_x, scene.render.resolution_y = resolution
    scene.render.filepath = filepath
    bpy.ops.render.render(write_still=True)
    return filepath


def contact_sheet(prefix, angles=("front", "side", "three_quarter"), **kwargs):
    """Render the same model from several angles. Proportion errors hide in a
    single view; they don't survive three."""
    return [render(f"{prefix}_{a}.png", angle=a, **kwargs) for a in angles]
