"""Print edge crease and bevel-weight values. Run inside Blender.

Needed because a .blend written by a newer Blender than the one reading it
loses these values: the attribute survives, its data does not. Everything else
— topology, modifiers, proportions — reads fine.

Blender: Scripting tab, paste, Run. Then paste the output back.
"""

import bpy
from collections import Counter

for ob in [o for o in bpy.data.objects if o.type == 'MESH']:
    me = ob.data
    for attr in ("crease_edge", "bevel_weight_edge"):
        layer = me.attributes.get(attr)
        if not layer or not len(layer.data):
            continue
        nonzero = [d.value for d in layer.data if d.value > 1e-6]
        if not nonzero:
            continue
        tally = Counter(round(v, 2) for v in nonzero)
        print(f"{ob.name} / {attr}: {len(nonzero)}/{len(layer.data)} edges")
        for value, count in sorted(tally.items(), reverse=True):
            print(f"    {value:.2f} -> {count} edges")
