# procedural_lab_consolidated_with_door_with_action_and_lod.py
# Blender 5.0.1-friendly bpy script
# 一鍵生成封閉式科技館骨架（滑動門動畫、密林、黑色轉場）並匯出 GLB

import bpy
import math
import os
import random
import tempfile
from mathutils import Vector, Euler

# ---------------------------
# Configuration
# ---------------------------
EXPORT_NAME = "procedural_lab_with_door.glb"
blend_dir = bpy.path.abspath("//")
if blend_dir and os.path.isdir(blend_dir):
    EXPORT_PATH = os.path.join(blend_dir, EXPORT_NAME)
else:
    EXPORT_PATH = os.path.join(tempfile.gettempdir(), EXPORT_NAME)

DOOR_WIDTH = 6.0
DOOR_HEIGHT = 4.0
WALL_THICKNESS = 0.25

WORLD_LAYOUT = {
    "outdoor": (0, 0, 0),
    "auto_door": (0, -40, 0),
    "entrance_hall": (0, -80, 0),
    "motivation_room": (0, -160, 0),
    "theory_room": (100, -160, 0),
    "programming_room": (200, -160, 0),
    "formula_room": (200, -260, 0),
    "simulation_center": (200, -400, 0),
    "conclusion_room": (200, -520, 0),
    "future_room": (200, -640, 0),
}

# ---------------------------
# Helpers: clear / materials
# ---------------------------
def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False, confirm=False)
    for mesh in list(bpy.data.meshes):
        if mesh.users == 0:
            try:
                bpy.data.meshes.remove(mesh)
            except Exception:
                pass

_material_cache = {}

def get_white_material(name="Mat_White", rough=0.3, metallic=0.0):
    key = (name, rough, metallic)
    if key in _material_cache:
        return _material_cache[key]

    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    out = nodes.get("Material Output")
    principled = nodes.get("Principled BSDF")
    if not principled:
        principled = nodes.new(type="ShaderNodeBsdfPrincipled")
        if out:
            mat.node_tree.links.new(principled.outputs['BSDF'], out.inputs['Surface'])

    principled.inputs["Base Color"].default_value = (0.96, 0.96, 0.98, 1.0)
    principled.inputs["Roughness"].default_value = rough
    principled.inputs["Metallic"].default_value = metallic
    _material_cache[key] = mat
    return mat

def get_emissive_material(name="Mat_Emit", color=(0.5, 0.8, 1.0, 1.0), strength=6.0):
    key = (name, color, strength)
    if key in _material_cache:
        return _material_cache[key]

    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    out = nodes.new(type="ShaderNodeOutputMaterial")
    emit = nodes.new(type="ShaderNodeEmission")
    emit.inputs['Color'].default_value = color
    emit.inputs['Strength'].default_value = strength
    links.new(emit.outputs['Emission'], out.inputs['Surface'])
    _material_cache[key] = mat
    return mat

# ---------------------------
# Primitive creators
# ---------------------------
def create_box(name, size, location=(0, 0, 0), rotation=(0, 0, 0), material=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.scale = (size[0] / 2.0, size[1] / 2.0, size[2] / 2.0)
    bpy.context.view_layer.update()
    if material:
        if obj.data.materials:
            obj.data.materials[0] = material
        else:
            obj.data.materials.append(material)
    return obj

def create_plane(name, size_x, size_y, location=(0, 0, 0), rotation=(0, 0, 0), material=None):
    bpy.ops.mesh.primitive_plane_add(size=1, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.scale = (size_x / 2.0, size_y / 2.0, 1)
    bpy.context.view_layer.update()
    if material:
        if obj.data.materials:
            obj.data.materials[0] = material
        else:
            obj.data.materials.append(material)
    return obj

def create_cylinder(name, radius, depth, location=(0, 0, 0), material=None, verts=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    if material:
        if obj.data.materials:
            obj.data.materials[0] = material
        else:
            obj.data.materials.append(material)
    return obj

# ---------------------------
# Composite pieces
# ---------------------------
def create_ground():
    mat = get_white_material("GroundMat", rough=0.95)
    g = create_plane("Ground", 300, 300, location=(0, 0, 0), material=mat)
    g.location.z = -0.01
    return g

def create_sky_dome(radius=180):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=(0, 0, 0))
    dome = bpy.context.object
    dome.name = "SkyDome"
    dome.scale.x = -1
    dome.data.materials.append(get_emissive_material("SkyMat", color=(0.02, 0.03, 0.08, 1.0), strength=0.06))
    return dome

def create_dense_forest(rows=7, cols=7, spacing=16, base_y=-140):
    trunk_mat = get_white_material("Trunk", rough=0.9)
    leaf_mat = get_emissive_material("Leaf", color=(0.02, 0.18, 0.05, 1.0), strength=0.6)
    for i in range(rows):
        for j in range(cols):
            x = (i - rows / 2) * spacing + random.uniform(-3.0, 3.0)
            y = base_y + (j - cols / 2) * spacing + random.uniform(-3.0, 3.0)
            h = random.uniform(5.0, 8.0)
            r = random.uniform(0.25, 0.6)
            create_cylinder(f"Trunk_{i}_{j}", r, h, location=(x, y, h / 2), material=trunk_mat)
            bpy.ops.mesh.primitive_uv_sphere_add(radius=random.uniform(1.6, 2.8), location=(x, y, h + 1.2))
            canopy = bpy.context.object
            canopy.name = f"Canopy_{i}_{j}"
            canopy.data.materials.append(leaf_mat)

def create_circular_hall(radius=8.5, height=14.0, position=(0, -80, 0)):
    verts = 64
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius + WALL_THICKNESS, depth=height, location=(position[0], position[1], position[2] + height / 2))
    outer = bpy.context.object
    outer.name = "Entrance_Outer"

    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius - 0.5, depth=height + 0.02, location=(position[0], position[1], position[2] + height / 2))
    inner = bpy.context.object
    inner.name = "Entrance_Inner"

    mod = outer.modifiers.new("bool_diff", "BOOLEAN")
    mod.object = inner
    mod.operation = 'DIFFERENCE'
    bpy.context.view_layer.objects.active = outer
    bpy.ops.object.modifier_apply(modifier=mod.name)
    try:
        bpy.data.objects.remove(inner, do_unlink=True)
    except Exception:
        pass

    create_box("Entrance_Floor", (radius * 2 + 2, radius * 2 + 2, 0.25), location=(position[0], position[1], position[2] - 0.125), material=get_white_material("FloorMat", rough=0.12))
    create_box("Entrance_Ceiling", (radius * 2 + 2, radius * 2 + 2, 0.25), location=(position[0], position[1], position[2] + height + 0.125), material=get_white_material("CeilMat", rough=0.3))
    outer.data.materials.append(get_white_material("HallWall", rough=0.25))
    return outer

def create_rect_room_closed(name, width, depth, height, position=(0, 0, 0)):
    """Closed room: no wall gaps."""
    wt = WALL_THICKNESS
    half_w = width / 2.0
    half_d = depth / 2.0

    floor = create_box(f"{name}_Floor", (width, depth, 0.2), location=(position[0], position[1], position[2] - 0.1), material=get_white_material("RoomFloor", rough=0.12))
    ceiling = create_box(f"{name}_Ceiling", (width, depth, 0.2), location=(position[0], position[1], position[2] + height + 0.1), material=get_white_material("RoomCeil", rough=0.3))

    front = create_box(f"{name}_Wall_Front", (width, wt, height), location=(position[0], position[1] - half_d + wt / 2, position[2] + height / 2), material=get_white_material("RoomWall", rough=0.28))
    back = create_box(f"{name}_Wall_Back", (width, wt, height), location=(position[0], position[1] + half_d - wt / 2, position[2] + height / 2), material=get_white_material("RoomWall", rough=0.28))

    left = create_box(f"{name}_Wall_Left", (depth, wt, height), location=(position[0] - half_w + wt / 2, position[1], position[2] + height / 2), material=get_white_material("RoomWall", rough=0.28))
    right = create_box(f"{name}_Wall_Right", (depth, wt, height), location=(position[0] + half_w - wt / 2, position[1], position[2] + height / 2), material=get_white_material("RoomWall", rough=0.28))
    left.rotation_euler = Euler((0, 0, math.radians(90)), 'XYZ')
    right.rotation_euler = Euler((0, 0, math.radians(90)), 'XYZ')

    return {"parts": [floor, ceiling, front, back, left, right]}

def create_sliding_door_group(position=(0, -40, 0), width=DOOR_WIDTH, height=DOOR_HEIGHT, thickness=0.12):
    door_empty = bpy.data.objects.new("door_group", None)
    bpy.context.scene.collection.objects.link(door_empty)
    door_empty.location = position

    left = create_box("door_L", (width / 2.0 - 0.02, thickness, height), location=(position[0] - width / 4.0, position[1], position[2] + height / 2.0), material=get_white_material("DoorMat", rough=0.18))
    right = create_box("door_R", (width / 2.0 - 0.02, thickness, height), location=(position[0] + width / 4.0, position[1], position[2] + height / 2.0), material=get_white_material("DoorMat", rough=0.18))
    left.parent = door_empty
    right.parent = door_empty

    left["closed_pos"] = tuple(left.location)
    right["closed_pos"] = tuple(right.location)

    open_offset = width * 0.5 + 0.05
    left["open_pos"] = tuple(Vector(left.location) + Vector((-open_offset, 0.0, 0.0)))
    right["open_pos"] = tuple(Vector(right.location) + Vector((open_offset, 0.0, 0.0)))
    door_empty["panels"] = [left.name, right.name]
    return door_empty

def animate_sliding_door(door_empty, frame_start=1, frame_open=36, frame_close=120):
    for name in door_empty.get("panels", []):
        panel = bpy.data.objects.get(name)
        if not panel:
            continue
        closed = Vector(panel["closed_pos"])
        openp = Vector(panel["open_pos"])
        panel.location = closed
        panel.keyframe_insert(data_path="location", frame=frame_start)
        panel.location = openp
        panel.keyframe_insert(data_path="location", frame=frame_open)
        panel.location = closed
        panel.keyframe_insert(data_path="location", frame=frame_close)

def create_portal_frame(position=(0, -120, 0), width=4.5, height=5.0):
    create_box("Portal_Frame", (width + 0.4, 0.4, height + 0.4), location=(position[0], position[1], position[2] + height / 2), material=get_white_material("PortalFrame", rough=0.15))
    create_plane("Portal_Surface", width - 0.1, height - 0.1, location=(position[0], position[1] + 0.01, position[2] + height / 2), material=get_emissive_material("PortalEmit", color=(0.6, 0.85, 1.0, 1.0), strength=8.0))

def create_bridge(position=(50, -160, 0), length=20, width=3.0):
    create_box("Bridge", (length, width, 0.15), location=(position[0], position[1], position[2] + 0.08), material=get_white_material("BridgeFloor", rough=0.18))
    create_box("Bridge_Edge_L", (length, 0.06, 0.05), location=(position[0], position[1] - width / 2 - 0.03, position[2] + 0.09), material=get_emissive_material("BridgeEdgeMat", color=(0.5, 0.85, 1.0, 1.0), strength=6.0))
    create_box("Bridge_Edge_R", (length, 0.06, 0.05), location=(position[0], position[1] + width / 2 + 0.03, position[2] + 0.09), material=get_emissive_material("BridgeEdgeMat", color=(0.5, 0.85, 1.0, 1.0), strength=6.0))

def create_spiral_staircase(center=(0, -80, 0), steps=20, radius=3.0, step_height=0.28, step_depth=0.8):
    for i in range(steps):
        angle = i * (2 * math.pi / steps)
        x = center[0] + math.cos(angle) * radius
        y = center[1] + math.sin(angle) * radius
        z = center[2] + i * step_height
        step = create_box(f"Stair_{i}", (radius * 0.5, step_depth, 0.15), location=(x, y, z + 0.075), material=get_white_material("StairMat", rough=0.25))
        step.rotation_euler = Euler((0, 0, -angle), 'XYZ')

def create_projection_plane(position=(0, -78, 4), w=6, h=3):
    create_plane("ProjectionPlane", w, h, location=(position[0], position[1], position[2]), material=get_emissive_material("ProjectionMat", color=(0.9, 0.95, 1.0, 1.0), strength=4.0))

def create_player_placeholder(position=(0, -78, 1.0)):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.35, location=(position[0], position[1], position[2] + 0.9))
    head = bpy.context.object
    head.name = "PlayerHead"
    create_cylinder("PlayerBody", radius=0.4, depth=1.4, location=(position[0], position[1], position[2] + 0.7), material=get_white_material("PlayerMat", rough=0.9))

# ---------------------------
# Camera fade panel
# ---------------------------
def create_fade_panel(parent_camera, size=8.0):
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, 0))
    panel = bpy.context.object
    panel.name = "FadePanel"
    panel.parent = parent_camera
    panel.location = Vector((0.0, 0.0, -1.0))

    mat = bpy.data.materials.new("FadeMat")
    mat.use_nodes = True
    mat.blend_method = 'BLEND'
    mat.shadow_method = 'NONE'

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out = nodes.new(type="ShaderNodeOutputMaterial")
    transp = nodes.new(type="ShaderNodeBsdfTransparent")
    emit = nodes.new(type="ShaderNodeEmission")
    emit.inputs['Color'].default_value = (0, 0, 0, 1)
    emit.inputs['Strength'].default_value = 1.0
    mix = nodes.new(type="ShaderNodeMixShader")

    links.new(transp.outputs['BSDF'], mix.inputs[1])
    links.new(emit.outputs['Emission'], mix.inputs[2])
    links.new(mix.outputs['Shader'], out.inputs['Surface'])
    panel.data.materials.append(mat)
    return mix

def animate_fade_panel(mix_node, frame_fade_in_start, frame_fade_in_end, frame_hold_end, frame_fade_out_end):
    mix_node.inputs[0].default_value = 0.0
    mix_node.inputs[0].keyframe_insert('default_value', frame=frame_fade_in_start)
    mix_node.inputs[0].default_value = 1.0
    mix_node.inputs[0].keyframe_insert('default_value', frame=frame_fade_in_end)
    mix_node.inputs[0].default_value = 1.0
    mix_node.inputs[0].keyframe_insert('default_value', frame=frame_hold_end)
    mix_node.inputs[0].default_value = 0.0
    mix_node.inputs[0].keyframe_insert('default_value', frame=frame_fade_out_end)

# ---------------------------
# Build world
# ---------------------------
def build_world_and_prepare():
    clear_scene()

    bpy.ops.object.light_add(type='SUN', location=(80, -80, 120))
    sun = bpy.context.object
    sun.data.energy = 3.0

    bpy.ops.object.light_add(type='AREA', location=(0, -80, 40))
    area = bpy.context.object
    area.data.energy = 400.0
    area.data.size = 20.0

    bpy.ops.object.camera_add(location=(0, -20, 8), rotation=(math.radians(75), 0, 0))
    cam = bpy.context.object
    cam.name = "PreviewCamera"
    bpy.context.scene.camera = cam

    create_ground()
    create_sky_dome(radius=180)
    create_dense_forest(rows=7, cols=7, spacing=16, base_y=-140)

    create_circular_hall(radius=8.5, height=14.0, position=WORLD_LAYOUT["entrance_hall"])
    create_rect_room_closed("EntranceRoomShell", 18, 18, 14, position=WORLD_LAYOUT["entrance_hall"])

    door = create_sliding_door_group(position=WORLD_LAYOUT["auto_door"], width=DOOR_WIDTH, height=DOOR_HEIGHT, thickness=0.12)
    return {"camera": cam, "door": door}

def finalize_and_export(prep, frame_start=1, frame_open=36, frame_close=120):
    cam = prep.get("camera")
    door = prep.get("door")

    create_projection_plane(position=(WORLD_LAYOUT["entrance_hall"][0], WORLD_LAYOUT["entrance_hall"][1] + 2, 4), w=6, h=3)

    create_rect_room_closed("MotivationRoom", 16, 12, 6, position=WORLD_LAYOUT["motivation_room"])
    create_rect_room_closed("TheoryRoom", 18, 14, 6, position=WORLD_LAYOUT["theory_room"])
    create_rect_room_closed("ProgrammingRoom", 18, 14, 6, position=WORLD_LAYOUT["programming_room"])
    create_rect_room_closed("FormulaRoom", 14, 12, 6, position=WORLD_LAYOUT["formula_room"])
    create_rect_room_closed("SimulationCenter", 28, 20, 8, position=WORLD_LAYOUT["simulation_center"])
    create_rect_room_closed("ConclusionRoom", 14, 12, 6, position=WORLD_LAYOUT["conclusion_room"])
    create_rect_room_closed("FutureRoom", 14, 12, 6, position=WORLD_LAYOUT["future_room"])

    create_bridge(position=(50, -160, 0), length=20, width=3)
    create_portal_frame(position=(0, -120, 0))
    create_spiral_staircase(center=(0, WORLD_LAYOUT["entrance_hall"][1] + 3, 0), steps=20, radius=3.5)
    create_player_placeholder(position=(0, WORLD_LAYOUT["entrance_hall"][1] + 2, 0.5))

    if door:
        animate_sliding_door(door, frame_start=frame_start, frame_open=frame_open, frame_close=frame_close)

    if cam:
        mix_node = create_fade_panel(cam, size=8.0)
        animate_fade_panel(mix_node, frame_open - 6, frame_open + 6, frame_open + 20, frame_open + 28)

    # Export with Blender-5 compatible options only
    bpy.ops.export_scene.gltf(
        filepath=EXPORT_PATH,
        export_format='GLB',
        export_apply=True,
        export_yup=True,
        export_animations=True,
    )
    print("Exported GLB to:", EXPORT_PATH)
    return EXPORT_PATH

# ---------------------------
# Run
# ---------------------------
if __name__ == "__main__":
    prep = build_world_and_prepare()
    out = finalize_and_export(prep, frame_start=1, frame_open=36, frame_close=120)
    print("Done. GLB:", out)
