import bpy, os, tempfile, random, math
from mathutils import Vector, Euler

# ============================================
# 配置
# ============================================
EXPORT_NAME = "ultimate_lab.glb"
blend_dir = bpy.path.abspath("//")
if blend_dir and os.path.isdir(blend_dir):
    EXPORT_PATH = os.path.join(blend_dir, EXPORT_NAME)
else:
    EXPORT_PATH = os.path.join(tempfile.gettempdir(), EXPORT_NAME)

# 房間佈局
LAYOUT = {
    "outdoor": (0, 0, 0),
    "auto_door": (0, -35, 0),
    "entrance_hall": (0, -45, 0),
    "stair_end": (0, -50, 6),
    "motivation_room": (0, -65, 6),
    "theory_room": (0, -85, 6),
    "programming_room": (0, -105, 6),
    "formula_room": (0, -125, 6),
    "simulation_center": (0, -155, 6),
    "conclusion_room": (0, -185, 6),
    "future_room": (0, -205, 6),
}

# 顏色主題
COLORS = {
    "cyan": (0.0, 0.83, 1.0, 1.0),
    "magenta": (1.0, 0.0, 0.5, 1.0),
    "purple": (0.5, 0.0, 1.0, 1.0),
    "white": (0.95, 0.95, 1.0, 1.0),
    "dark": (0.05, 0.05, 0.15, 1.0),
}

# ============================================
# 場景清理
# ============================================
def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False, confirm=False)
    for collection in [bpy.data.meshes, bpy.data.materials, bpy.data.images]:
        for item in list(collection):
            try:
                if hasattr(item, "users") and item.users == 0:
                    collection.remove(item)
            except:
                pass


# ============================================
# 材質系統（Blender 5.0.1 相容）
# ============================================
_mat_cache = {}


def mat_pbr(name, color=(0.9, 0.9, 0.9, 1.0), rough=0.5, metallic=0.0, emit_strength=0.0):
    """PBR 材質生成器 - Blender 5.0+ 相容"""
    key = (
        name,
        tuple([round(c, 3) for c in color]),
        round(rough, 3),
        round(metallic, 3),
        round(emit_strength, 3),
    )
    if key in _mat_cache:
        return _mat_cache[key]

    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    # 輸出節點
    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (300, 0)

    # Principled BSDF
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (0, 0)

    # 設置參數（Blender 5.0+ 使用新的輸入名稱）
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metallic

    # Emission（5.0+ 版本）
    if emit_strength > 0:
        try:
            # Blender 5.0+ 使用 "Emission Color" 和 "Emission Strength"
            bsdf.inputs["Emission Color"].default_value = color
            bsdf.inputs["Emission Strength"].default_value = emit_strength
        except KeyError:
            # 舊版本回退
            try:
                bsdf.inputs["Emission"].default_value = color
                bsdf.inputs["Emission Strength"].default_value = emit_strength
            except:
                pass

    links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

    _mat_cache[key] = mat
    return mat


def mat_emissive(name, color=(0.8, 0.9, 1.0, 1.0), strength=5.0):
    """純發光材質（用於星星、燈光等）"""
    key = ("emit_" + name, tuple([round(c, 3) for c in color]), round(strength, 3))
    if key in _mat_cache:
        return _mat_cache[key]

    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (200, 0)

    emission = nodes.new("ShaderNodeEmission")
    emission.location = (0, 0)
    emission.inputs["Color"].default_value = color
    emission.inputs["Strength"].default_value = strength

    links.new(emission.outputs["Emission"], output.inputs["Surface"])

    _mat_cache[key] = mat
    return mat


def mat_glass(name, color=(0.8, 0.9, 1.0, 1.0), ior=1.45):
    """玻璃材質"""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    output = nodes.new("ShaderNodeOutputMaterial")
    glass = nodes.new("ShaderNodeBsdfGlass")
    glass.inputs["Color"].default_value = color
    glass.inputs["IOR"].default_value = ior

    links.new(glass.outputs["BSDF"], output.inputs["Surface"])
    return mat


# ============================================
# 幾何生成工具
# ============================================
def create_box(name, size, loc=(0, 0, 0), rot=(0, 0, 0), mat=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    obj.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    if mat:
        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)
    return obj


def create_cylinder(name, r, h, loc=(0, 0, 0), rot=(0, 0, 0), mat=None, verts=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=h, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    if mat:
        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)
    return obj


def create_plane(name, sx, sy, loc=(0, 0, 0), rot=(0, 0, 0), mat=None):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    obj.scale = (sx / 2, sy / 2, 1)
    if mat:
        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)
    return obj


def create_torus(name, major_r, minor_r, loc=(0, 0, 0), rot=(0, 0, 0), mat=None):
    bpy.ops.mesh.primitive_torus_add(major_radius=major_r, minor_radius=minor_r, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    if mat:
        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)
    return obj


# ============================================
# 環境系統
# ============================================
def setup_world():
    """設置夜晚世界"""
    try:
        world = bpy.data.worlds["World"]
    except:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world

    world.use_nodes = True
    nodes = world.node_tree.nodes
    links = world.node_tree.links
    nodes.clear()

    output = nodes.new("ShaderNodeOutputWorld")
    bg = nodes.new("ShaderNodeBackground")
    bg.inputs["Color"].default_value = (0.01, 0.02, 0.08, 1.0)
    bg.inputs["Strength"].default_value = 0.3

    links.new(bg.outputs["Background"], output.inputs["Surface"])


def create_star_field(count=400, radius=280.0):
    """生成星空（使用純發光材質）"""
    star_mat = mat_emissive("Star", color=(1.0, 1.0, 1.0, 1.0), strength=10.0)

    rand = random.Random(42)
    for i in range(count):
        theta = rand.uniform(0, math.pi * 0.5)
        phi = rand.uniform(0, 2 * math.pi)

        x = radius * math.sin(theta) * math.cos(phi)
        y = radius * math.sin(theta) * math.sin(phi)
        z = radius * math.cos(theta)

        size = rand.uniform(0.08, 0.2)
        create_cylinder(
            f"Star_{i}",
            size,
            size * 3,
            loc=(x, y, z),
            rot=(rand.random(), rand.random(), rand.random()),
            mat=star_mat,
            verts=6,
        )


def create_ground_and_path():
    """地面和步道"""
    # 主地面
    ground_mat = mat_pbr("Ground", color=(0.05, 0.06, 0.08, 1.0), rough=0.9)
    create_plane("Ground", 800, 800, loc=(0, 0, -0.1), mat=ground_mat)

    # 步道
    path_length = abs(LAYOUT["entrance_hall"][1] - LAYOUT["outdoor"][1]) + 30
    path_center_y = (LAYOUT["outdoor"][1] + LAYOUT["entrance_hall"][1]) / 2

    path_mat = mat_pbr("Path", color=(0.2, 0.22, 0.25, 1.0), rough=0.7, metallic=0.1)
    create_plane("Walkway", 8, path_length, loc=(0, path_center_y, 0), mat=path_mat)

    # 發光邊緣
    edge_mat = mat_pbr("EdgeGlow", color=COLORS["cyan"], emit_strength=5.0)
    create_plane("EdgeL", 0.3, path_length, loc=(4.2, path_center_y, 0.02), mat=edge_mat)
    create_plane("EdgeR", 0.3, path_length, loc=(-4.2, path_center_y, 0.02), mat=edge_mat)

    # 發光粒子線
    particle_mat = mat_emissive("Particle", color=COLORS["purple"], strength=8.0)
    for i in range(int(path_length / 3)):
        y_pos = LAYOUT["outdoor"][1] - i * 3
        create_cylinder(
            f"Particle_{i}",
            0.15,
            0.3,
            loc=(random.uniform(-3, 3), y_pos, 0.2),
            mat=particle_mat,
            verts=8,
        )


# ============================================
# 森林系統
# ============================================
def create_tree(x, y, seed=0):
    """生成單棵樹"""
    rand = random.Random(seed)

    # 樹幹
    trunk_h = rand.uniform(6.0, 10.0)
    trunk_r = rand.uniform(0.3, 0.6)
    trunk_mat = mat_pbr("Trunk", color=(0.15, 0.1, 0.08, 1.0), rough=0.9)
    trunk = create_cylinder("Trunk", trunk_r, trunk_h, loc=(x, y, trunk_h / 2), mat=trunk_mat, verts=12)

    # 樹冠
    crown_mat = mat_pbr("Crown", color=(0.05, 0.3, 0.1, 1.0), rough=0.8, emit_strength=0.3)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=trunk_r * 4, location=(x, y, trunk_h + trunk_r * 2.5))
    crown = bpy.context.object
    crown.data.materials.append(crown_mat)

    # 合併
    bpy.ops.object.select_all(action='DESELECT')
    trunk.select_set(True)
    crown.select_set(True)
    bpy.context.view_layer.objects.active = trunk
    bpy.ops.object.join()

    return bpy.context.object


def create_forest():
    """生成密集森林"""
    path_start = LAYOUT["outdoor"][1] + 10
    path_end = LAYOUT["entrance_hall"][1] - 10
    path_length = abs(path_end - path_start)

    # 左側森林（3排）
    for row in range(3):
        x_base = -12 - row * 5
        for i in range(int(path_length / 5)):
            y = path_start - i * 5 + random.uniform(-2, 2)
            x = x_base + random.uniform(-2, 2)
            create_tree(x, y, seed=row * 100 + i)

    # 右側森林（3排）
    for row in range(3):
        x_base = 12 + row * 5
        for i in range(int(path_length / 5)):
            y = path_start - i * 5 + random.uniform(-2, 2)
            x = x_base + random.uniform(-2, 2)
            create_tree(x, y, seed=1000 + row * 100 + i)


# ============================================
# 建築系統
# ============================================
def create_auto_door(origin):
    """自動滑門"""
    # 門框
    frame_mat = mat_pbr("DoorFrame", color=COLORS["cyan"], metallic=0.8, emit_strength=3.0)
    frame_w, frame_h = 8.0, 5.0

    create_box("DoorFrameTop", (frame_w, 0.3, 0.3), loc=(origin[0], origin[1], frame_h), mat=frame_mat)
    create_box("DoorFrameL", (0.3, 0.3, frame_h), loc=(origin[0] - frame_w / 2, origin[1], frame_h / 2), mat=frame_mat)
    create_box("DoorFrameR", (0.3, 0.3, frame_h), loc=(origin[0] + frame_w / 2, origin[1], frame_h / 2), mat=frame_mat)

    # 門板
    panel_mat = mat_glass("DoorPanel", color=(0.5, 0.7, 1.0, 1.0))
    panel_w = frame_w / 2 - 0.2
    panel_h = frame_h - 0.3

    left_panel = create_box(
        "DoorLeft",
        (panel_w, 0.1, panel_h),
        loc=(origin[0] - panel_w / 2, origin[1], panel_h / 2),
        mat=panel_mat,
    )
    right_panel = create_box(
        "DoorRight",
        (panel_w, 0.1, panel_h),
        loc=(origin[0] + panel_w / 2, origin[1], panel_h / 2),
        mat=panel_mat,
    )

    # 開門動畫
    for panel, direction in [(left_panel, -1), (right_panel, 1)]:
        panel.keyframe_insert(data_path="location", frame=1)
        panel.location.x = origin[0] + direction * frame_w * 0.6
        panel.keyframe_insert(data_path="location", frame=60)


def create_entrance_hall(center, radius=15.0, height=12.0):
    """圓形入口大廳（含穹頂）"""
    # 地板
    floor_mat = mat_pbr("HallFloor", color=(0.9, 0.9, 0.95, 1.0), rough=0.3, metallic=0.1)
    create_cylinder("HallFloor", radius, 0.3, loc=(center[0], center[1], 0.15), mat=floor_mat, verts=32)

    # 穹頂（新增）
    dome_mat = mat_pbr("Dome", color=(0.85, 0.90, 0.95, 1.0), rough=0.3, metallic=0.2, emit_strength=0.5)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=(center[0], center[1], height))
    dome = bpy.context.object
    dome.name = "Dome"
    dome.scale = (1, 1, 0.5)  # 壓扁成穹頂
    dome.data.materials.append(dome_mat)

    # 只保留上半球
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.bisect(plane_co=(center[0], center[1], height), plane_no=(0, 0, 1), clear_inner=True)
    bpy.ops.object.mode_set(mode='OBJECT')

    # 發光圓環
    ring_mat = mat_emissive("HallRing", color=COLORS["cyan"], strength=8.0)
    create_torus("HallRing", radius - 0.5, 0.2, loc=(center[0], center[1], 0.3), mat=ring_mat)

    # 牆面
    wall_mat = mat_pbr("HallWall", color=COLORS["white"], rough=0.5, metallic=0.1)
    segments = 16
    gap_angle = 30.0

    for i in range(segments):
        angle = (360.0 / segments) * i
        if -gap_angle <= ((angle + 180) % 360 - 180) <= gap_angle:
            continue

        rad = math.radians(angle)
        x = center[0] + (radius - 0.6) * math.cos(rad)
        y = center[1] + (radius - 0.6) * math.sin(rad)

        create_box(f"HallWall_{i}", (3.0, 0.5, height), loc=(x, y, height / 2), rot=(0, 0, rad), mat=wall_mat)

    # 中央全息
    holo_mat = mat_emissive("Hologram", color=COLORS["cyan"], strength=6.0)
    create_torus(
        "CentralHolo",
        2.0,
        0.1,
        loc=(center[0], center[1], height / 2),
        rot=(math.radians(90), 0, 0),
        mat=holo_mat,
    )


def create_spiral_staircase(center, height=6.0, radius=4.0, steps=32):
    """螺旋樓梯"""
    step_mat = mat_pbr("StairStep", color=(0.85, 0.85, 0.9, 1.0), rough=0.4, metallic=0.3)

    h_step = height / steps
    angle_step = (2 * math.pi * 1.5) / steps

    for i in range(steps):
        angle = i * angle_step
        x = center[0] + radius * math.cos(angle)
        y = center[1] + radius * math.sin(angle)
        z = 0.2 + i * h_step

        create_box(f"Step_{i}", (2.5, 0.8, 0.15), loc=(x, y, z), rot=(0, 0, angle), mat=step_mat)

    # 中央柱
    pillar_mat = mat_emissive("Pillar", color=COLORS["cyan"], strength=2.0)
    create_cylinder("StairPillar", 0.3, height + 0.5, loc=(center[0], center[1], (height + 0.5) / 2), mat=pillar_mat, verts=16)


def create_lab_room(name, center, width=32, depth=28, height=8):
    """實驗室房間（含屋頂）"""
    floor_mat = mat_pbr(f"{name}_Floor", color=COLORS["white"], rough=0.4, metallic=0.05)
    wall_mat = mat_pbr(f"{name}_Wall", color=(0.92, 0.92, 0.95, 1.0), rough=0.6)
    ceiling_mat = mat_pbr(
        f"{name}_Ceiling",
        color=(0.88, 0.88, 0.92, 1.0),
        rough=0.5,
        emit_strength=1.0,
    )

    # 地板
    create_plane(f"{name}_Floor", width, depth, loc=(center[0], center[1], center[2]), mat=floor_mat)

    # 天花板（新增）
    create_plane(
        f"{name}_Ceiling",
        width,
        depth,
        loc=(center[0], center[1], center[2] + height),
        mat=ceiling_mat,
    )

    # 四面牆
    hw, hd, hh = width / 2, depth / 2, height / 2
    create_box(
        f"{name}_North",
        (width, 0.4, height),
        loc=(center[0], center[1] + hd, center[2] + hh),
        mat=wall_mat,
    )
    create_box(
        f"{name}_South",
        (width, 0.4, height),
        loc=(center[0], center[1] - hd, center[2] + hh),
        mat=wall_mat,
    )
    create_box(
        f"{name}_East",
        (0.4, depth, height),
        loc=(center[0] + hw, center[1], center[2] + hh),
        mat=wall_mat,
    )
    create_box(
        f"{name}_West",
        (0.4, depth, height),
        loc=(center[0] - hw, center[1], center[2] + hh),
        mat=wall_mat,
    )

    # 發光邊線
    edge_mat = mat_emissive(f"{name}_Edge", color=COLORS["cyan"], strength=4.0)
    corners = [(hw, hd), (hw, -hd), (-hw, hd), (-hw, -hd)]
    for i, (ex, ey) in enumerate(corners):
        create_cylinder(
            f"{name}_EdgeLight_{i}",
            0.1,
            height,
            loc=(center[0] + ex, center[1] + ey, center[2] + hh),
            mat=edge_mat,
            verts=8,
        )


def create_portal(name, loc, target_name=""):
    """傳送門"""
    # 外環
    outer_mat = mat_emissive("PortalOuter", color=COLORS["purple"], strength=10.0)
    create_torus(f"{name}_Outer", 2.5, 0.15, loc=loc, rot=(math.radians(90), 0, 0), mat=outer_mat)

    # 內環
    inner_mat = mat_emissive("PortalInner", color=COLORS["cyan"], strength=8.0)
    create_torus(f"{name}_Inner", 2.0, 0.1, loc=loc, rot=(math.radians(90), 0, 0), mat=inner_mat)


def create_light_bridge(name, start, end, width=4.0):
    """發光橋"""
    vec = Vector(end) - Vector(start)
    length = vec.length
    mid = (Vector(start) + Vector(end)) / 2
    angle = math.atan2(vec.y, vec.x)

    bridge_mat = mat_pbr("Bridge", color=COLORS["cyan"], emit_strength=6.0)
    create_plane(name, length, width, loc=(mid.x, mid.y, start[2] + 0.05), rot=(0, 0, angle), mat=bridge_mat)


# ============================================
# 相機與燈光
# ============================================
def setup_camera_and_lighting(target=(0, 0, 3)):
    """設置相機和燈光"""
    # 相機
    cam_loc = (target[0] + 25, target[1] + 30, target[2] + 20)
    bpy.ops.object.camera_add(location=cam_loc)
    cam = bpy.context.object

    direction = Vector(target) - Vector(cam_loc)
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

    bpy.context.scene.camera = cam

    # 主光源
    bpy.ops.object.light_add(type='SUN', location=(20, 20, 40))
    sun = bpy.context.object
    sun.data.energy = 1.5


# ============================================
# 主建構函數
# ============================================
def build_ultimate_lab():
    """建構完整場景"""
    print("🚀 開始建構...")

    clear_scene()
    setup_world()

    print("🌌 星空...")
    create_star_field(400, 280.0)

    print("🌲 森林...")
    create_forest()

    print("🛤️  步道...")
    create_ground_and_path()

    print("🚪 自動門...")
    create_auto_door(LAYOUT["auto_door"])

    print("🏛️  入口大廳...")
    create_entrance_hall(LAYOUT["entrance_hall"])

    print("🌀 螺旋樓梯...")
    create_spiral_staircase(LAYOUT["stair_end"])

    # 房間
    rooms = [
        ("Motivation", LAYOUT["motivation_room"], 32, 28, 8),
        ("Theory", LAYOUT["theory_room"], 32, 28, 8),
        ("Programming", LAYOUT["programming_room"], 32, 28, 8),
        ("Formula", LAYOUT["formula_room"], 32, 28, 8),
        ("Simulation", LAYOUT["simulation_center"], 64, 48, 10),
        ("Conclusion", LAYOUT["conclusion_room"], 32, 28, 8),
        ("Future", LAYOUT["future_room"], 32, 28, 8),
    ]

    for room_name, center, w, d, h in rooms:
        print(f"🏢 {room_name}...")
        create_lab_room(room_name, center, w, d, h)

    # 連接
    print("🌀 傳送門...")
    create_portal(
        "Portal1",
        (
            LAYOUT["motivation_room"][0],
            LAYOUT["motivation_room"][1] - 12,
            LAYOUT["motivation_room"][2] + 3,
        ),
    )
    create_portal(
        "Portal2",
        (
            LAYOUT["programming_room"][0],
            LAYOUT["programming_room"][1] - 12,
            LAYOUT["programming_room"][2] + 3,
        ),
    )
    create_portal(
        "Portal3",
        (
            LAYOUT["simulation_center"][0],
            LAYOUT["simulation_center"][1] - 22,
            LAYOUT["simulation_center"][2] + 4,
        ),
    )

    print("🌉 光橋...")
    create_light_bridge(
        "Bridge1",
        (
            LAYOUT["theory_room"][0],
            LAYOUT["theory_room"][1] - 14,
            LAYOUT["theory_room"][2],
        ),
        (
            LAYOUT["programming_room"][0],
            LAYOUT["programming_room"][1] + 14,
            LAYOUT["programming_room"][2],
        ),
    )
    create_light_bridge(
        "Bridge2",
        (
            LAYOUT["formula_room"][0],
            LAYOUT["formula_room"][1] - 14,
            LAYOUT["formula_room"][2],
        ),
        (
            LAYOUT["simulation_center"][0],
            LAYOUT["simulation_center"][1] + 24,
            LAYOUT["simulation_center"][2],
        ),
    )
    create_light_bridge(
        "Bridge3",
        (
            LAYOUT["conclusion_room"][0],
            LAYOUT["conclusion_room"][1] - 14,
            LAYOUT["conclusion_room"][2],
        ),
        (
            LAYOUT["future_room"][0],
            LAYOUT["future_room"][1] + 14,
            LAYOUT["future_room"][2],
        ),
    )

    print("📷 相機...")
    setup_camera_and_lighting(LAYOUT["entrance_hall"])

    # 渲染設置
    bpy.context.scene.render.engine = 'BLENDER_EEVEE_NEXT'  # Blender 5.0 使用 EEVEE_NEXT
    try:
        bpy.context.scene.eevee.use_bloom = True
    except:
        pass

    print("✅ 完成！")


# ============================================
# 匯出
# ============================================
def export_glb(path):
    """匯出 GLB"""
    try:
        bpy.ops.export_scene.gltf(
            filepath=path,
            export_format='GLB',
            export_yup=True,
            export_animations=True,
            export_apply=True,
        )
        return True
    except Exception as e:
        print(f"❌ 匯出失敗: {e}")
        return False


# ============================================
# 執行
# ============================================
def main():
    build_ultimate_lab()

    success = export_glb(EXPORT_PATH)
    if success:
        print(f"🎉 成功匯出到: {EXPORT_PATH}")
    else:
        print("❌ 匯出失敗")


if __name__ == "__main__":
    main()
