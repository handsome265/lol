"""
Ultimate Sci‑Fi Laboratory Generator (Blender 5.0.1)
- Closed multi-level research base with roof shell + skylights
- Functional zones: lobby, labs, server/AI, test chamber, control center
- Animated doors, fans, scanners, energy rings, bridge flow particles
- Cinematic lighting and GLB export

Usage:
1) Blender 5.0.1 -> Scripting
2) Paste this script -> Run Script
3) GLB exports to ~/Desktop/ultimate_lab_pro.glb
"""

import os
import math
import random
import bpy
from mathutils import Vector

# --------------------------------------------------
# Config
# --------------------------------------------------
EXPORT_NAME = "ultimate_lab_pro.glb"
EXPORT_PATH = os.path.join(os.path.expanduser("~"), "Desktop", EXPORT_NAME)

COLORS = {
    "steel": (0.63, 0.67, 0.74, 1.0),
    "panel": (0.90, 0.92, 0.97, 1.0),
    "dark": (0.06, 0.08, 0.13, 1.0),
    "cyan": (0.0, 0.88, 1.0, 1.0),
    "magenta": (1.0, 0.24, 0.70, 1.0),
    "purple": (0.62, 0.28, 1.0, 1.0),
    "green": (0.2, 0.95, 0.55, 1.0),
    "white": (0.97, 0.97, 1.0, 1.0),
}

LAYOUT = {
    # z=0 ground level
    "lobby": (0, 0, 0),
    "common_lab": (34, 0, 0),
    "rest_area": (-34, 0, 0),
    "service_core": (0, -28, 0),
    # z=6 upper deck
    "ai_lab": (34, 0, 6),
    "chem_lab": (0, 28, 6),
    "physics_lab": (-34, 0, 6),
    "control_center": (0, -28, 6),
}

ROOM_SIZE = {
    "lobby": (24, 20, 8),
    "common_lab": (24, 20, 8),
    "rest_area": (20, 16, 7),
    "service_core": (20, 16, 7),
    "ai_lab": (24, 20, 8),
    "chem_lab": (24, 20, 8),
    "physics_lab": (24, 20, 8),
    "control_center": (20, 16, 8),
}

MATS = {}


# --------------------------------------------------
# Low-level helpers
# --------------------------------------------------
def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False, confirm=False)
    for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.images, bpy.data.textures, bpy.data.cameras, bpy.data.lights):
        for it in list(coll):
            try:
                if getattr(it, "users", 0) == 0:
                    coll.remove(it)
            except Exception:
                pass


def ensure_world():
    if bpy.context.scene.world is None:
        bpy.context.scene.world = bpy.data.worlds.new("World")
    w = bpy.context.scene.world
    w.use_nodes = True
    n = w.node_tree.nodes
    l = w.node_tree.links
    n.clear()
    out = n.new("ShaderNodeOutputWorld")
    bg = n.new("ShaderNodeBackground")
    bg.inputs["Color"].default_value = (0.01, 0.02, 0.06, 1.0)
    bg.inputs["Strength"].default_value = 0.35
    l.new(bg.outputs["Background"], out.inputs["Surface"])


def mat_pbr(name, color=(1, 1, 1, 1), rough=0.4, metal=0.1, emit=0.0):
    key = ("pbr", name, color, rough, metal, emit)
    if key in MATS:
        return MATS[key]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    n = m.node_tree.nodes
    l = m.node_tree.links
    n.clear()
    out = n.new("ShaderNodeOutputMaterial")
    bsdf = n.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if emit > 0:
        try:
            bsdf.inputs["Emission Color"].default_value = color
            bsdf.inputs["Emission Strength"].default_value = emit
        except Exception:
            try:
                bsdf.inputs["Emission"].default_value = color
                bsdf.inputs["Emission Strength"].default_value = emit
            except Exception:
                pass
    l.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    MATS[key] = m
    return m


def mat_neon(name, color, strength=12.0):
    key = ("neon", name, color, strength)
    if key in MATS:
        return MATS[key]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    n = m.node_tree.nodes
    l = m.node_tree.links
    n.clear()
    out = n.new("ShaderNodeOutputMaterial")
    em = n.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = color
    em.inputs["Strength"].default_value = strength
    l.new(em.outputs["Emission"], out.inputs["Surface"])
    MATS[key] = m
    return m


def mat_glass(name, color=(0.6, 0.85, 1.0, 0.35), rough=0.02):
    key = ("glass", name, color, rough)
    if key in MATS:
        return MATS[key]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    n = m.node_tree.nodes
    l = m.node_tree.links
    n.clear()
    out = n.new("ShaderNodeOutputMaterial")
    glass = n.new("ShaderNodeBsdfGlass")
    glass.inputs["Color"].default_value = color
    glass.inputs["Roughness"].default_value = rough
    glass.inputs["IOR"].default_value = 1.45
    l.new(glass.outputs["BSDF"], out.inputs["Surface"])
    m.blend_method = 'BLEND'
    MATS[key] = m
    return m


def assign_mat(obj, mat):
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)


def box(name, size, loc=(0, 0, 0), rot=(0, 0, 0), mat=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    if mat:
        assign_mat(o, mat)
    return o


def plane(name, sx, sy, loc=(0, 0, 0), rot=(0, 0, 0), mat=None):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = (sx / 2, sy / 2, 1)
    if mat:
        assign_mat(o, mat)
    return o


def cyl(name, r, h, loc=(0, 0, 0), rot=(0, 0, 0), verts=24, mat=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=h, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    if mat:
        assign_mat(o, mat)
    return o


def torus(name, major, minor, loc=(0, 0, 0), rot=(0, 0, 0), mat=None):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    if mat:
        assign_mat(o, mat)
    return o


def animate_rotation(obj, frame_end=240, axis='z', turns=1.0):
    obj.keyframe_insert(data_path="rotation_euler", frame=1)
    delta = math.radians(360 * turns)
    if axis == 'x':
        obj.rotation_euler.x += delta
    elif axis == 'y':
        obj.rotation_euler.y += delta
    else:
        obj.rotation_euler.z += delta
    obj.keyframe_insert(data_path="rotation_euler", frame=frame_end)


def pulse_emission(mat, start=1, end=180, low=2.0, high=10.0):
    if not mat.use_nodes:
        return
    for node in mat.node_tree.nodes:
        if node.type == 'EMISSION':
            node.inputs["Strength"].default_value = low
            node.inputs["Strength"].keyframe_insert("default_value", frame=start)
            node.inputs["Strength"].default_value = high
            node.inputs["Strength"].keyframe_insert("default_value", frame=(start + end) // 2)
            node.inputs["Strength"].default_value = low
            node.inputs["Strength"].keyframe_insert("default_value", frame=end)
            break


# --------------------------------------------------
# Architectural shell (closed roof + skylights)
# --------------------------------------------------
def create_outer_envelope():
    shell_mat = mat_pbr("ShellMetal", COLORS["steel"], rough=0.35, metal=0.75)
    dark_mat = mat_pbr("DarkPanel", COLORS["dark"], rough=0.6, metal=0.35)
    glass_mat = mat_glass("SkylightGlass", (0.6, 0.86, 1.0, 0.28), 0.02)

    # Main platform
    plane("BasePlate", 180, 220, loc=(0, -80, -0.2), mat=dark_mat)

    # Perimeter walls (closed structure)
    box("Wall_N", (180, 1.2, 18), loc=(0, 30, 9), mat=shell_mat)
    box("Wall_S", (180, 1.2, 18), loc=(0, -190, 9), mat=shell_mat)
    box("Wall_E", (1.2, 220, 18), loc=(90, -80, 9), mat=shell_mat)
    box("Wall_W", (1.2, 220, 18), loc=(-90, -80, 9), mat=shell_mat)

    # Roof slab
    roof = plane("RoofMain", 178, 218, loc=(0, -80, 18), mat=shell_mat)

    # Truss beams on roof
    for i in range(-5, 6):
        box(f"RoofBeam_X_{i}", (0.6, 218, 0.8), loc=(i * 16, -80, 18.4), mat=shell_mat)
    for j in range(-6, 7):
        box(f"RoofBeam_Y_{j}", (178, 0.6, 0.8), loc=(0, -80 + j * 16, 18.2), mat=shell_mat)

    # Skylight strips
    for i in range(-3, 4):
        plane(f"Skylight_{i}", 10, 190, loc=(i * 20, -80, 18.45), mat=glass_mat)


# --------------------------------------------------
# Rooms / corridors / bridges
# --------------------------------------------------
def create_room(name, center, size, theme_color):
    w, d, h = size
    x, y, z = center

    floor_mat = mat_pbr(f"{name}_Floor", (0.16, 0.18, 0.24, 1), rough=0.35, metal=0.75)
    wall_mat = mat_pbr(f"{name}_Wall", COLORS["panel"], rough=0.52, metal=0.15)
    ceil_mat = mat_pbr(f"{name}_Ceiling", (0.84, 0.87, 0.94, 1), rough=0.45, metal=0.1)
    edge_mat = mat_neon(f"{name}_EdgeNeon", theme_color, strength=10)

    plane(f"{name}_FloorMesh", w, d, loc=(x, y, z), mat=floor_mat)
    plane(f"{name}_CeilMesh", w, d, loc=(x, y, z + h), mat=ceil_mat)

    hw, hd, hh = w / 2, d / 2, h / 2
    box(f"{name}_N", (w, 0.6, h), loc=(x, y + hd, z + hh), mat=wall_mat)
    box(f"{name}_S", (w, 0.6, h), loc=(x, y - hd, z + hh), mat=wall_mat)
    box(f"{name}_E", (0.6, d, h), loc=(x + hw, y, z + hh), mat=wall_mat)
    box(f"{name}_W", (0.6, d, h), loc=(x - hw, y, z + hh), mat=wall_mat)

    for i, (sx, sy) in enumerate(((hw, hd), (hw, -hd), (-hw, hd), (-hw, -hd))):
        cyl(f"{name}_LightCol_{i}", 0.10, h, loc=(x + sx, y + sy, z + hh), mat=edge_mat)

    # Ceiling light grid
    light_panel_mat = mat_neon(f"{name}_LightPanel", (0.92, 0.96, 1.0, 1), strength=6)
    pulse_emission(light_panel_mat, low=3.0, high=8.0)
    for gx in range(3):
        for gy in range(3):
            px = x - w / 2 + (gx + 0.5) * (w / 3)
            py = y - d / 2 + (gy + 0.5) * (d / 3)
            plane(f"{name}_Panel_{gx}_{gy}", w / 4.2, d / 4.2, loc=(px, py, z + h - 0.06), mat=light_panel_mat)


def create_corridor(name, start, end, width=8, z=0):
    v = Vector(end) - Vector(start)
    length = v.length
    center = (Vector(start) + Vector(end)) / 2
    angle = math.atan2(v.y, v.x)

    floor_mat = mat_pbr(f"{name}_Floor", (0.20, 0.22, 0.28, 1), rough=0.28, metal=0.7)
    edge_l = mat_neon(f"{name}_EdgeL", COLORS["cyan"], 12)
    edge_r = mat_neon(f"{name}_EdgeR", COLORS["magenta"], 12)

    plane(f"{name}_Mesh", length, width, loc=(center.x, center.y, z + 0.03), rot=(0, 0, angle), mat=floor_mat)
    plane(f"{name}_EdgeL", length, 0.26, loc=(center.x, center.y + width / 2 - 0.15, z + 0.05), rot=(0, 0, angle), mat=edge_l)
    plane(f"{name}_EdgeR", length, 0.26, loc=(center.x, center.y - width / 2 + 0.15, z + 0.05), rot=(0, 0, angle), mat=edge_r)


def room_edge_port(center, size, direction):
    """Return a connection point snapped to a room wall edge.

    direction: '+x', '-x', '+y', '-y'
    """
    x, y, z = center
    w, d, h = size
    if direction == '+x':
        return (x + w / 2, y, z)
    if direction == '-x':
        return (x - w / 2, y, z)
    if direction == '+y':
        return (x, y + d / 2, z)
    return (x, y - d / 2, z)


def create_enclosed_corridor(name, start, end, width=8, height=5.2, thickness=0.32, z=0):
    """Create a sealed corridor (floor + ceiling + side walls) between two room-edge ports.

    This avoids visual gaps where only a flat floor strip existed.
    """
    v = Vector(end) - Vector(start)
    length = v.length
    center = (Vector(start) + Vector(end)) / 2
    angle = math.atan2(v.y, v.x)

    floor_mat = mat_pbr(f"{name}_Floor", (0.22, 0.24, 0.30, 1), rough=0.30, metal=0.72)
    ceil_mat = mat_pbr(f"{name}_Ceil", (0.84, 0.88, 0.95, 1), rough=0.45, metal=0.12)
    wall_mat = mat_pbr(f"{name}_Wall", COLORS["panel"], rough=0.52, metal=0.16)
    edge_mat = mat_neon(f"{name}_Edge", COLORS["cyan"], 10)

    # Floor / Ceiling
    plane(f"{name}_FloorMesh", length, width, loc=(center.x, center.y, z + 0.03), rot=(0, 0, angle), mat=floor_mat)
    plane(f"{name}_CeilMesh", length, width, loc=(center.x, center.y, z + height), rot=(0, 0, angle), mat=ceil_mat)

    # Side walls
    off = width / 2 + thickness / 2
    px = -math.sin(angle)
    py = math.cos(angle)
    box(
        f"{name}_WallL",
        (length, thickness, height),
        loc=(center.x + px * off, center.y + py * off, z + height / 2),
        rot=(0, 0, angle),
        mat=wall_mat,
    )
    box(
        f"{name}_WallR",
        (length, thickness, height),
        loc=(center.x - px * off, center.y - py * off, z + height / 2),
        rot=(0, 0, angle),
        mat=wall_mat,
    )

    # Inner neon strips
    plane(f"{name}_NeonL", length, 0.10, loc=(center.x + px * (off - thickness / 2), center.y + py * (off - thickness / 2), z + height - 0.12), rot=(0, 0, angle), mat=edge_mat)
    plane(f"{name}_NeonR", length, 0.10, loc=(center.x - px * (off - thickness / 2), center.y - py * (off - thickness / 2), z + height - 0.12), rot=(0, 0, angle), mat=edge_mat)


def create_light_bridge(name, start, end, width=7.0):
    v = Vector(end) - Vector(start)
    length = v.length
    center = (Vector(start) + Vector(end)) / 2
    angle = math.atan2(v.y, v.x)

    surf = mat_glass(f"{name}_Glass", (0.45, 0.85, 1.0, 0.30), 0.08)
    edge = mat_neon(f"{name}_Edge", COLORS["cyan"], 14)

    plane(f"{name}_Surf", length, width, loc=(center.x, center.y, start[2] + 0.12), rot=(0, 0, angle), mat=surf)
    plane(f"{name}_EdgeL", length, 0.30, loc=(center.x, center.y + width / 2 - 0.18, start[2] + 0.14), rot=(0, 0, angle), mat=edge)
    plane(f"{name}_EdgeR", length, 0.30, loc=(center.x, center.y - width / 2 + 0.18, start[2] + 0.14), rot=(0, 0, angle), mat=edge)

    # Flow particles along bridge
    pmat = mat_neon(f"{name}_FlowParticle", COLORS["purple"], 18)
    count = max(6, int(length / 3))
    for i in range(count):
        t = i / count
        px = start[0] + v.x * t
        py = start[1] + v.y * t
        pz = start[2] + 0.45
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.12, location=(px, py, pz))
        p = bpy.context.object
        p.name = f"{name}_Flow_{i}"
        assign_mat(p, pmat)
        p.keyframe_insert(data_path="location", frame=1)
        p.location.x, p.location.y = end[0], end[1]
        p.keyframe_insert(data_path="location", frame=120)


# --------------------------------------------------
# Functional equipment
# --------------------------------------------------
def create_sliding_door(origin, width=9.0, height=5.4):
    frame_mat = mat_pbr("DoorFrame", COLORS["steel"], rough=0.26, metal=0.9, emit=0.5)
    glass_mat = mat_glass("DoorPanel", (0.5, 0.8, 1.0, 0.35), 0.04)
    strip_mat = mat_neon("DoorStrip", COLORS["cyan"], 16)

    box("MainDoorTop", (width, 0.4, 0.4), loc=(origin[0], origin[1], height + 0.2), mat=frame_mat)
    box("MainDoorLCol", (0.4, 0.4, height), loc=(origin[0] - width / 2, origin[1], height / 2), mat=frame_mat)
    box("MainDoorRCol", (0.4, 0.4, height), loc=(origin[0] + width / 2, origin[1], height / 2), mat=frame_mat)

    panel_w = width / 2 - 0.35
    panel_h = height - 0.4
    left = box("MainDoorLeft", (panel_w, 0.14, panel_h), loc=(origin[0] - panel_w / 2, origin[1], panel_h / 2), mat=glass_mat)
    right = box("MainDoorRight", (panel_w, 0.14, panel_h), loc=(origin[0] + panel_w / 2, origin[1], panel_h / 2), mat=glass_mat)

    box("MainDoorStripL", (0.05, 0.16, panel_h * 0.8), loc=(left.location.x, left.location.y - 0.08, left.location.z), mat=strip_mat)
    box("MainDoorStripR", (0.05, 0.16, panel_h * 0.8), loc=(right.location.x, right.location.y - 0.08, right.location.z), mat=strip_mat)

    # Smooth open animation
    for p, sgn in ((left, -1), (right, 1)):
        p.keyframe_insert(data_path="location", frame=1)
        p.location.x = origin[0] + sgn * width * 0.64
        p.keyframe_insert(data_path="location", frame=80)


def create_ai_server_racks(center):
    x, y, z = center
    rack_mat = mat_pbr("ServerRack", (0.12, 0.14, 0.19, 1), rough=0.45, metal=0.55)
    led_mat = mat_neon("ServerLED", COLORS["green"], 9)

    for i in range(4):
        rx = x - 6 + i * 4
        box(f"AIRack_{i}", (2.2, 1.4, 5.6), loc=(rx, y, z + 2.8), mat=rack_mat)
        for j in range(4):
            box(f"AIRackLED_{i}_{j}", (1.8, 0.05, 0.12), loc=(rx, y - 0.73, z + 1.2 + j * 1.0), mat=led_mat)


def create_chem_pipes(center):
    x, y, z = center
    pipe_mat = mat_pbr("ChemPipe", (0.78, 0.82, 0.9, 1), rough=0.2, metal=0.9)
    glow_mat = mat_neon("ChemGlow", COLORS["magenta"], 10)
    for i in range(5):
        cyl(f"ChemPipeV_{i}", 0.2, 5.8, loc=(x - 7 + i * 3.5, y + 6, z + 3), mat=pipe_mat)
        torus(f"ChemRing_{i}", 0.9, 0.08, loc=(x - 7 + i * 3.5, y + 6, z + 4.8), rot=(math.radians(90), 0, 0), mat=glow_mat)


def create_physics_energy_loop(center):
    x, y, z = center
    ring_outer = mat_neon("PhysRingOuter", COLORS["cyan"], 16)
    ring_inner = mat_neon("PhysRingInner", COLORS["purple"], 12)

    r1 = torus("PhysRing1", 3.2, 0.18, loc=(x, y, z + 3.8), rot=(math.radians(90), 0, 0), mat=ring_outer)
    r2 = torus("PhysRing2", 2.5, 0.13, loc=(x, y, z + 3.8), rot=(math.radians(90), math.radians(35), 0), mat=ring_inner)
    animate_rotation(r1, frame_end=180, axis='z', turns=1.0)
    animate_rotation(r2, frame_end=180, axis='z', turns=-1.0)


def create_control_hologram(center):
    x, y, z = center
    base = mat_pbr("ControlBase", COLORS["steel"], rough=0.3, metal=0.9)
    holo = mat_neon("ControlHolo", COLORS["cyan"], 14)

    cyl("CtrlBase", 2.6, 0.9, loc=(x, y, z + 0.45), mat=base)
    for i in range(3):
        r = torus(f"CtrlHolo_{i}", 1.8 + i * 0.35, 0.07, loc=(x, y, z + 2.8 + i * 0.45), rot=(math.radians(90), 0, math.radians(i * 20)), mat=holo)
        animate_rotation(r, frame_end=180, axis='z', turns=(1 if i % 2 == 0 else -1))


# --------------------------------------------------
# Lighting / camera / render
# --------------------------------------------------
def setup_lighting_camera_render():
    target = LAYOUT["lobby"]

    bpy.ops.object.light_add(type='SUN', location=(55, 40, 95))
    sun = bpy.context.object
    sun.name = "SunKey"
    sun.data.energy = 2.6
    sun.data.color = (1.0, 0.96, 0.92)
    sun.rotation_euler = (math.radians(58), 0, math.radians(35))

    bpy.ops.object.light_add(type='AREA', location=(0, -40, 26))
    fill = bpy.context.object
    fill.name = "FillArea"
    fill.data.energy = 1400
    fill.data.size = 42
    fill.data.color = (0.86, 0.92, 1.0)

    accents = [((38, -30, 12), COLORS["cyan"], 550), ((-38, -30, 12), COLORS["magenta"], 550), ((0, -120, 16), COLORS["purple"], 650)]
    for i, (loc, col, energy) in enumerate(accents):
        bpy.ops.object.light_add(type='POINT', location=loc)
        p = bpy.context.object
        p.name = f"Accent_{i}"
        p.data.energy = energy
        p.data.color = col[:3]

    cam_loc = (36, 84, 42)
    bpy.ops.object.camera_add(location=cam_loc)
    cam = bpy.context.object
    cam.name = "CinematicCam"
    direction = Vector(target) - Vector(cam_loc)
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = 42
    cam.data.dof.use_dof = True
    cam.data.dof.focus_distance = 70
    cam.data.dof.aperture_fstop = 2.8
    bpy.context.scene.camera = cam

    scene = bpy.context.scene
    try:
        scene.render.engine = 'BLENDER_EEVEE_NEXT'
    except Exception:
        scene.render.engine = 'BLENDER_EEVEE'
    try:
        eevee = scene.eevee
        eevee.use_bloom = True
        eevee.bloom_intensity = 0.14
        eevee.use_gtao = True
        eevee.use_ssr = True
        eevee.taa_render_samples = 48
    except Exception:
        pass

    scene.view_settings.view_transform = 'Filmic'
    scene.view_settings.look = 'Very High Contrast'
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 100
    scene.render.fps = 30
    scene.frame_end = 240


# --------------------------------------------------
# Build pipeline
# --------------------------------------------------
def build_ultimate_sci_fi_lab():
    print("🚀 Building Ultimate Sci‑Fi Laboratory...")
    clear_scene()
    ensure_world()

    create_outer_envelope()

    # Ground-level rooms
    create_room("Lobby", LAYOUT["lobby"], ROOM_SIZE["lobby"], COLORS["cyan"])
    create_room("CommonLab", LAYOUT["common_lab"], ROOM_SIZE["common_lab"], COLORS["green"])
    create_room("RestArea", LAYOUT["rest_area"], ROOM_SIZE["rest_area"], COLORS["magenta"])
    create_room("ServiceCore", LAYOUT["service_core"], ROOM_SIZE["service_core"], COLORS["purple"])

    # Upper-level rooms
    create_room("AILab", LAYOUT["ai_lab"], ROOM_SIZE["ai_lab"], COLORS["green"])
    create_room("ChemLab", LAYOUT["chem_lab"], ROOM_SIZE["chem_lab"], COLORS["magenta"])
    create_room("PhysicsLab", LAYOUT["physics_lab"], ROOM_SIZE["physics_lab"], COLORS["cyan"])
    create_room("ControlCenter", LAYOUT["control_center"], ROOM_SIZE["control_center"], COLORS["purple"])

    # Corridors (sealed edge-to-edge connectors to avoid wall gaps)
    create_enclosed_corridor(
        "Cor_Lobby_to_Common",
        room_edge_port(LAYOUT["lobby"], ROOM_SIZE["lobby"], '+x'),
        room_edge_port(LAYOUT["common_lab"], ROOM_SIZE["common_lab"], '-x'),
        width=8,
        height=5.2,
        z=0,
    )
    create_enclosed_corridor(
        "Cor_Lobby_to_Rest",
        room_edge_port(LAYOUT["lobby"], ROOM_SIZE["lobby"], '-x'),
        room_edge_port(LAYOUT["rest_area"], ROOM_SIZE["rest_area"], '+x'),
        width=8,
        height=5.2,
        z=0,
    )
    create_enclosed_corridor(
        "Cor_Lobby_to_Service",
        room_edge_port(LAYOUT["lobby"], ROOM_SIZE["lobby"], '-y'),
        room_edge_port(LAYOUT["service_core"], ROOM_SIZE["service_core"], '+y'),
        width=8,
        height=5.2,
        z=0,
    )

    create_enclosed_corridor(
        "Cor_AI_to_Chem",
        room_edge_port(LAYOUT["ai_lab"], ROOM_SIZE["ai_lab"], '-x'),
        room_edge_port(LAYOUT["chem_lab"], ROOM_SIZE["chem_lab"], '+x'),
        width=8,
        height=5.2,
        z=6,
    )
    create_enclosed_corridor(
        "Cor_Chem_to_Physics",
        room_edge_port(LAYOUT["chem_lab"], ROOM_SIZE["chem_lab"], '-x'),
        room_edge_port(LAYOUT["physics_lab"], ROOM_SIZE["physics_lab"], '+x'),
        width=8,
        height=5.2,
        z=6,
    )
    create_enclosed_corridor(
        "Cor_Physics_to_Control",
        room_edge_port(LAYOUT["physics_lab"], ROOM_SIZE["physics_lab"], '-y'),
        room_edge_port(LAYOUT["control_center"], ROOM_SIZE["control_center"], '+x'),
        width=8,
        height=5.2,
        z=6,
    )

    create_light_bridge("Bridge_AI_Chem", LAYOUT["ai_lab"], LAYOUT["chem_lab"], width=7)
    create_light_bridge("Bridge_Chem_Phys", LAYOUT["chem_lab"], LAYOUT["physics_lab"], width=7)
    create_light_bridge("Bridge_Phys_Control", LAYOUT["physics_lab"], LAYOUT["control_center"], width=7)

    # Main entrance door and interior systems
    create_sliding_door((0, 26, 0))
    create_ai_server_racks(LAYOUT["ai_lab"])
    create_chem_pipes(LAYOUT["chem_lab"])
    create_physics_energy_loop(LAYOUT["physics_lab"])
    create_control_hologram(LAYOUT["control_center"])

    # Atmospheric stars visible via skylights
    star_mat = mat_neon("Stars", COLORS["white"], 14)
    rng = random.Random(42)
    for i in range(250):
        theta = rng.uniform(0, math.pi * 0.55)
        phi = rng.uniform(0, 2 * math.pi)
        rad = 240
        x = rad * math.sin(theta) * math.cos(phi)
        y = -80 + rad * math.sin(theta) * math.sin(phi)
        z = 150 + rad * math.cos(theta)
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=rng.uniform(0.05, 0.13), location=(x, y, z))
        s = bpy.context.object
        s.name = f"Star_{i}"
        assign_mat(s, star_mat)

    setup_lighting_camera_render()
    print("✅ Scene build complete.")


def export_glb(path=EXPORT_PATH):
    print(f"📦 Exporting GLB -> {path}")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=path,
        export_format='GLB',
        export_yup=True,
        export_apply=True,
        export_animations=True,
        export_lights=True,
        export_materials='EXPORT',
        export_colors=True,
        export_attributes=True,
        export_extras=True,
    )
    if os.path.exists(path):
        mb = os.path.getsize(path) / (1024 * 1024)
        print(f"✅ Exported: {path} ({mb:.2f} MB)")


def main():
    build_ultimate_sci_fi_lab()
    export_glb(EXPORT_PATH)
    print("🎉 All done.")


if __name__ == "__main__":
    main()
