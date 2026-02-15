# Blender bpy script - 程式生成 AAA 科技館骨架（含 sliding door action、樹 LOD、黑色 overlay png）並匯出 glb
# Paste into Blender Text Editor and Run. (Blender 3.x / 4.x)
import bpy, math, os, tempfile, random
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

# also prepare path for overlay png
EXPORT_DIR = os.path.dirname(EXPORT_PATH) or tempfile.gettempdir()
OVERLAY_PNG = os.path.join(EXPORT_DIR, "overlay_black.png")

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
    "future_room": (200, -640, 0)
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
            except:
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
# Primitives
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


def create_cylinder(name, radius, depth, location=(0, 0, 0), material=None, verts=24):
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
# Composite pieces + LOD trees
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


def create_dense_forest_lod(rows=6, cols=6, spacing=18, base_y=-160):
    trunk_mat = get_white_material("Trunk", rough=0.9)
    leaf_mat = get_emissive_material("Leaf", color=(0.02, 0.18, 0.05, 1.0), strength=0.6)
    low_mat = get_white_material("LeafLow", rough=1.0)
    for i in range(rows):
        for j in range(cols):
            x = (i - rows / 2) * spacing + random.uniform(-3.0, 3.0)
            y = base_y + (j - cols / 2) * spacing + random.uniform(-3.0, 3.0)
            h = random.uniform(5.0, 8.0)
            r = random.uniform(0.25, 0.6)
            trunk = create_cylinder(f"Trunk_{i}_{j}", r, h, location=(x, y, h / 2), material=trunk_mat)
            # create parent empty
            parent = bpy.data.objects.new(f"Tree_{i}_{j}_parent", None)
            bpy.context.scene.collection.objects.link(parent)
            parent.location = (x, y, 0)
            # high canopy (sphere)
            bpy.ops.mesh.primitive_uv_sphere_add(radius=random.uniform(1.6, 2.6), location=(x, y, h + 1.0))
            high = bpy.context.object
            high.name = f"CanopyHigh_{i}_{j}"
            high.data.materials.append(leaf_mat)
            high.parent = parent
            high.location = (0, 0, h + 1.0)
            # low canopy (simple plane billboard)
            bpy.ops.mesh.primitive_plane_add(size=2.0, location=(x, y, h + 0.6))
            low = bpy.context.object
            low.name = f"CanopyLow_{i}_{j}"
            low.data.materials.append(low_mat)
            low.parent = parent
            low.location = (0, 0, h + 0.6)
            # trunk parented
            trunk.parent = parent
            trunk.location = (0, 0, h / 2)
            # custom property to describe LOD children & distances (string for GLTF-friendly)
            parent["lod_info"] = f"levels=2;high={high.name};low={low.name};distances=8,28"
    return True


def create_circular_hall(radius=8.5, height=14.0, position=(0, -80, 0)):
    verts = 64
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=verts,
        radius=radius + WALL_THICKNESS,
        depth=height,
        location=(position[0], position[1], position[2] + height / 2),
    )
    outer = bpy.context.object
    outer.name = "Entrance_Outer"
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=verts,
        radius=radius - 0.5,
        depth=height + 0.02,
        location=(position[0], position[1], position[2] + height / 2),
    )
    inner = bpy.context.object
    inner.name = "Entrance_Inner"
    mod = outer.modifiers.new("bool_diff", "BOOLEAN")
    mod.object = inner
    mod.operation = 'DIFFERENCE'
    bpy.context.view_layer.objects.active = outer
    bpy.ops.object.modifier_apply(modifier=mod.name)
    try:
        bpy.data.objects.remove(inner, do_unlink=True)
    except:
        pass
    create_box(
        "Entrance_Floor",
        (radius * 2 + 2, radius * 2 + 2, 0.25),
        location=(position[0], position[1], position[2] - 0.125),
        material=get_white_material("FloorMat", rough=0.12),
    )
    create_box(
        "Entrance_Ceiling",
        (radius * 2 + 2, radius * 2 + 2, 0.25),
        location=(position[0], position[1], position[2] + height + 0.125),
        material=get_white_material("CeilMat", rough=0.3),
    )
    outer.data.materials.append(get_white_material("HallWall", rough=0.25))
    return outer


def create_rect_room_with_doorgap(name, width, depth, height, position=(0, 0, 0), door_center_offset=(0, -0.5, 0)):
    floor = create_box(
        f"{name}_Floor",
        (width, depth, 0.2),
        location=(position[0], position[1], position[2] - 0.1),
        material=get_white_material("RoomFloor", rough=0.12),
    )
    ceiling = create_box(
        f"{name}_Ceiling",
        (width, depth, 0.2),
        location=(position[0], position[1], position[2] + height + 0.1),
        material=get_white_material("RoomCeil", rough=0.3),
    )
    half_w = width / 2.0
    half_d = depth / 2.0
    wt = WALL_THICKNESS
    door_w = DOOR_WIDTH
    door_center_x = position[0] + door_center_offset[0]
    left_seg_width = max(0.5, (width / 2.0) - (door_w / 2.0))
    right_seg_width = left_seg_width
    front_left = create_box(
        f"{name}_Wall_Front_L",
        (left_seg_width, wt, height),
        location=(position[0] - (width / 2.0 - left_seg_width / 2.0), position[1] - half_d + wt / 2, position[2] + height / 2),
        material=get_white_material("RoomWall", rough=0.28),
    )
    front_right = create_box(
        f"{name}_Wall_Front_R",
        (right_seg_width, wt, height),
        location=(position[0] + (width / 2.0 - right_seg_width / 2.0), position[1] - half_d + wt / 2, position[2] + height / 2),
        material=get_white_material("RoomWall", rough=0.28),
    )
    back = create_box(
        f"{name}_Wall_Back",
        (width, wt, height),
        location=(position[0], position[1] + half_d - wt / 2, position[2] + height / 2),
        material=get_white_material("RoomWall", rough=0.28),
    )
    left = create_box(
        f"{name}_Wall_Left",
        (depth, wt, height),
        location=(position[0] - half_w + wt / 2, position[1], position[2] + height / 2),
        material=get_white_material("RoomWall", rough=0.28),
    )
    right = create_box(
        f"{name}_Wall_Right",
        (depth, wt, height),
        location=(position[0] + half_w - wt / 2, position[1], position[2] + height / 2),
        material=get_white_material("RoomWall", rough=0.28),
    )
    left.rotation_euler = Euler((0, 0, math.radians(90)), 'XYZ')
    right.rotation_euler = Euler((0, 0, math.radians(90)), 'XYZ')
    door_world_x = door_center_x
    door_world_y = position[1] - half_d
    door_world_z = position[2]
    return {
        "parts": [floor, ceiling, front_left, front_right, back, left, right],
        "door_pos": (door_world_x, door_world_y + wt / 2, door_world_z),
    }


def create_sliding_door_group(position=(0, -40, 0), width=DOOR_WIDTH, height=DOOR_HEIGHT, thickness=0.12, orientation='Y'):
    door_empty = bpy.data.objects.new("door_group", None)
    bpy.context.scene.collection.objects.link(door_empty)
    door_empty.location = position
    left_loc = (-(width / 4.0), 0.0, height / 2.0)
    right_loc = ((width / 4.0), 0.0, height / 2.0)
    left = create_box(
        "door_L",
        (width / 2.0 - 0.02, thickness, height),
        location=(position[0] + left_loc[0], position[1] + left_loc[1], position[2] + left_loc[2]),
        material=get_white_material("DoorMat", rough=0.18),
    )
    right = create_box(
        "door_R",
        (width / 2.0 - 0.02, thickness, height),
        location=(position[0] + right_loc[0], position[1] + right_loc[1], position[2] + right_loc[2]),
        material=get_white_material("DoorMat", rough=0.18),
    )
    left.parent = door_empty
    right.parent = door_empty
    left["closed_pos"] = tuple(left.location)
    right["closed_pos"] = tuple(right.location)
    open_offset = width * 0.5 + 0.05
    left_open = Vector(left.location) + Vector((-open_offset, 0.0, 0.0))
    right_open = Vector(right.location) + Vector((open_offset, 0.0, 0.0))
    left["open_pos"] = tuple(left_open)
    right["open_pos"] = tuple(right_open)
    door_empty["is_door_group"] = True
    door_empty["panels"] = [left.name, right.name]
    return door_empty


# create single action "Door_Open" and keyframe both panels into it; then push the action as an NLA strip on the door empty (for easy engine selection)
def animate_sliding_door_as_action(door_empty, frame_start=1, frame_open=36, frame_close=120):
    panels = door_empty.get("panels", [])
    # make new action
    action_name = "Door_Open"
    if action_name in bpy.data.actions:
        action = bpy.data.actions[action_name]
    else:
        action = bpy.data.actions.new(action_name)
    # for each panel, assign action and insert keyframes (location)
    for name in panels:
        panel = bpy.data.objects.get(name)
        if not panel:
            continue
        panel.animation_data_create()
        # assign the shared action to panel's animation_data - this will write fcurves into this action
        panel.animation_data.action = action
        closed = Vector(panel["closed_pos"])
        openp = Vector(panel["open_pos"])
        panel.location = closed
        panel.keyframe_insert(data_path="location", frame=frame_start)
        panel.location = openp
        panel.keyframe_insert(data_path="location", frame=frame_open)
        panel.location = closed
        panel.keyframe_insert(data_path="location", frame=frame_close)
    # create NLA strip on the door_empty referencing the action (so engine artists can find it easily)
    door_empty.animation_data_create()
    track = door_empty.animation_data.nla_tracks.new()
    track.name = "Door_NLA"
    strip = track.strips.new(action.name + "_strip", frame_start, action)
    strip.action_frame_start = frame_start
    strip.action_frame_end = frame_close
    # tag door_empty with the action name for easy lookup in engine
    door_empty["door_action"] = action.name


def create_portal_frame(position=(0, -120, 0), width=4.5, height=5.0):
    outer = create_box(
        "Portal_Frame",
        (width + 0.4, 0.4, height + 0.4),
        location=(position[0], position[1], position[2] + height / 2),
        material=get_white_material("PortalFrame", rough=0.15),
    )
    plane = create_plane(
        "Portal_Surface",
        width - 0.1,
        height - 0.1,
        location=(position[0], position[1] + 0.01, position[2] + height / 2),
        material=get_emissive_material("PortalEmit", color=(0.6, 0.85, 1.0, 1.0), strength=8.0),
    )
    return (outer, plane)


def create_bridge(position=(50, -160, 0), length=20, width=3.0):
    bridge = create_box(
        "Bridge",
        (length, width, 0.15),
        location=(position[0], position[1], position[2] + 0.08),
        material=get_white_material("BridgeFloor", rough=0.18),
    )
    edge_l = create_box(
        "Bridge_Edge_L",
        (length, 0.06, 0.05),
        location=(position[0], position[1] - width / 2 - 0.03, position[2] + 0.09),
        material=get_emissive_material("BridgeEdgeMat", color=(0.5, 0.85, 1.0, 1.0), strength=6.0),
    )
    edge_r = create_box(
        "Bridge_Edge_R",
        (length, 0.06, 0.05),
        location=(position[0], position[1] + width / 2 + 0.03, position[2] + 0.09),
        material=get_emissive_material("BridgeEdgeMat", color=(0.5, 0.85, 1.0, 1.0), strength=6.0),
    )
    return [bridge, edge_l, edge_r]


def create_spiral_staircase(center=(0, -80, 0), steps=20, radius=3.0, step_height=0.28, step_depth=0.8):
    objs = []
    for i in range(steps):
        angle = i * (2 * math.pi / steps)
        x = center[0] + math.cos(angle) * radius
        y = center[1] + math.sin(angle) * radius
        z = center[2] + i * step_height
        step = create_box(
            f"Stair_{i}",
            (radius * 0.5, step_depth, 0.15),
            location=(x, y, z + 0.075),
            material=get_white_material("StairMat", rough=0.25),
        )
        step.rotation_euler = Euler((0, 0, -angle), 'XYZ')
        objs.append(step)
    return objs


def create_projection_plane(position=(0, -78, 4), w=6, h=3):
    plane = create_plane(
        "ProjectionPlane",
        w,
        h,
        location=(position[0], position[1], position[2]),
        material=get_emissive_material("ProjectionMat", color=(0.9, 0.95, 1.0, 1.0), strength=4.0),
    )
    plane.rotation_euler = Euler((0, 0, 0), 'XYZ')
    return plane


def create_player_placeholder(position=(0, -78, 1.0)):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.35, location=(position[0], position[1], position[2] + 0.9))
    head = bpy.context.object
    head.name = "PlayerHead"
    cyl = create_cylinder(
        "PlayerBody",
        radius=0.4,
        depth=1.4,
        location=(position[0], position[1], position[2] + 0.7),
        material=get_white_material("PlayerMat", rough=0.9),
    )
    return (head, cyl)


# ---------------------------
# Create a 1x1 black png for overlay use in Three.js
# ---------------------------
def save_black_overlay_png(path):
    # create 1x1 image in Blender and save as PNG
    img_name = "overlay_black_img"
    if img_name in bpy.data.images:
        img = bpy.data.images[img_name]
    else:
        img = bpy.data.images.new(img_name, width=1, height=1, alpha=True, float_buffer=False)
        img.pixels = [0.0, 0.0, 0.0, 1.0]
    img.filepath_raw = path
    img.file_format = 'PNG'
    try:
        img.save()
        print("Saved overlay PNG to:", path)
    except Exception as e:
        print("Failed saving overlay PNG:", e)


# ---------------------------
# View helpers
# ---------------------------
def set_all_view3d_to_material_preview():
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                space = area.spaces.active
                try:
                    space.shading.type = 'MATERIAL'
                except:
                    pass
                try:
                    space.shading.color_type = 'MATERIAL'
                except:
                    pass


def apply_material_color_to_object_viewport():
    for obj in bpy.data.objects:
        if obj.type != 'MESH':
            continue
        col = None
        if obj.data.materials:
            mat = obj.data.materials[0]
            if mat is None:
                continue
            if mat.use_nodes and mat.node_tree:
                principled = None
                emission = None
                for n in mat.node_tree.nodes:
                    if n.type == 'BSDF_PRINCIPLED' and principled is None:
                        principled = n
                    if n.type == 'EMISSION' and emission is None:
                        emission = n
                if principled:
                    try:
                        col = tuple(principled.inputs['Base Color'].default_value)
                    except:
                        pass
                if col is None and emission:
                    try:
                        col = tuple(emission.inputs['Color'].default_value)
                    except:
                        pass
            else:
                try:
                    col = tuple(mat.diffuse_color)
                except:
                    pass
        if col:
            if len(col) == 3:
                col = (col[0], col[1], col[2], 1.0)
            try:
                obj.color = col
            except:
                pass
            try:
                mat.diffuse_color = col
            except:
                pass


# ---------------------------
# Build world (main)
# ---------------------------
def build_world_and_prepare():
    clear_scene()
    try:
        bpy.context.scene.unit_settings.system = 'METRIC'
    except:
        pass

    # Lights & cam
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

    # Env + LOD forest
    create_ground()
    create_sky_dome(radius=180)
    create_dense_forest_lod(rows=7, cols=7, spacing=16, base_y=-140)

    # entrance & door
    create_circular_hall(radius=8.5, height=14.0, position=WORLD_LAYOUT["entrance_hall"])
    create_rect_room_with_doorgap("EntranceRoomShell", 18, 18, 14, position=WORLD_LAYOUT["entrance_hall"])
    door_pos = WORLD_LAYOUT["auto_door"]
    door = create_sliding_door_group(position=door_pos, width=DOOR_WIDTH, height=DOOR_HEIGHT, thickness=0.12, orientation='Y')
    return {"camera": cam, "door": door}


def finalize_and_export(prep, frame_start=1, frame_open=36, frame_close=120):
    door = prep.get("door")
    # other rooms & features
    create_projection_plane(position=(WORLD_LAYOUT["entrance_hall"][0], WORLD_LAYOUT["entrance_hall"][1] + 2, 4), w=6, h=3)
    create_rect_room_with_doorgap("MotivationRoom", 16, 12, 6, position=WORLD_LAYOUT["motivation_room"])
    create_rect_room_with_doorgap("TheoryRoom", 18, 14, 6, position=WORLD_LAYOUT["theory_room"])
    create_rect_room_with_doorgap("ProgrammingRoom", 18, 14, 6, position=WORLD_LAYOUT["programming_room"])
    create_rect_room_with_doorgap("FormulaRoom", 14, 12, 6, position=WORLD_LAYOUT["formula_room"])
    create_rect_room_with_doorgap("SimulationCenter", 28, 20, 8, position=WORLD_LAYOUT["simulation_center"])
    create_rect_room_with_doorgap("ConclusionRoom", 14, 12, 6, position=WORLD_LAYOUT["conclusion_room"])
    create_rect_room_with_doorgap("FutureRoom", 14, 12, 6, position=WORLD_LAYOUT["future_room"])
    create_bridge(position=(50, -160, 0), length=20, width=3)
    create_portal_frame(position=(0, -120, 0))
    create_spiral_staircase(center=(0, WORLD_LAYOUT["entrance_hall"][1] + 3, 0), steps=20, radius=3.5)
    create_player_placeholder(position=(0, WORLD_LAYOUT["entrance_hall"][1] + 2, 0.5))

    # animate door as single action + NLA strip (no auto-trigger)
    if door:
        animate_sliding_door_as_action(door, frame_start=frame_start, frame_open=frame_open, frame_close=frame_close)

    # prepare black overlay png for Three.js fade (1x1)
    save_black_overlay_png(OVERLAY_PNG)

    # tidy apply scales
    for ob in [o for o in bpy.data.objects if o.type == 'MESH']:
        bpy.context.view_layer.objects.active = ob
        ob.select_set(True)
        try:
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        except:
            pass
        ob.select_set(False)

    # ensure export dir exists
    export_dir = os.path.dirname(EXPORT_PATH)
    if export_dir and not os.path.exists(export_dir):
        try:
            os.makedirs(export_dir, exist_ok=True)
        except:
            pass

    set_all_view3d_to_material_preview()
    apply_material_color_to_object_viewport()

    # export GLB with animations
    bpy.ops.export_scene.gltf(filepath=EXPORT_PATH, export_format='GLB', export_apply=True, export_yup=True, export_animations=True)
    print("Exported GLB to:", EXPORT_PATH)
    print("Overlay PNG:", OVERLAY_PNG)
    return EXPORT_PATH


# ---------------------------
# Run
# ---------------------------
if __name__ == "__main__":
    if not bpy.data.is_saved:
        print("Warning: .blend not saved. Export will go to:", EXPORT_DIR)
    prep = build_world_and_prepare()
    out = finalize_and_export(prep, frame_start=1, frame_open=36, frame_close=120)
    print("Done. GLB:", out)
