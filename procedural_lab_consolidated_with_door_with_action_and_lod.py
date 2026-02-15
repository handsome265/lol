"""
Blender 5.0.1 script
- Procedurally builds a sci-fi lab scene
- Adds animated sliding door
- Exports GLB to Desktop as ultimate_lab_pro.glb

Usage (inside Blender 5.0.1):
1) Open Scripting workspace
2) Paste this file content
3) Run Script
"""

import bpy
import os
import math
import random
from mathutils import Vector

# =========================
# Config
# =========================
EXPORT_NAME = "ultimate_lab_pro.glb"
DESKTOP = os.path.join(os.path.expanduser("~"), "Desktop")
EXPORT_PATH = os.path.join(DESKTOP, EXPORT_NAME)

LAYOUT = {
    "outdoor": (0, 0, 0),
    "auto_door": (0, -20, 0),
    "entrance_hall": (0, -38, 0),
    "stair_top": (0, -38, 6),
    "motivation_room": (0, -65, 6),
    "theory_room": (0, -92, 6),
    "programming_room": (0, -119, 6),
    "formula_room": (0, -146, 6),
    "simulation_center": (0, -190, 6),
    "conclusion_room": (0, -235, 6),
    "future_room": (0, -262, 6),
}

COLORS = {
    "cyan": (0.0, 0.88, 1.0, 1.0),
    "magenta": (1.0, 0.2, 0.7, 1.0),
    "purple": (0.6, 0.2, 1.0, 1.0),
    "white": (0.97, 0.97, 1.0, 1.0),
}

MAT_CACHE = {}


# =========================
# Utilities
# =========================
def safe_unlink_data_block(collection):
    for item in list(collection):
        try:
            if hasattr(item, "users") and item.users == 0:
                collection.remove(item)
        except Exception:
            pass


def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False, confirm=False)

    safe_unlink_data_block(bpy.data.meshes)
    safe_unlink_data_block(bpy.data.materials)
    safe_unlink_data_block(bpy.data.images)
    safe_unlink_data_block(bpy.data.textures)
    safe_unlink_data_block(bpy.data.lights)
    safe_unlink_data_block(bpy.data.cameras)


# =========================
# Materials (Blender 5.0.1)
# =========================
def mat_neon(name, color=(0, 1, 1, 1), strength=10.0):
    key = ("neon", name, color, strength)
    if key in MAT_CACHE:
        return MAT_CACHE[key]

    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    n = mat.node_tree.nodes
    l = mat.node_tree.links
    n.clear()

    out = n.new("ShaderNodeOutputMaterial")
    em = n.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = color
    em.inputs["Strength"].default_value = strength
    l.new(em.outputs["Emission"], out.inputs["Surface"])

    MAT_CACHE[key] = mat
    return mat


def mat_pbr(name, base=(0.9, 0.9, 0.95, 1), rough=0.4, metallic=0.1, emission=0.0):
    key = ("pbr", name, base, rough, metallic, emission)
    if key in MAT_CACHE:
        return MAT_CACHE[key]

    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    n = mat.node_tree.nodes
    l = mat.node_tree.links
    n.clear()

    out = n.new("ShaderNodeOutputMaterial")
    bsdf = n.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = base
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metallic

    if emission > 0:
        try:
            bsdf.inputs["Emission Color"].default_value = base
            bsdf.inputs["Emission Strength"].default_value = emission
        except Exception:
            try:
                bsdf.inputs["Emission"].default_value = base
                bsdf.inputs["Emission Strength"].default_value = emission
            except Exception:
                pass

    l.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    MAT_CACHE[key] = mat
    return mat


def mat_glass(name, color=(0.5, 0.8, 1.0, 1.0), rough=0.0):
    key = ("glass", name, color, rough)
    if key in MAT_CACHE:
        return MAT_CACHE[key]

    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    n = mat.node_tree.nodes
    l = mat.node_tree.links
    n.clear()

    out = n.new("ShaderNodeOutputMaterial")
    glass = n.new("ShaderNodeBsdfGlass")
    glass.inputs["Color"].default_value = color
    glass.inputs["Roughness"].default_value = rough
    glass.inputs["IOR"].default_value = 1.45

    l.new(glass.outputs["BSDF"], out.inputs["Surface"])
    mat.blend_method = 'BLEND'

    MAT_CACHE[key] = mat
    return mat


# =========================
# Primitive helpers
# =========================
def apply_mat(obj, mat):
    if not mat:
        return
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)


def create_box(name, size, loc=(0, 0, 0), rot=(0, 0, 0), mat=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    apply_mat(o, mat)
    return o


def create_plane(name, sx, sy, loc=(0, 0, 0), rot=(0, 0, 0), mat=None):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = (sx / 2, sy / 2, 1)
    apply_mat(o, mat)
    return o


def create_cylinder(name, r, h, loc=(0, 0, 0), rot=(0, 0, 0), mat=None, verts=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=h, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    apply_mat(o, mat)
    return o


def create_torus(name, major, minor, loc=(0, 0, 0), rot=(0, 0, 0), mat=None):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    apply_mat(o, mat)
    return o


# =========================
# Scene builders
# =========================
def setup_world():
    if bpy.context.scene.world is None:
        bpy.context.scene.world = bpy.data.worlds.new("World")
    world = bpy.context.scene.world
    world.use_nodes = True

    n = world.node_tree.nodes
    l = world.node_tree.links
    n.clear()

    out = n.new("ShaderNodeOutputWorld")
    bg = n.new("ShaderNodeBackground")
    bg.inputs["Color"].default_value = (0.02, 0.03, 0.08, 1.0)
    bg.inputs["Strength"].default_value = 0.35
    l.new(bg.outputs["Background"], out.inputs["Surface"])


def create_star_field(count=250, radius=280.0):
    star_mat = mat_neon("StarNeon", (1, 1, 1, 1), 12.0)
    rng = random.Random(42)
    for i in range(count):
        theta = rng.uniform(0, math.pi * 0.6)
        phi = rng.uniform(0, 2 * math.pi)
        x = radius * math.sin(theta) * math.cos(phi)
        y = radius * math.sin(theta) * math.sin(phi)
        z = radius * math.cos(theta)
        r = rng.uniform(0.05, 0.15)
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=r, location=(x, y, z))
        s = bpy.context.object
        s.name = f"Star_{i}"
        apply_mat(s, star_mat)


def create_ground_and_path():
    create_plane("Ground", 900, 900, loc=(0, -140, -0.1), mat=mat_pbr("Ground", (0.12, 0.13, 0.18, 1), 0.7, 0.2))

    path_start = LAYOUT["outdoor"][1]
    path_end = LAYOUT["entrance_hall"][1]
    path_len = abs(path_end - path_start) + 10
    center_y = (path_start + path_end) / 2

    create_plane("Walkway", 10, path_len, loc=(0, center_y, 0.02), mat=mat_pbr("Path", (0.8, 0.82, 0.9, 1), 0.25, 0.8))
    create_plane("PathEdgeL", 0.3, path_len, loc=(5.2, center_y, 0.04), mat=mat_neon("PathEdgeLC", COLORS["cyan"], 18))
    create_plane("PathEdgeR", 0.3, path_len, loc=(-5.2, center_y, 0.04), mat=mat_neon("PathEdgeRC", COLORS["magenta"], 18))


def create_forest(rows=3, spacing=7):
    rng = random.Random(123)
    start_y = LAYOUT["outdoor"][1] + 8
    end_y = LAYOUT["entrance_hall"][1] - 5
    trunk_mat = mat_pbr("Trunk", (0.2, 0.15, 0.1, 1), 0.8, 0)
    leaf_mat = mat_neon("Leaf", (0.1, 0.6, 0.25, 1), 2.5)

    idx = 0
    for side in (-1, 1):
        for row in range(rows):
            x_base = side * (13 + row * 5)
            y = start_y
            while y > end_y:
                x = x_base + rng.uniform(-1.5, 1.5)
                h = rng.uniform(6, 10)
                r = rng.uniform(0.3, 0.5)
                create_cylinder(f"TreeTrunk_{idx}", r, h, loc=(x, y, h / 2), mat=trunk_mat, verts=12)
                bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=r * 4.2, location=(x, y, h + r * 2.2))
                crown = bpy.context.object
                crown.name = f"TreeCrown_{idx}"
                apply_mat(crown, leaf_mat)
                idx += 1
                y -= spacing + rng.uniform(-1.2, 1.2)


def create_auto_door(origin):
    frame_mat = mat_pbr("DoorFrame", COLORS["cyan"], 0.25, 0.85, emission=0.8)
    glass_mat = mat_glass("DoorGlass", (0.45, 0.75, 1.0, 0.5), 0.03)

    fw, fh = 8.0, 5.0
    create_box("DoorFrameTop", (fw, 0.35, 0.35), loc=(origin[0], origin[1], fh + 0.2), mat=frame_mat)
    create_box("DoorFrameL", (0.35, 0.35, fh), loc=(origin[0] - fw / 2, origin[1], fh / 2), mat=frame_mat)
    create_box("DoorFrameR", (0.35, 0.35, fh), loc=(origin[0] + fw / 2, origin[1], fh / 2), mat=frame_mat)

    panel_w = fw / 2 - 0.3
    panel_h = fh - 0.3
    l_panel = create_box("DoorLeft", (panel_w, 0.12, panel_h), loc=(origin[0] - panel_w / 2, origin[1], panel_h / 2), mat=glass_mat)
    r_panel = create_box("DoorRight", (panel_w, 0.12, panel_h), loc=(origin[0] + panel_w / 2, origin[1], panel_h / 2), mat=glass_mat)

    for panel, sign in ((l_panel, -1), (r_panel, 1)):
        panel.keyframe_insert(data_path="location", frame=1)
        panel.location.x = origin[0] + sign * fw * 0.62
        panel.keyframe_insert(data_path="location", frame=80)


def create_entrance_hall(center, radius=15, height=12):
    floor = create_cylinder("HallFloor", radius, 0.35, loc=(center[0], center[1], 0.17), mat=mat_pbr("HallFloorMat", COLORS["white"], 0.3, 0.2), verts=48)
    create_torus("HallRing", radius * 0.82, 0.12, loc=(center[0], center[1], 0.42), mat=mat_neon("HallRingMat", COLORS["cyan"], 14))

    wall_mat = mat_pbr("HallWall", (0.92, 0.93, 0.97, 1), 0.45, 0.15)
    segments = 20
    open_angle = 35
    for i in range(segments):
        angle = (360 / segments) * i
        if -open_angle <= ((angle + 180) % 360 - 180) <= open_angle:
            continue
        rad = math.radians(angle)
        x = center[0] + (radius - 0.5) * math.cos(rad)
        y = center[1] + (radius - 0.5) * math.sin(rad)
        create_box(f"HallWall_{i}", (3.2, 0.5, height), loc=(x, y, height / 2), rot=(0, 0, rad), mat=wall_mat)

    dome = mat_glass("HallDome", (0.7, 0.9, 1.0, 0.3), 0.03)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius * 0.95, location=(center[0], center[1], height))
    d = bpy.context.object
    d.name = "HallDome"
    d.scale = (1, 1, 0.55)
    apply_mat(d, dome)


def create_spiral_stairs(center, height=6.0, radius=4.2, steps=34):
    step_mat = mat_pbr("StepMat", (0.85, 0.86, 0.9, 1), 0.35, 0.35)
    rise = height / steps
    ang_step = (2 * math.pi * 1.6) / steps

    for i in range(steps):
        a = i * ang_step
        x = center[0] + radius * math.cos(a)
        y = center[1] + radius * math.sin(a)
        z = 0.2 + i * rise
        create_box(f"Step_{i}", (2.6, 0.9, 0.16), loc=(x, y, z), rot=(0, 0, a), mat=step_mat)

    create_cylinder("StairCore", 0.36, height + 1.2, loc=(center[0], center[1], (height + 1.2) / 2), mat=mat_neon("StairCoreMat", COLORS["purple"], 10), verts=24)


def create_room(name, center, width=34, depth=30, height=9):
    floor_mat = mat_pbr(f"{name}_FloorMat", (0.86, 0.88, 0.93, 1), 0.35, 0.1)
    wall_mat = mat_pbr(f"{name}_WallMat", (0.92, 0.93, 0.97, 1), 0.5, 0.15)
    ceil_mat = mat_pbr(f"{name}_CeilMat", (0.88, 0.9, 0.95, 1), 0.45, 0.2, emission=0.7)

    create_plane(f"{name}_Floor", width, depth, loc=(center[0], center[1], center[2]), mat=floor_mat)
    create_plane(f"{name}_Ceiling", width, depth, loc=(center[0], center[1], center[2] + height), mat=ceil_mat)

    hw, hd, hh = width / 2, depth / 2, height / 2
    create_box(f"{name}_N", (width, 0.5, height), loc=(center[0], center[1] + hd, center[2] + hh), mat=wall_mat)
    create_box(f"{name}_S", (width, 0.5, height), loc=(center[0], center[1] - hd, center[2] + hh), mat=wall_mat)
    create_box(f"{name}_E", (0.5, depth, height), loc=(center[0] + hw, center[1], center[2] + hh), mat=wall_mat)
    create_box(f"{name}_W", (0.5, depth, height), loc=(center[0] - hw, center[1], center[2] + hh), mat=wall_mat)

    edge_mat = mat_neon(f"{name}_Edge", COLORS["cyan"], 12)
    for i, (ex, ey) in enumerate(((hw, hd), (hw, -hd), (-hw, hd), (-hw, -hd))):
        create_cylinder(f"{name}_Edge_{i}", 0.1, height, loc=(center[0] + ex, center[1] + ey, center[2] + hh), mat=edge_mat, verts=12)


def create_portal(name, loc):
    ring1 = create_torus(f"{name}_R1", 2.8, 0.16, loc=loc, rot=(math.radians(90), 0, 0), mat=mat_neon(f"{name}_R1M", COLORS["purple"], 20))
    ring2 = create_torus(f"{name}_R2", 2.3, 0.12, loc=loc, rot=(math.radians(90), 0, 0), mat=mat_neon(f"{name}_R2M", COLORS["cyan"], 15))
    for idx, r in enumerate((ring1, ring2)):
        r.keyframe_insert(data_path="rotation_euler", frame=1)
        r.rotation_euler.z += math.radians(360 * (1 if idx == 0 else -1))
        r.keyframe_insert(data_path="rotation_euler", frame=180)


def create_light_bridge(name, start, end, width=5):
    v = Vector(end) - Vector(start)
    length = v.length
    mid = (Vector(start) + Vector(end)) / 2
    angle = math.atan2(v.y, v.x)

    create_plane(name, length, width, loc=(mid.x, mid.y, start[2] + 0.08), rot=(0, 0, angle), mat=mat_glass(f"{name}_Surf", (0.45, 0.8, 1.0, 0.35), 0.1))
    for side, col in ((1, COLORS["cyan"]), (-1, COLORS["magenta"])):
        offset = side * (width / 2 + 0.15)
        px = -math.sin(angle) * offset
        py = math.cos(angle) * offset
        create_plane(f"{name}_Edge_{side}", length, 0.22, loc=(mid.x + px, mid.y + py, start[2] + 0.12), rot=(0, 0, angle), mat=mat_neon(f"{name}_EdgeMat_{side}", col, 15))


# =========================
# Camera / Light / Render
# =========================
def setup_lighting(target):
    bpy.ops.object.light_add(type='SUN', location=(50, 20, 80))
    sun = bpy.context.object
    sun.name = "KeySun"
    sun.data.energy = 2.2
    sun.data.color = (1.0, 0.95, 0.9)
    sun.rotation_euler = (math.radians(55), 0, math.radians(25))

    bpy.ops.object.light_add(type='AREA', location=(target[0], target[1] + 25, target[2] + 25))
    area = bpy.context.object
    area.name = "FillArea"
    area.data.energy = 1000
    area.data.size = 35

    for i, (offset, col) in enumerate((((30, 0, 15), COLORS["cyan"]), ((-30, 0, 15), COLORS["magenta"]))):
        bpy.ops.object.light_add(type='POINT', location=(target[0] + offset[0], target[1] + offset[1], target[2] + offset[2]))
        p = bpy.context.object
        p.name = f"Accent_{i}"
        p.data.energy = 450
        p.data.color = (col[0], col[1], col[2])


def setup_camera(target):
    loc = (target[0] + 26, target[1] + 56, target[2] + 30)
    bpy.ops.object.camera_add(location=loc)
    cam = bpy.context.object
    cam.name = "CinematicCamera"
    direction = Vector(target) - Vector(loc)
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

    cam.data.lens = 50
    cam.data.sensor_width = 36
    cam.data.dof.use_dof = True
    cam.data.dof.focus_distance = 60
    cam.data.dof.aperture_fstop = 2.8

    bpy.context.scene.camera = cam


def setup_render():
    scene = bpy.context.scene
    try:
        scene.render.engine = 'BLENDER_EEVEE_NEXT'
    except Exception:
        scene.render.engine = 'BLENDER_EEVEE'

    try:
        eevee = scene.eevee
        eevee.use_bloom = True
        eevee.bloom_intensity = 0.18
        eevee.use_gtao = True
        eevee.use_ssr = True
        eevee.taa_render_samples = 32
    except Exception:
        pass

    scene.view_settings.view_transform = 'Filmic'
    scene.view_settings.look = 'High Contrast'
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 100
    scene.render.fps = 30
    scene.frame_end = 240


# =========================
# Main pipeline
# =========================
def build_scene():
    clear_scene()
    setup_world()

    create_star_field()
    create_forest()
    create_ground_and_path()

    create_auto_door(LAYOUT["auto_door"])
    create_entrance_hall(LAYOUT["entrance_hall"])
    create_spiral_stairs(LAYOUT["stair_top"])

    rooms = [
        ("Motivation", LAYOUT["motivation_room"], 34, 30, 9),
        ("Theory", LAYOUT["theory_room"], 34, 30, 9),
        ("Programming", LAYOUT["programming_room"], 34, 30, 9),
        ("Formula", LAYOUT["formula_room"], 34, 30, 9),
        ("Simulation", LAYOUT["simulation_center"], 68, 52, 12),
        ("Conclusion", LAYOUT["conclusion_room"], 34, 30, 9),
        ("Future", LAYOUT["future_room"], 34, 30, 9),
    ]
    for n, c, w, d, h in rooms:
        create_room(n, c, w, d, h)

    create_portal("Portal_Motiv", (LAYOUT["motivation_room"][0], LAYOUT["motivation_room"][1] - 14, LAYOUT["motivation_room"][2] + 3.5))
    create_portal("Portal_Prog", (LAYOUT["programming_room"][0], LAYOUT["programming_room"][1] - 14, LAYOUT["programming_room"][2] + 3.5))
    create_portal("Portal_Sim", (LAYOUT["simulation_center"][0], LAYOUT["simulation_center"][1] - 24, LAYOUT["simulation_center"][2] + 4.5))

    create_light_bridge(
        "Bridge_Theory_Prog",
        (LAYOUT["theory_room"][0], LAYOUT["theory_room"][1] - 16, LAYOUT["theory_room"][2]),
        (LAYOUT["programming_room"][0], LAYOUT["programming_room"][1] + 16, LAYOUT["programming_room"][2]),
    )
    create_light_bridge(
        "Bridge_Formula_Sim",
        (LAYOUT["formula_room"][0], LAYOUT["formula_room"][1] - 16, LAYOUT["formula_room"][2]),
        (LAYOUT["simulation_center"][0], LAYOUT["simulation_center"][1] + 28, LAYOUT["simulation_center"][2]),
    )
    create_light_bridge(
        "Bridge_Conclusion_Future",
        (LAYOUT["conclusion_room"][0], LAYOUT["conclusion_room"][1] - 16, LAYOUT["conclusion_room"][2]),
        (LAYOUT["future_room"][0], LAYOUT["future_room"][1] + 16, LAYOUT["future_room"][2]),
    )

    setup_lighting(LAYOUT["entrance_hall"])
    setup_camera(LAYOUT["entrance_hall"])
    setup_render()


def export_glb(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=path,
        export_format='GLB',
        export_yup=True,
        export_animations=True,
        export_apply=True,
        export_lights=True,
        export_materials='EXPORT',
        export_colors=True,
        export_attributes=True,
        export_extras=True,
    )


def main():
    print("🚀 Building scene for Blender 5.0.1...")
    build_scene()
    print(f"📦 Exporting GLB -> {EXPORT_PATH}")
    export_glb(EXPORT_PATH)
    print("✅ Done")


if __name__ == "__main__":
    main()
