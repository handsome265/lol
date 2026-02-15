import bpy, os, tempfile, random, math
from mathutils import Vector, Euler, Color

# ============================================
# 配置
# ============================================
EXPORT_NAME = "ultimate_lab_pro.glb"

# 自動存到桌面（跨平台）
import os
desktop = os.path.join(os.path.expanduser("~"), "Desktop")
EXPORT_PATH = os.path.join(desktop, EXPORT_NAME)

print(f"📍 GLB 將儲存到: {EXPORT_PATH}")

# 房間佈局（優化過的線性動線）
LAYOUT = {
    "outdoor": (0, 0, 0),
    "pathway_mid": (0, -20, 0),
    "auto_door": (0, -38, 0),
    "entrance_hall": (0, -48, 0),
    "stair_bottom": (0, -52, 0),
    "stair_top": (0, -52, 6),
    "corridor_1": (0, -68, 6),
    "motivation_room": (0, -85, 6),
    "corridor_2": (0, -102, 6),
    "theory_room": (0, -119, 6),
    "corridor_3": (0, -136, 6),
    "programming_room": (0, -153, 6),
    "corridor_4": (0, -170, 6),
    "formula_room": (0, -187, 6),
    "corridor_5": (0, -210, 6),
    "simulation_center": (0, -245, 6),
    "corridor_6": (0, -280, 6),
    "conclusion_room": (0, -297, 6),
    "corridor_7": (0, -314, 6),
    "future_room": (0, -331, 6)
}

# 顏色主題（更鮮豔）
COLORS = {
    "cyan": (0.0, 0.9, 1.0, 1.0),
    "magenta": (1.0, 0.1, 0.6, 1.0),
    "purple": (0.6, 0.1, 1.0, 1.0),
    "blue": (0.1, 0.5, 1.0, 1.0),
    "green": (0.0, 1.0, 0.6, 1.0),
    "orange": (1.0, 0.5, 0.0, 1.0),
    "white": (0.98, 0.98, 1.0, 1.0),
    "dark": (0.03, 0.04, 0.08, 1.0)
}

# ============================================
# 場景清理
# ============================================
def clear_scene():
    """完全清空場景"""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False, confirm=False)

    # 清理所有數據塊
    for collection in [bpy.data.meshes, bpy.data.materials, bpy.data.images,
                       bpy.data.textures, bpy.data.lights, bpy.data.cameras]:
        for item in list(collection):
            try:
                if hasattr(item, "users") and item.users == 0:
                    collection.remove(item)
            except:
                pass

    print("✅ 場景已清空")

# ============================================
# 高級材質系統
# ============================================
_mat_cache = {}

def mat_chrome(name="Chrome"):
    """鉻金屬材質"""
    if name in _mat_cache:
        return _mat_cache[name]

    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    output = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")

    bsdf.inputs["Base Color"].default_value = (0.9, 0.9, 0.95, 1.0)
    bsdf.inputs["Metallic"].default_value = 1.0
    bsdf.inputs["Roughness"].default_value = 0.05

    try:
        bsdf.inputs["Emission Color"].default_value = (0.8, 0.9, 1.0, 1.0)
        bsdf.inputs["Emission Strength"].default_value = 0.2
    except:
        pass

    links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])
    _mat_cache[name] = mat
    return mat

def mat_hologram(name="Hologram", color=(0.0, 0.9, 1.0, 1.0), strength=15.0):
    """全息投影材質"""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    output = nodes.new("ShaderNodeOutputMaterial")

    # 混合 Emission 和 Transparent
    mix = nodes.new("ShaderNodeMixShader")
    emit = nodes.new("ShaderNodeEmission")
    trans = nodes.new("ShaderNodeBsdfTransparent")

    emit.inputs["Color"].default_value = color
    emit.inputs["Strength"].default_value = strength

    # Fresnel 效果
    fresnel = nodes.new("ShaderNodeFresnel")
    fresnel.inputs["IOR"].default_value = 1.45

    links.new(fresnel.outputs["Fac"], mix.inputs["Fac"])
    links.new(emit.outputs["Emission"], mix.inputs[2])
    links.new(trans.outputs["BSDF"], mix.inputs[1])
    links.new(mix.outputs["Shader"], output.inputs["Surface"])

    mat.blend_method = 'BLEND'
    return mat

def mat_neon(name="Neon", color=(0.0, 0.9, 1.0, 1.0), strength=20.0):
    """霓虹燈材質"""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    output = nodes.new("ShaderNodeOutputMaterial")
    emit = nodes.new("ShaderNodeEmission")

    emit.inputs["Color"].default_value = color
    emit.inputs["Strength"].default_value = strength

    links.new(emit.outputs["Emission"], output.inputs["Surface"])
    return mat

def mat_glass_tinted(name="GlassTinted", color=(0.5, 0.8, 1.0, 1.0), roughness=0.0):
    """彩色玻璃材質"""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    output = nodes.new("ShaderNodeOutputMaterial")
    glass = nodes.new("ShaderNodeBsdfGlass")

    glass.inputs["Color"].default_value = color
    glass.inputs["Roughness"].default_value = roughness
    glass.inputs["IOR"].default_value = 1.45

    links.new(glass.outputs["BSDF"], output.inputs["Surface"])
    mat.blend_method = 'BLEND'
    return mat

def mat_floor_metallic(name="FloorMetal"):
    """金屬地板材質"""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    output = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")

    bsdf.inputs["Base Color"].default_value = (0.15, 0.16, 0.2, 1.0)
    bsdf.inputs["Metallic"].default_value = 0.9
    bsdf.inputs["Roughness"].default_value = 0.3

    # 添加程序化紋理
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 50.0

    color_ramp = nodes.new("ShaderNodeValToRGB")
    color_ramp.color_ramp.elements[0].position = 0.45
    color_ramp.color_ramp.elements[1].position = 0.55

    links.new(noise.outputs["Fac"], color_ramp.inputs["Fac"])
    links.new(color_ramp.outputs["Color"], bsdf.inputs["Roughness"])
    links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

    return mat

def mat_wall_panels(name="WallPanel"):
    """科技感牆面材質"""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    output = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")

    bsdf.inputs["Base Color"].default_value = (0.92, 0.93, 0.96, 1.0)
    bsdf.inputs["Metallic"].default_value = 0.2
    bsdf.inputs["Roughness"].default_value = 0.4

    try:
        bsdf.inputs["Emission Color"].default_value = (0.9, 0.95, 1.0, 1.0)
        bsdf.inputs["Emission Strength"].default_value = 0.5
    except:
        pass

    # 添加 Voronoi 紋理模擬面板
    voronoi = nodes.new("ShaderNodeTexVoronoi")
    voronoi.inputs["Scale"].default_value = 5.0

    links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

    return mat

# ============================================
# 幾何生成工具（增強版）
# ============================================
def create_box(name, size, loc=(0,0,0), rot=(0,0,0), mat=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    obj.scale = (size[0]/2, size[1]/2, size[2]/2)

    # 添加斜角修改器
    bevel = obj.modifiers.new(type='BEVEL', name='Bevel')
    bevel.width = 0.02
    bevel.segments = 2

    if mat:
        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)

    obj.data.use_auto_smooth = True
    return obj

def create_cylinder(name, r, h, loc=(0,0,0), rot=(0,0,0), mat=None, verts=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=h, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name

    if mat:
        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)

    obj.data.use_auto_smooth = True
    return obj

def create_plane(name, sx, sy, loc=(0,0,0), rot=(0,0,0), mat=None):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    obj.scale = (sx/2, sy/2, 1)

    if mat:
        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)

    return obj

def create_torus(name, major_r, minor_r, loc=(0,0,0), rot=(0,0,0), mat=None):
    bpy.ops.mesh.primitive_torus_add(major_radius=major_r, minor_radius=minor_r, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name

    if mat:
        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)

    obj.data.use_auto_smooth = True
    return obj

def create_ico_sphere(name, r, subdivisions=2, loc=(0,0,0), mat=None):
    """創建更圓滑的球體"""
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdivisions, radius=r, location=loc)
    obj = bpy.context.object
    obj.name = name

    if mat:
        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)

    obj.data.use_auto_smooth = True
    return obj

# ============================================
# 環境系統（超強化）
# ============================================
def setup_world_advanced():
    """設置高級世界環境"""
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

    # 背景 + 星空混合
    mix = nodes.new("ShaderNodeMixShader")

    # 主背景（漸變）
    bg1 = nodes.new("ShaderNodeBackground")
    bg1.inputs["Color"].default_value = (0.01, 0.02, 0.06, 1.0)
    bg1.inputs["Strength"].default_value = 0.2

    # 星空背景
    bg2 = nodes.new("ShaderNodeBackground")
    bg2.inputs["Color"].default_value = (0.05, 0.08, 0.15, 1.0)
    bg2.inputs["Strength"].default_value = 0.5

    # 使用 Musgrave 紋理製造星雲效果
    musgrave = nodes.new("ShaderNodeTexMusgrave")
    musgrave.inputs["Scale"].default_value = 0.5

    links.new(musgrave.outputs["Fac"], mix.inputs["Fac"])
    links.new(bg1.outputs["Background"], mix.inputs[1])
    links.new(bg2.outputs["Background"], mix.inputs[2])
    links.new(mix.outputs["Shader"], output.inputs["Surface"])

    # 環境照明
    world.light_settings.use_ambient_occlusion = True

    print("✅ 高級世界環境設置完成")

def create_volumetric_atmosphere():
    """創建體積光效果"""
    # 創建大型立方體作為體積容器
    bpy.ops.mesh.primitive_cube_add(size=600, location=(0, -150, 150))
    vol_cube = bpy.context.object
    vol_cube.name = "VolumetricAtmosphere"

    # 創建體積材質
    mat = bpy.data.materials.new("VolumeMaterial")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    output = nodes.new("ShaderNodeOutputMaterial")
    volume = nodes.new("ShaderNodeVolumeScatter")

    volume.inputs["Density"].default_value = 0.001
    volume.inputs["Anisotropy"].default_value = 0.3

    links.new(volume.outputs["Volume"], output.inputs["Volume"])

    vol_cube.data.materials.append(mat)
    vol_cube.hide_render = False

    print("✅ 體積光效果已添加")

def create_advanced_star_field(count=800, radius=300.0):
    """高級星空系統"""
    # 創建多種大小的星星
    star_sizes = [
        (0.05, 0.1, 400, 12.0),   # 小星星
        (0.1, 0.2, 250, 15.0),    # 中星星
        (0.2, 0.4, 150, 20.0)     # 大星星
    ]

    rand = random.Random(42)
    star_index = 0

    for size_min, size_max, star_count, intensity in star_sizes:
        mat = mat_neon(f"Star_{size_min}", color=(1.0, 1.0, 1.0, 1.0), strength=intensity)

        for i in range(star_count):
            theta = rand.uniform(0, math.pi * 0.6)
            phi = rand.uniform(0, 2 * math.pi)

            x = radius * math.sin(theta) * math.cos(phi)
            y = radius * math.sin(theta) * math.sin(phi)
            z = radius * math.cos(theta)

            size = rand.uniform(size_min, size_max)

            # 創建星星（使用 Ico Sphere 更圓滑）
            star = create_ico_sphere(
                f"Star_{star_index}",
                size,
                subdivisions=1,
                loc=(x, y, z),
                mat=mat
            )

            # 添加微弱閃爍動畫
            if rand.random() < 0.3:
                star.scale = (1.0, 1.0, 1.0)
                star.keyframe_insert(data_path="scale", frame=1)
                star.scale = (rand.uniform(0.8, 1.2), rand.uniform(0.8, 1.2), rand.uniform(0.8, 1.2))
                star.keyframe_insert(data_path="scale", frame=rand.randint(40, 80))

            star_index += 1

    print(f"✅ 創建了 {star_index} 顆星星")

def create_nebula_particles():
    """創建星雲粒子效果"""
    rand = random.Random(123)

    nebula_colors = [
        (0.6, 0.1, 1.0, 1.0),  # 紫色
        (0.0, 0.7, 1.0, 1.0),  # 青色
        (1.0, 0.3, 0.6, 1.0)   # 粉紅
    ]

    for color_idx, color in enumerate(nebula_colors):
        mat = mat_hologram(f"Nebula_{color_idx}", color=color, strength=3.0)

        for i in range(50):
            theta = rand.uniform(0, math.pi * 0.5)
            phi = rand.uniform(0, 2 * math.pi)
            distance = rand.uniform(200, 280)

            x = distance * math.sin(theta) * math.cos(phi)
            y = distance * math.sin(theta) * math.sin(phi)
            z = distance * math.cos(theta)

            size = rand.uniform(2.0, 5.0)

            nebula = create_ico_sphere(
                f"Nebula_{color_idx}_{i}",
                size,
                subdivisions=2,
                loc=(x, y, z),
                mat=mat
            )

            nebula.scale = (rand.uniform(0.5, 1.5), rand.uniform(0.5, 1.5), rand.uniform(0.5, 1.5))

    print("✅ 星雲粒子創建完成")

def create_ground_and_path_pro():
    """專業級地面和步道"""
    # 主地面（金屬質感）
    ground_mat = mat_floor_metallic("GroundMetal")
    ground = create_plane("Ground", 900, 900, loc=(0, -150, -0.1), mat=ground_mat)

    # 步道（發光）
    path_start = LAYOUT["outdoor"][1]
    path_end = LAYOUT["entrance_hall"][1]
    path_length = abs(path_end - path_start) + 10
    path_center_y = (path_start + path_end) / 2

    # 主步道
    path_mat = mat_chrome("PathChrome")
    path = create_plane("Walkway", 10, path_length, loc=(0, path_center_y, 0.01), mat=path_mat)

    # 發光邊緣（更炫）
    edge_colors = [COLORS["cyan"], COLORS["magenta"]]
    for idx, color in enumerate(edge_colors):
        side = 1 if idx == 0 else -1
        edge_mat = mat_neon(f"PathEdge_{idx}", color=color, strength=25.0)

        # 多層邊緣
        create_plane(f"PathEdge_{idx}_1", 0.4, path_length,
                    loc=(side * 5.5, path_center_y, 0.03), mat=edge_mat)
        create_plane(f"PathEdge_{idx}_2", 0.2, path_length,
                    loc=(side * 5.8, path_center_y, 0.05), mat=edge_mat)

    # 發光粒子（更多更炫）
    particle_colors = [COLORS["purple"], COLORS["blue"], COLORS["cyan"]]

    for i in range(int(path_length / 2)):
        y_pos = path_start - i * 2
        color = random.choice(particle_colors)
        particle_mat = mat_neon(f"Particle_{i}", color=color, strength=18.0)

        x_offset = random.uniform(-4, 4)
        z_height = random.uniform(0.2, 1.5)

        particle = create_ico_sphere(
            f"PathParticle_{i}",
            random.uniform(0.1, 0.25),
            subdivisions=2,
            loc=(x_offset, y_pos, z_height),
            mat=particle_mat
        )

        # 添加浮動動畫
        particle.keyframe_insert(data_path="location", frame=1)
        particle.location.z += random.uniform(0.3, 0.8)
        particle.keyframe_insert(data_path="location", frame=random.randint(60, 120))

    print("✅ 專業級地面和步道創建完成")

# ============================================
# 森林系統（強化版）
# ============================================
def create_tree_advanced(x, y, seed=0):
    """高級樹木生成"""
    rand = random.Random(seed)

    trunk_h = rand.uniform(7.0, 12.0)
    trunk_r = rand.uniform(0.35, 0.7)

    # 樹幹（使用圓柱 + 輕微錐形）
    trunk_mat = mat_chrome(f"Trunk_{seed}")
    trunk = create_cylinder(
        f"Trunk_{seed}",
        trunk_r * 0.8,
        trunk_h,
        loc=(x, y, trunk_h/2),
        mat=trunk_mat,
        verts=16
    )
    trunk.scale.z = 1.1  # 輕微拉長

    # 樹冠（多層）
    crown_colors = [
        (0.05, 0.35, 0.1, 1.0),
        (0.08, 0.4, 0.15, 1.0),
        (0.1, 0.45, 0.2, 1.0)
    ]

    crowns = []
    for idx, color in enumerate(crown_colors):
        crown_mat = mat_hologram(f"Crown_{seed}_{idx}", color=color, strength=rand.uniform(2.0, 4.0))

        crown_size = trunk_r * (4.5 - idx * 0.5)
        crown_height = trunk_h + trunk_r * (2.5 + idx * 0.3)

        crown = create_ico_sphere(
            f"Crown_{seed}_{idx}",
            crown_size,
            subdivisions=2,
            loc=(x, y, crown_height),
            mat=crown_mat
        )

        crowns.append(crown)

    # 合併所有部分
    bpy.ops.object.select_all(action='DESELECT')
    trunk.select_set(True)
    for crown in crowns:
        crown.select_set(True)

    bpy.context.view_layer.objects.active = trunk
    bpy.ops.object.join()

    return bpy.context.object

def create_forest_advanced():
    """高級森林系統"""
    path_start = LAYOUT["outdoor"][1] + 12
    path_end = LAYOUT["entrance_hall"][1] - 8
    path_length = abs(path_end - path_start)

    tree_count = 0

    # 左側森林（4排）
    for row in range(4):
        x_base = -14 - row * 6
        trees_in_row = int(path_length / 4.5)

        for i in range(trees_in_row):
            y = path_start - i * 4.5 + random.uniform(-2.5, 2.5)
            x = x_base + random.uniform(-2, 2)

            create_tree_advanced(x, y, seed=tree_count)
            tree_count += 1

    # 右側森林（4排）
    for row in range(4):
        x_base = 14 + row * 6
        trees_in_row = int(path_length / 4.5)

        for i in range(trees_in_row):
            y = path_start - i * 4.5 + random.uniform(-2.5, 2.5)
            x = x_base + random.uniform(-2, 2)

            create_tree_advanced(x, y, seed=tree_count + 1000)
            tree_count += 1

    print(f"✅ 創建了 {tree_count} 棵高級樹木")

# ============================================
# 建築系統（超強化）
# ============================================
def create_auto_door_pro(origin):
    """專業級自動門"""
    frame_w, frame_h = 9.0, 5.5

    # 外框（鉻金屬）
    frame_mat = mat_chrome("DoorFrameChrome")

    # 頂部
    top = create_box("DoorFrameTop", (frame_w, 0.4, 0.4),
                    loc=(origin[0], origin[1], frame_h + 0.2), mat=frame_mat)

    # 側柱（帶裝飾）
    for side, x_offset in [("L", -frame_w/2 - 0.2), ("R", frame_w/2 + 0.2)]:
        # 主柱
        pillar = create_box(f"DoorPillar_{side}", (0.4, 0.4, frame_h),
                          loc=(origin[0] + x_offset, origin[1], frame_h/2), mat=frame_mat)

        # 發光裝飾條
        for i in range(5):
            strip_mat = mat_neon(f"DoorStrip_{side}_{i}", color=COLORS["cyan"], strength=15.0)
            strip_h = 0.6
            strip_y_offset = (i - 2) * 1.2

            create_box(f"DoorStrip_{side}_{i}", (0.05, 0.42, strip_h),
                      loc=(origin[0] + x_offset, origin[1], frame_h/2 + strip_y_offset),
                      mat=strip_mat)

    # 門板（彩色玻璃 + 全息效果）
    panel_mat = mat_glass_tinted("DoorPanelGlass", color=(0.4, 0.7, 1.0, 0.6), roughness=0.1)
    panel_w = frame_w / 2 - 0.3
    panel_h = frame_h - 0.5

    left_panel = create_box("DoorLeft", (panel_w, 0.15, panel_h),
                           loc=(origin[0] - panel_w/2 - 0.15, origin[1], panel_h/2 + 0.25),
                           mat=panel_mat)
    right_panel = create_box("DoorRight", (panel_w, 0.15, panel_h),
                            loc=(origin[0] + panel_w/2 + 0.15, origin[1], panel_h/2 + 0.25),
                            mat=panel_mat)

    # 門上的全息圖案
    for panel in [left_panel, right_panel]:
        holo_mat = mat_hologram("DoorHolo", color=COLORS["cyan"], strength=12.0)

        # 創建幾何圖案
        bpy.ops.mesh.primitive_torus_add(
            major_radius=0.8,
            minor_radius=0.08,
            location=(panel.location.x, panel.location.y - 0.1, panel.location.z)
        )
        holo = bpy.context.object
        holo.data.materials.append(holo_mat)
        holo.parent = panel

    # 開門動畫（更流暢）
    for panel, direction in [(left_panel, -1), (right_panel, 1)]:
        panel.keyframe_insert(data_path="location", frame=1)

        # 創建更複雜的動畫曲線
        panel.location.x = origin[0] + direction * (frame_w * 0.65)
        panel.keyframe_insert(data_path="location", frame=80)

        # 設置插值類型為 Bezier
        if panel.animation_data and panel.animation_data.action:
            for fc in panel.animation_data.action.fcurves:
                for kp in fc.keyframe_points:
                    kp.interpolation = 'BEZIER'
                    kp.handle_left_type = 'AUTO_CLAMPED'
                    kp.handle_right_type = 'AUTO_CLAMPED'

    print("✅ 專業級自動門創建完成")

def create_entrance_hall_pro(center, radius=18.0, height=15.0):
    """專業級圓形大廳"""
    # 地板（金屬質感 + 發光圖案）
    floor_mat = mat_floor_metallic("HallFloorMetal")
    floor = create_cylinder("HallFloor", radius, 0.4,
                           loc=(center[0], center[1], 0.2),
                           mat=floor_mat, verts=64)

    # 發光圓環（多層）
    ring_radii = [
        (radius * 0.3, 0.15, 20.0, COLORS["cyan"]),
        (radius * 0.5, 0.12, 15.0, COLORS["purple"]),
        (radius * 0.7, 0.10, 12.0, COLORS["blue"]),
        (radius * 0.85, 0.08, 10.0, COLORS["magenta"])
    ]

    for idx, (r, thickness, intensity, color) in enumerate(ring_radii):
        ring_mat = mat_neon(f"HallRing_{idx}", color=color, strength=intensity)
        ring = create_torus(f"HallRing_{idx}", r, thickness,
                          loc=(center[0], center[1], 0.45),
                          mat=ring_mat)

        # 添加旋轉動畫
        ring.rotation_euler = (0, 0, 0)
        ring.keyframe_insert(data_path="rotation_euler", frame=1)
        ring.rotation_euler.z = math.radians(360 if idx % 2 == 0 else -360)
        ring.keyframe_insert(data_path="rotation_euler", frame=240)

    # 牆面（面板質感）
    wall_mat = mat_wall_panels("HallWallPanel")
    segments = 24
    gap_angle = 35.0

    for i in range(segments):
        angle = (360.0 / segments) * i
        if -gap_angle <= ((angle + 180) % 360 - 180) <= gap_angle:
            continue

        rad = math.radians(angle)
        x = center[0] + (radius - 0.7) * math.cos(rad)
        y = center[1] + (radius - 0.7) * math.sin(rad)

        wall = create_box(f"HallWall_{i}", (3.5, 0.6, height),
                         loc=(x, y, height/2), rot=(0, 0, rad), mat=wall_mat)

        # 在牆上添加發光裝飾
        if i % 3 == 0:
            deco_mat = mat_neon(f"WallDeco_{i}", color=COLORS["cyan"], strength=8.0)
            deco = create_box(f"WallDeco_{i}", (0.1, 0.65, height * 0.8),
                            loc=(x * 0.98, y * 0.98, height/2), rot=(0, 0, rad), mat=deco_mat)

    # 穹頂（玻璃 + 發光）
    dome_mat = mat_glass_tinted("HallDome", color=(0.7, 0.9, 1.0, 0.3), roughness=0.05)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius * 0.95, location=(center[0], center[1], height))
    dome = bpy.context.object
    dome.name = "HallDome"
    dome.scale = (1, 1, 0.55)
    dome.data.materials.append(dome_mat)

    # 切割下半部分
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.bisect(plane_co=(center[0], center[1], height),
                       plane_no=(0, 0, 1), clear_inner=True)
    bpy.ops.object.mode_set(mode='OBJECT')

    # 中央全息投影裝置
    holo_base_mat = mat_chrome("HoloBase")
    holo_base = create_cylinder("HoloBase", 2.5, 0.8,
                                loc=(center[0], center[1], 0.4),
                                mat=holo_base_mat, verts=32)

    # 旋轉的全息環
    for i in range(3):
        holo_mat = mat_hologram(f"CentralHolo_{i}", color=COLORS["cyan"], strength=18.0)
        holo_ring = create_torus(f"CentralHolo_{i}", 1.8 + i * 0.3, 0.08,
                                loc=(center[0], center[1], height/2 + i * 0.5),
                                rot=(math.radians(90), 0, math.radians(i * 45)),
                                mat=holo_mat)

        # 旋轉動畫
        holo_ring.keyframe_insert(data_path="rotation_euler", frame=1)
        holo_ring.rotation_euler.z += math.radians(360 * (1 if i % 2 == 0 else -1))
        holo_ring.keyframe_insert(data_path="rotation_euler", frame=180)

    print("✅ 專業級圓形大廳創建完成")

def create_spiral_staircase_pro(center, height=6.5, radius=4.5, steps=40):
    """專業級螺旋樓梯"""
    step_mat = mat_chrome("StairStepChrome")

    h_step = height / steps
    angle_step = (2 * math.pi * 1.8) / steps

    for i in range(steps):
        angle = i * angle_step
        x = center[0] + radius * math.cos(angle)
        y = center[1] + radius * math.sin(angle)
        z = 0.2 + i * h_step

        step = create_box(f"Step_{i}", (2.8, 1.0, 0.18),
                         loc=(x, y, z), rot=(0, 0, angle), mat=step_mat)

        # 在每階添加發光邊緣
        if i % 2 == 0:
            edge_mat = mat_neon(f"StepEdge_{i}", color=COLORS["cyan"], strength=10.0)
            edge = create_box(f"StepEdge_{i}", (2.9, 0.08, 0.2),
                            loc=(x, y + 0.5, z), rot=(0, 0, angle), mat=edge_mat)

    # 中央柱（發光 + 裝飾）
    pillar_mat = mat_neon("StairPillar", color=COLORS["purple"], strength=12.0)
    pillar = create_cylinder("StairPillar", 0.4, height + 1.0,
                            loc=(center[0], center[1], (height + 1.0)/2),
                            mat=pillar_mat, verts=32)

    # 螺旋發光線
    for i in range(5):
        helix_angle = (2 * math.pi / 5) * i
        helix_mat = mat_neon(f"StairHelix_{i}", color=COLORS["cyan"], strength=8.0)

        bpy.ops.mesh.primitive_cylinder_add(radius=0.06, depth=height + 1.0,
                                           location=(center[0], center[1], (height + 1.0)/2),
                                           vertices=3)
        helix = bpy.context.object
        helix.name = f"StairHelix_{i}"
        helix.location.x += 0.35 * math.cos(helix_angle)
        helix.location.y += 0.35 * math.sin(helix_angle)
        helix.data.materials.append(helix_mat)

    print("✅ 專業級螺旋樓梯創建完成")

def create_lab_room_pro(name, center, width=34, depth=30, height=9):
    """專業級實驗室房間"""
    # 地板（金屬質感）
    floor_mat = mat_floor_metallic(f"{name}_FloorMetal")
    floor = create_plane(f"{name}_Floor", width, depth,
                        loc=(center[0], center[1], center[2]), mat=floor_mat)

    # 天花板（發光 + 面板）
    ceiling_mat = mat_wall_panels(f"{name}_CeilingPanel")
    ceiling = create_plane(f"{name}_Ceiling", width, depth,
                          loc=(center[0], center[1], center[2] + height), mat=ceiling_mat)

    # 四面牆（面板質感）
    wall_mat = mat_wall_panels(f"{name}_Wall")
    hw, hd, hh = width/2, depth/2, height/2

    walls = [
        (f"{name}_North", (width, 0.5, height), (0, hd, hh)),
        (f"{name}_South", (width, 0.5, height), (0, -hd, hh)),
        (f"{name}_East", (0.5, depth, height), (hw, 0, hh)),
        (f"{name}_West", (0.5, depth, height), (-hw, 0, hh))
    ]

    for wall_name, size, offset in walls:
        wall = create_box(wall_name, size,
                         loc=(center[0] + offset[0], center[1] + offset[1], center[2] + offset[2]),
                         mat=wall_mat)

    # 發光邊線（四個角落）
    edge_mat = mat_neon(f"{name}_EdgeGlow", color=COLORS["cyan"], strength=15.0)
    corners = [(hw, hd), (hw, -hd), (-hw, hd), (-hw, -hd)]

    for i, (ex, ey) in enumerate(corners):
        edge = create_cylinder(f"{name}_EdgeLight_{i}", 0.12, height,
                              loc=(center[0] + ex, center[1] + ey, center[2] + hh),
                              mat=edge_mat, verts=16)

        # 添加頂部和底部的發光圓盤
        cap_mat = mat_neon(f"{name}_EdgeCap_{i}", color=COLORS["magenta"], strength=12.0)
        top_cap = create_cylinder(f"{name}_EdgeCapTop_{i}", 0.18, 0.08,
                                 loc=(center[0] + ex, center[1] + ey, center[2] + height),
                                 mat=cap_mat, verts=16)
        bottom_cap = create_cylinder(f"{name}_EdgeCapBottom_{i}", 0.18, 0.08,
                                    loc=(center[0] + ex, center[1] + ey, center[2]),
                                    mat=cap_mat, verts=16)

    # 天花板發光面板（網格排列）
    panel_mat = mat_neon(f"{name}_CeilingLight", color=(0.9, 0.95, 1.0, 1.0), strength=8.0)

    panel_grid_x = 3
    panel_grid_y = 3
    panel_size = min(width / panel_grid_x, depth / panel_grid_y) * 0.6

    for i in range(panel_grid_x):
        for j in range(panel_grid_y):
            px = center[0] - width/2 + (width / panel_grid_x) * (i + 0.5)
            py = center[1] - depth/2 + (depth / panel_grid_y) * (j + 0.5)
            pz = center[2] + height - 0.15

            panel = create_plane(f"{name}_LightPanel_{i}_{j}", panel_size, panel_size,
                               loc=(px, py, pz), mat=panel_mat)

    print(f"✅ 專業級房間 {name} 創建完成")

def create_portal_pro(name, loc, target_name=""):
    """專業級傳送門"""
    # 外環（多層）
    ring_configs = [
        (3.0, 0.18, COLORS["purple"], 25.0),
        (2.6, 0.14, COLORS["magenta"], 20.0),
        (2.2, 0.10, COLORS["blue"], 15.0)
    ]

    for idx, (radius, thickness, color, intensity) in enumerate(ring_configs):
        ring_mat = mat_neon(f"{name}_Ring_{idx}", color=color, strength=intensity)
        ring = create_torus(f"{name}_Ring_{idx}", radius, thickness,
                          loc=loc, rot=(math.radians(90), 0, 0), mat=ring_mat)

        # 旋轉動畫
        ring.rotation_euler = (math.radians(90), 0, 0)
        ring.keyframe_insert(data_path="rotation_euler", frame=1)
        ring.rotation_euler.z = math.radians(360 * (1 if idx % 2 == 0 else -1))
        ring.keyframe_insert(data_path="rotation_euler", frame=160)

    # 能量場（全息效果）
    field_mat = mat_hologram(f"{name}_Field", color=COLORS["cyan"], strength=10.0)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=2.2, location=loc)
    field = bpy.context.object
    field.name = f"{name}_Field"
    field.scale = (1, 0.15, 1)
    field.rotation_euler = (math.radians(90), 0, 0)
    field.data.materials.append(field_mat)

    # 粒子流動效果
    for i in range(12):
        angle = (2 * math.pi / 12) * i
        px = loc[0] + 1.8 * math.cos(angle)
        py = loc[1]
        pz = loc[2] + 1.8 * math.sin(angle)

        particle_mat = mat_neon(f"{name}_Particle_{i}", color=COLORS["cyan"], strength=15.0)
        particle = create_ico_sphere(f"{name}_Particle_{i}", 0.12, subdivisions=2,
                                     loc=(px, py, pz), mat=particle_mat)

        # 圓周運動動畫
        particle.keyframe_insert(data_path="location", frame=1)
        next_angle = angle + math.radians(360)
        particle.location.x = loc[0] + 1.8 * math.cos(next_angle)
        particle.location.z = loc[2] + 1.8 * math.sin(next_angle)
        particle.keyframe_insert(data_path="location", frame=120)

    print(f"✅ 專業級傳送門 {name} 創建完成")

def create_light_bridge_pro(name, start, end, width=5.0):
    """專業級光橋"""
    vec = Vector(end) - Vector(start)
    length = vec.length
    mid = (Vector(start) + Vector(end)) / 2
    angle = math.atan2(vec.y, vec.x)

    # 主橋面（玻璃質感）
    bridge_mat = mat_glass_tinted(f"{name}_Surface", color=(0.4, 0.8, 1.0, 0.4), roughness=0.1)
    bridge = create_plane(name, length, width,
                         loc=(mid.x, mid.y, start[2] + 0.08),
                         rot=(0, 0, angle), mat=bridge_mat)

    # 發光邊緣（雙層）
    for side in [-1, 1]:
        # 外層邊緣
        outer_mat = mat_neon(f"{name}_EdgeOuter_{side}", color=COLORS["cyan"], strength=20.0)
        outer_offset = side * (width/2 + 0.15)
        perp_x = -math.sin(angle) * outer_offset
        perp_y = math.cos(angle) * outer_offset

        outer = create_plane(f"{name}_EdgeOuter_{side}", length, 0.3,
                           loc=(mid.x + perp_x, mid.y + perp_y, start[2] + 0.12),
                           rot=(0, 0, angle), mat=outer_mat)

        # 內層邊緣
        inner_mat = mat_neon(f"{name}_EdgeInner_{side}", color=COLORS["magenta"], strength=15.0)
        inner_offset = side * (width/2 - 0.2)
        perp_x = -math.sin(angle) * inner_offset
        perp_y = math.cos(angle) * inner_offset

        inner = create_plane(f"{name}_EdgeInner_{side}", length, 0.15,
                           loc=(mid.x + perp_x, mid.y + perp_y, start[2] + 0.15),
                           rot=(0, 0, angle), mat=inner_mat)

    # 能量流粒子
    num_particles = int(length / 2)
    for i in range(num_particles):
        t = i / num_particles
        px = start[0] + vec.x * t
        py = start[1] + vec.y * t
        pz = start[2] + 0.3

        particle_mat = mat_neon(f"{name}_Particle_{i}", color=COLORS["purple"], strength=12.0)
        particle = create_ico_sphere(f"{name}_Particle_{i}", 0.15, subdivisions=2,
                                     loc=(px, py, pz), mat=particle_mat)

        # 沿橋流動動畫
        particle.keyframe_insert(data_path="location", frame=1)
        particle.location.x = end[0]
        particle.location.y = end[1]
        particle.keyframe_insert(data_path="location", frame=100)

    print(f"✅ 專業級光橋 {name} 創建完成")

# ============================================
# 照明系統（電影級）
# ============================================
def setup_cinematic_lighting(target=(0, -150, 3)):
    """電影級照明設置"""
    # 主光源（太陽光）
    bpy.ops.object.light_add(type='SUN', location=(50, 20, 80))
    sun = bpy.context.object
    sun.name = "KeyLight_Sun"
    sun.data.energy = 2.5
    sun.data.color = (1.0, 0.95, 0.9)
    sun.data.angle = math.radians(5)

    direction = Vector(target) - Vector(sun.location)
    sun.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

    # 區域光（主要照明）
    bpy.ops.object.light_add(type='AREA', location=(target[0], target[1], target[2] + 30))
    area_main = bpy.context.object
    area_main.name = "FillLight_Area"
    area_main.data.energy = 1200
    area_main.data.size = 40
    area_main.data.color = (0.9, 0.95, 1.0)

    # 背光（輪廓光）
    bpy.ops.object.light_add(type='SPOT', location=(target[0], target[1] - 50, target[2] + 20))
    rim = bpy.context.object
    rim.name = "RimLight_Spot"
    rim.data.energy = 800
    rim.data.spot_size = math.radians(60)
    rim.data.spot_blend = 0.3
    rim.data.color = (0.7, 0.85, 1.0)

    direction = Vector(target) - Vector(rim.location)
    rim.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

    # 彩色氛圍光
    accent_lights = [
        ((target[0] + 30, target[1], target[2] + 15), COLORS["cyan"], 600),
        ((target[0] - 30, target[1], target[2] + 15), COLORS["magenta"], 600),
        ((target[0], target[1] + 40, target[2] + 10), COLORS["purple"], 400)
    ]

    for idx, (loc, color, energy) in enumerate(accent_lights):
        bpy.ops.object.light_add(type='POINT', location=loc)
        accent = bpy.context.object
        accent.name = f"AccentLight_{idx}"
        accent.data.energy = energy
        accent.data.color = (color[0], color[1], color[2])
        accent.data.shadow_soft_size = 5.0

    print("✅ 電影級照明設置完成")

def setup_camera_cinematic(target=(0, -150, 3)):
    """電影級相機設置"""
    cam_distance = 60
    cam_height = 35
    cam_loc = (target[0] + cam_distance * 0.5, target[1] + cam_distance, target[2] + cam_height)

    bpy.ops.object.camera_add(location=cam_loc)
    cam = bpy.context.object
    cam.name = "CinematicCamera"

    # 對準目標
    direction = Vector(target) - Vector(cam_loc)
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

    # 相機設置
    cam.data.lens = 50
    cam.data.sensor_width = 36
    cam.data.dof.use_dof = True
    cam.data.dof.focus_distance = cam_distance
    cam.data.dof.aperture_fstop = 2.8

    # 設為活動相機
    bpy.context.scene.camera = cam

    # 相機運動動畫（可選）
    cam.keyframe_insert(data_path="location", frame=1)
    cam.location.z += 10
    cam.keyframe_insert(data_path="location", frame=240)

    print("✅ 電影級相機設置完成")

# ============================================
# 渲染設置（最高品質）
# ============================================
def setup_render_settings():
    """設置最高品質渲染"""
    scene = bpy.context.scene

    # 渲染引擎
    try:
        scene.render.engine = 'BLENDER_EEVEE_NEXT'
    except:
        scene.render.engine = 'BLENDER_EEVEE'

    # EEVEE 設置
    try:
        eevee = scene.eevee
        eevee.use_bloom = True
        eevee.bloom_threshold = 0.8
        eevee.bloom_knee = 0.5
        eevee.bloom_radius = 6.5
        eevee.bloom_intensity = 0.15

        eevee.use_gtao = True
        eevee.gtao_distance = 0.2

        eevee.use_ssr = True
        eevee.use_ssr_refraction = True

        eevee.taa_render_samples = 64
    except:
        pass

    # 色彩管理
    scene.view_settings.view_transform = 'Filmic'
    scene.view_settings.look = 'Very High Contrast'

    # 輸出設置
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 100

    # 幀率
    scene.render.fps = 30
    scene.frame_end = 240

    print("✅ 渲染設置完成")

# ============================================
# 主建構函數
# ============================================
def build_ultimate_lab_pro():
    """建構超屌實驗室"""
    print("🚀 開始建構超屌實驗室...")
    print("=" * 50)

    clear_scene()

    print("\n🌍 設置世界環境...")
    setup_world_advanced()
    create_volumetric_atmosphere()

    print("\n🌌 生成星空系統...")
    create_advanced_star_field(800, 300.0)
    create_nebula_particles()

    print("\n🌲 生成高級森林...")
    create_forest_advanced()

    print("\n🛤️  建造專業級地面和步道...")
    create_ground_and_path_pro()

    print("\n🚪 建造專業級自動門...")
    create_auto_door_pro(LAYOUT["auto_door"])

    print("\n🏛️  建造專業級入口大廳...")
    create_entrance_hall_pro(LAYOUT["entrance_hall"])

    print("\n🌀 建造專業級螺旋樓梯...")
    create_spiral_staircase_pro(LAYOUT["stair_top"])

    # 房間
    print("\n🏢 建造實驗室房間...")
    rooms = [
        ("Motivation", LAYOUT["motivation_room"], 34, 30, 9),
        ("Theory", LAYOUT["theory_room"], 34, 30, 9),
        ("Programming", LAYOUT["programming_room"], 34, 30, 9),
        ("Formula", LAYOUT["formula_room"], 34, 30, 9),
        ("Simulation", LAYOUT["simulation_center"], 68, 52, 12),
        ("Conclusion", LAYOUT["conclusion_room"], 34, 30, 9),
        ("Future", LAYOUT["future_room"], 34, 30, 9)
    ]

    for room_name, center, w, d, h in rooms:
        create_lab_room_pro(room_name, center, w, d, h)

    # 連接系統
    print("\n🌀 建造專業級傳送門...")
    portals = [
        ("Portal_Motiv", (LAYOUT["motivation_room"][0], LAYOUT["motivation_room"][1] - 14, LAYOUT["motivation_room"][2] + 3.5)),
        ("Portal_Prog", (LAYOUT["programming_room"][0], LAYOUT["programming_room"][1] - 14, LAYOUT["programming_room"][2] + 3.5)),
        ("Portal_Sim", (LAYOUT["simulation_center"][0], LAYOUT["simulation_center"][1] - 24, LAYOUT["simulation_center"][2] + 4.5))
    ]

    for portal_name, portal_loc in portals:
        create_portal_pro(portal_name, portal_loc)

    print("\n🌉 建造專業級光橋...")
    bridges = [
        ("Bridge_Theory_Prog",
         (LAYOUT["theory_room"][0], LAYOUT["theory_room"][1] - 16, LAYOUT["theory_room"][2]),
         (LAYOUT["programming_room"][0], LAYOUT["programming_room"][1] + 16, LAYOUT["programming_room"][2])),
        ("Bridge_Formula_Sim",
         (LAYOUT["formula_room"][0], LAYOUT["formula_room"][1] - 16, LAYOUT["formula_room"][2]),
         (LAYOUT["simulation_center"][0], LAYOUT["simulation_center"][1] + 28, LAYOUT["simulation_center"][2])),
        ("Bridge_Conclusion_Future",
         (LAYOUT["conclusion_room"][0], LAYOUT["conclusion_room"][1] - 16, LAYOUT["conclusion_room"][2]),
         (LAYOUT["future_room"][0], LAYOUT["future_room"][1] + 16, LAYOUT["future_room"][2]))
    ]

    for bridge_name, start, end in bridges:
        create_light_bridge_pro(bridge_name, start, end)

    print("\n💡 設置電影級照明...")
    setup_cinematic_lighting(LAYOUT["entrance_hall"])

    print("\n📷 設置電影級相機...")
    setup_camera_cinematic(LAYOUT["entrance_hall"])

    print("\n🎨 設置渲染參數...")
    setup_render_settings()

    print("\n" + "=" * 50)
    print("✅ 超屌實驗室建構完成！")
    print("=" * 50)

# ============================================
# 匯出
# ============================================
def export_glb_pro(path):
    """專業級 GLB 匯出"""
    print(f"\n📦 正在匯出 GLB 到: {path}")

    try:
        bpy.ops.export_scene.gltf(
            filepath=path,
            export_format='GLB',
            export_yup=True,
            export_animations=True,
            export_apply=True,
            export_lights=True,
            export_cameras=False,
            export_materials='EXPORT',
            export_colors=True,
            export_attributes=True,
            export_extras=True
        )

        # 獲取檔案大小
        import os
        file_size = os.path.getsize(path) / (1024 * 1024)

        print(f"✅ 匯出成功！")
        print(f"📍 檔案位置: {path}")
        print(f"📊 檔案大小: {file_size:.2f} MB")

        # 嘗試打開檔案所在資料夾
        try:
            import subprocess
            import platform

            folder = os.path.dirname(path)

            if platform.system() == "Windows":
                subprocess.Popen(f'explorer /select,"{path}"')
            elif platform.system() == "Darwin":  # macOS
                subprocess.Popen(["open", "-R", path])
            else:  # Linux
                subprocess.Popen(["xdg-open", folder])

            print("📂 已打開檔案所在資料夾")
        except:
            pass

        return True

    except Exception as e:
        print(f"❌ 匯出失敗: {e}")
        return False

# ============================================
# 執行
# ============================================
def main():
    """主程式"""
    build_ultimate_lab_pro()

    print("\n🎬 正在準備匯出...")
    success = export_glb_pro(EXPORT_PATH)

    if success:
        print("\n🎉 全部完成！")
        print("現在可以將 GLB 檔案上傳到你的 Codespace 了！")
    else:
        print("\n❌ 匯出過程出現問題")

if __name__ == "__main__":
    main()
