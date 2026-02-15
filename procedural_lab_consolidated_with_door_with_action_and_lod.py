# -*- coding: utf-8 -*-
"""Ultimate Procedural Sci‑Fi Laboratory (Blender 5.0.1+)"""
import bpy
import math
import os
import random
import tempfile
from mathutils import Vector, Euler

EXPORT_NAME = "ultimate_procedural_lab.glb"
blend_dir = bpy.path.abspath("//")
if blend_dir and os.path.isdir(blend_dir):
    EXPORT_PATH = os.path.join(blend_dir, EXPORT_NAME)
else:
    EXPORT_PATH = os.path.join(tempfile.gettempdir(), EXPORT_NAME)
OVERLAY_PATH = os.path.join(os.path.dirname(EXPORT_PATH), "overlay_black.png")
random.seed(424242)
WALL = 0.25
DOOR_W = 6.0
DOOR_H = 4.0
LAYOUT = {"lobby": (0,-72,0), "gate":(0,-36,0), "motivation":(0,-132,0), "theory":(64,-132,0), "programming":(128,-132,0), "formula":(128,-208,0), "simulation":(128,-300,0), "conclusion":(128,-388,0), "future":(128,-472,0)}
ROOM_SPECS = {"lobby": (30,30,12), "motivation":(22,18,8), "theory":(24,20,8), "programming":(24,20,8), "formula":(22,18,8), "simulation":(38,26,10), "conclusion":(22,18,8), "future":(22,18,8)}
THEME = {"white": (0.95,0.96,0.99,1), "steel":(0.62,0.67,0.76,1), "dark":(0.05,0.06,0.1,1), "cyan":(0.02,0.85,1,1), "magenta":(0.98,0.2,0.65,1), "purple":(0.58,0.26,1,1), "green":(0.15,0.9,0.5,1)}
MAT_CACHE = {}

def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False, confirm=False)
    for coll in [bpy.data.meshes, bpy.data.materials, bpy.data.images, bpy.data.textures, bpy.data.cameras, bpy.data.lights]:
        for item in list(coll):
            try:
                if getattr(item, "users", 0) == 0:
                    coll.remove(item)
            except Exception:
                pass

def mat_pbr(name, color=(1,1,1,1), rough=0.4, metal=0.0, emit=0.0):
    key=("pbr",name,color,rough,metal,emit)
    if key in MAT_CACHE: return MAT_CACHE[key]
    m=bpy.data.materials.new(name=name); m.use_nodes=True
    n=m.node_tree.nodes; l=m.node_tree.links; n.clear()
    out=n.new(type="ShaderNodeOutputMaterial")
    bsdf=n.new(type="ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value=color
    bsdf.inputs["Roughness"].default_value=rough
    bsdf.inputs["Metallic"].default_value=metal
    if emit>0:
        try:
            bsdf.inputs["Emission Color"].default_value=color
            bsdf.inputs["Emission Strength"].default_value=emit
        except Exception:
            pass
    l.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    MAT_CACHE[key]=m; return m

def mat_emit(name, color=(0.5,0.8,1,1), strength=8.0):
    key=("emit",name,color,strength)
    if key in MAT_CACHE: return MAT_CACHE[key]
    m=bpy.data.materials.new(name=name); m.use_nodes=True
    n=m.node_tree.nodes; l=m.node_tree.links; n.clear()
    out=n.new(type="ShaderNodeOutputMaterial")
    em=n.new(type="ShaderNodeEmission")
    em.inputs["Color"].default_value=color; em.inputs["Strength"].default_value=strength
    l.new(em.outputs["Emission"], out.inputs["Surface"])
    MAT_CACHE[key]=m; return m

def mat_glass(name, color=(0.65,0.88,1,0.35), rough=0.03):
    key=("glass",name,color,rough)
    if key in MAT_CACHE: return MAT_CACHE[key]
    m=bpy.data.materials.new(name=name); m.use_nodes=True
    n=m.node_tree.nodes; l=m.node_tree.links; n.clear()
    out=n.new(type="ShaderNodeOutputMaterial")
    g=n.new(type="ShaderNodeBsdfGlass")
    g.inputs["Color"].default_value=color; g.inputs["Roughness"].default_value=rough
    l.new(g.outputs["BSDF"], out.inputs["Surface"])
    m.blend_method="BLEND"; MAT_CACHE[key]=m; return m

def set_mat(obj, mat):
    if obj.data.materials: obj.data.materials[0]=mat
    else: obj.data.materials.append(mat)

def box(name, size, loc=(0,0,0), rot=(0,0,0), mat=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o=bpy.context.object; o.name=name; o.scale=(size[0]/2,size[1]/2,size[2]/2)
    if mat: set_mat(o, mat)
    return o

def plane(name, sx, sy, loc=(0,0,0), rot=(0,0,0), mat=None):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
    o=bpy.context.object; o.name=name; o.scale=(sx/2,sy/2,1)
    if mat: set_mat(o, mat)
    return o

def cylinder(name, r, h, loc=(0,0,0), rot=(0,0,0), verts=24, mat=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=h, location=loc, rotation=rot)
    o=bpy.context.object; o.name=name
    if mat: set_mat(o, mat)
    return o

def torus(name, major, minor, loc=(0,0,0), rot=(0,0,0), mat=None):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor, location=loc, rotation=rot)
    o=bpy.context.object; o.name=name
    if mat: set_mat(o, mat)
    return o

def ico(name, radius, loc=(0,0,0), sub=1, mat=None):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=radius, location=loc)
    o=bpy.context.object; o.name=name
    if mat: set_mat(o, mat)
    return o

def room(center, w, d, h, prefix):
    x,y,z=center
    wm=mat_pbr(f"{prefix}_Wall", THEME["white"], 0.52, 0.12)
    fm=mat_pbr(f"{prefix}_Floor", (0.18,0.2,0.25,1), 0.34, 0.68)
    cm=mat_pbr(f"{prefix}_Ceil", (0.84,0.86,0.92,1), 0.44, 0.10, emit=0.2)
    hw,hd=w/2,d/2
    box(f"{prefix}_Floor", (w,d,0.2), (x,y,z-0.1), mat=fm)
    box(f"{prefix}_Ceil", (w,d,0.2), (x,y,z+h+0.1), mat=cm)
    box(f"{prefix}_N", (w,WALL,h), (x,y+hd-WALL/2,z+h/2), mat=wm)
    box(f"{prefix}_S", (w,WALL,h), (x,y-hd+WALL/2,z+h/2), mat=wm)
    box(f"{prefix}_E", (d,WALL,h), (x+hw-WALL/2,y,z+h/2), rot=(0,0,math.radians(90)), mat=wm)
    box(f"{prefix}_W", (d,WALL,h), (x-hw+WALL/2,y,z+h/2), rot=(0,0,math.radians(90)), mat=wm)
    return {"center":center,"w":w,"d":d,"h":h}

def edge(r, d):
    x,y,z=r["center"]
    if d=="+x": return (x+r["w"]/2,y,z)
    if d=="-x": return (x-r["w"]/2,y,z)
    if d=="+y": return (x,y+r["d"]/2,z)
    return (x,y-r["d"]/2,z)

def corridor(name, a, b, width=8, height=5):
    va, vb = Vector(a), Vector(b)
    v = vb-va; L=v.length; c=(va+vb)/2; ang=math.atan2(v.y,v.x)
    floor=mat_pbr(f"{name}_F", (0.2,0.22,0.28,1), 0.32, 0.6)
    ceil=mat_pbr(f"{name}_C", (0.82,0.85,0.92,1), 0.45, 0.1)
    wall=mat_pbr(f"{name}_W", THEME["white"], 0.55, 0.12)
    neon=mat_emit(f"{name}_N", THEME["cyan"], 8.0)
    plane(f"{name}_Floor", L, width, (c.x,c.y,a[2]+0.03), (0,0,ang), floor)
    plane(f"{name}_Ceil", L, width, (c.x,c.y,a[2]+height), (0,0,ang), ceil)
    off=width/2 + WALL/2; px=-math.sin(ang); py=math.cos(ang)
    box(f"{name}_L", (L,WALL,height), (c.x+px*off,c.y+py*off,a[2]+height/2), (0,0,ang), wall)
    box(f"{name}_R", (L,WALL,height), (c.x-px*off,c.y-py*off,a[2]+height/2), (0,0,ang), wall)
    plane(f"{name}_NL", L, 0.08, (c.x+px*(off-WALL/2),c.y+py*(off-WALL/2),a[2]+height-0.12), (0,0,ang), neon)
    plane(f"{name}_NR", L, 0.08, (c.x-px*(off-WALL/2),c.y-py*(off-WALL/2),a[2]+height-0.12), (0,0,ang), neon)

def sliding_door(name, pos):
    x,y,z=pos
    fm=mat_pbr(f"{name}_Frame", THEME["steel"], 0.24, 0.86, emit=0.2)
    gm=mat_glass(f"{name}_Glass")
    sm=mat_emit(f"{name}_Strip", THEME["cyan"], 12)
    box(f"{name}_Top", (DOOR_W,0.35,0.35), (x,y,z+DOOR_H+0.2), mat=fm)
    box(f"{name}_LC", (0.35,0.35,DOOR_H), (x-DOOR_W/2,y,z+DOOR_H/2), mat=fm)
    box(f"{name}_RC", (0.35,0.35,DOOR_H), (x+DOOR_W/2,y,z+DOOR_H/2), mat=fm)
    pw=DOOR_W/2-0.2
    l=box(f"{name}_L", (pw,0.12,DOOR_H-0.25), (x-pw/2,y,z+DOOR_H/2), mat=gm)
    r=box(f"{name}_R", (pw,0.12,DOOR_H-0.25), (x+pw/2,y,z+DOOR_H/2), mat=gm)
    box(f"{name}_LS", (0.05,0.14,DOOR_H-0.8), (l.location.x,y-0.07,z+DOOR_H/2), mat=sm)
    box(f"{name}_RS", (0.05,0.14,DOOR_H-0.8), (r.location.x,y-0.07,z+DOOR_H/2), mat=sm)
    l.keyframe_insert(data_path="location", frame=1); l.location.x -= DOOR_W*0.62; l.keyframe_insert(data_path="location", frame=80)
    r.keyframe_insert(data_path="location", frame=1); r.location.x += DOOR_W*0.62; r.keyframe_insert(data_path="location", frame=80)

def bridge(name, a, b, width=5):
    va,vb=Vector(a),Vector(b); v=vb-va; L=v.length; c=(va+vb)/2; ang=math.atan2(v.y,v.x)
    plane(f"{name}_Deck", L, width, (c.x,c.y,a[2]+0.09), (0,0,ang), mat_glass(f"{name}_G", (0.45,0.82,1,0.33),0.08))
    plane(f"{name}_L", L, 0.24, (c.x,c.y+width/2-0.14,a[2]+0.12), (0,0,ang), mat_emit(f"{name}_LM", THEME["cyan"], 13))
    plane(f"{name}_R", L, 0.18, (c.x,c.y-width/2+0.10,a[2]+0.14), (0,0,ang), mat_emit(f"{name}_RM", THEME["magenta"], 10))

def setup_env():
    if bpy.context.scene.world is None: bpy.context.scene.world = bpy.data.worlds.new("World")
    w=bpy.context.scene.world; w.use_nodes=True
    n=w.node_tree.nodes; l=w.node_tree.links; n.clear()
    out=n.new(type="ShaderNodeOutputWorld")
    bg=n.new(type="ShaderNodeBackground"); bg.inputs["Color"].default_value=(0.015,0.02,0.055,1); bg.inputs["Strength"].default_value=0.42
    l.new(bg.outputs["Background"], out.inputs["Surface"])

def sky_and_ground():
    plane("Ground",460,860,(60,-220,-0.01), mat=mat_pbr("GroundM", (0.08,0.09,0.12,1), 0.95, 0.05))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=190, location=(0,-160,40))
    d=bpy.context.object; d.name="SkyDome"; d.scale.x=-1; set_mat(d, mat_emit("Sky", (0.03,0.04,0.09,1), 0.08))

def forest():
    tm=mat_pbr("TreeTrunk", (0.2,0.14,0.1,1), 0.86, 0)
    lm=mat_emit("TreeLeaf", (0.08,0.32,0.12,1), 2.0)
    idx=0
    for i in range(7):
        for j in range(7):
            x=(i-3.5)*16 + random.uniform(-3,3)
            y=-130 + (j-3.5)*16 + random.uniform(-3,3)
            h=random.uniform(5,8.5); r=random.uniform(0.25,0.6)
            cylinder(f"Trunk_{idx}", r, h, (x,y,h/2), mat=tm)
            ico(f"Leaf_{idx}", random.uniform(1.6,2.6), (x,y,h+1.0), sub=2, mat=lm)
            idx += 1

def lights_camera_render():
    bpy.ops.object.light_add(type="SUN", location=(80,-80,120)); sun=bpy.context.object; sun.data.energy=3.0
    bpy.ops.object.light_add(type="AREA", location=(20,-130,48)); ar=bpy.context.object; ar.data.energy=520; ar.data.size=25
    bpy.ops.object.camera_add(location=(0,-20,8), rotation=(math.radians(75),0,0)); cam=bpy.context.object; bpy.context.scene.camera=cam
    scene=bpy.context.scene
    try: scene.render.engine="BLENDER_EEVEE_NEXT"
    except Exception: scene.render.engine="BLENDER_EEVEE"
    try:
        ee=scene.eevee; ee.use_bloom=True; ee.use_gtao=True; ee.use_ssr=True; ee.taa_render_samples=48
    except Exception:
        pass
    scene.view_settings.view_transform="Filmic"; scene.view_settings.look="Very High Contrast"
    scene.render.resolution_x=1920; scene.render.resolution_y=1080; scene.render.fps=30; scene.frame_end=240
    return cam

def fade_panel(cam):
    p=plane("FadePanel",8,8,(0,0,0)); p.parent=cam; p.location=Vector((0,0,-1.0))
    m=bpy.data.materials.new("FadeMat"); m.use_nodes=True; m.blend_method="BLEND"
    # Blender build compatibility: some versions do not expose shadow_method on Material
    try:
        m.shadow_method = "NONE"
    except Exception:
        pass
    n=m.node_tree.nodes; l=m.node_tree.links; n.clear()
    out=n.new(type="ShaderNodeOutputMaterial")
    tr=n.new(type="ShaderNodeBsdfTransparent")
    em=n.new(type="ShaderNodeEmission"); em.inputs["Color"].default_value=(0,0,0,1)
    mix=n.new(type="ShaderNodeMixShader")
    l.new(tr.outputs["BSDF"], mix.inputs[1]); l.new(em.outputs["Emission"], mix.inputs[2]); l.new(mix.outputs["Shader"], out.inputs["Surface"])
    set_mat(p,m)
    mix.inputs[0].default_value=0; mix.inputs[0].keyframe_insert("default_value", frame=30)
    mix.inputs[0].default_value=1; mix.inputs[0].keyframe_insert("default_value", frame=42)
    mix.inputs[0].default_value=1; mix.inputs[0].keyframe_insert("default_value", frame=56)
    mix.inputs[0].default_value=0; mix.inputs[0].keyframe_insert("default_value", frame=64)

def overlay_png(path):
    name="overlay_black_img"
    if name in bpy.data.images: img=bpy.data.images[name]
    else:
        img=bpy.data.images.new(name, width=1, height=1, alpha=True, float_buffer=False)
        img.pixels=[0.0,0.0,0.0,1.0]
    img.filepath_raw=path; img.file_format="PNG"
    try: img.save()
    except Exception: pass

def build():
    clear_scene(); setup_env(); sky_and_ground(); forest(); cam=lights_camera_render()
    # rooms
    rs={}
    for k,c in LAYOUT.items():
        if k in ROOM_SPECS: rs[k]=room(c,*ROOM_SPECS[k], prefix=k.capitalize())
    # corridors no gaps
    corridor("C1", edge(rs["lobby"],"-y"), edge(rs["motivation"],"+y"), 8, 5)
    corridor("C2", edge(rs["motivation"],"+x"), edge(rs["theory"],"-x"), 8, 5)
    corridor("C3", edge(rs["theory"],"+x"), edge(rs["programming"],"-x"), 8, 5)
    corridor("C4", edge(rs["programming"],"-y"), edge(rs["formula"],"+y"), 8, 5)
    corridor("C5", edge(rs["formula"],"-y"), edge(rs["simulation"],"+y"), 8, 5)
    corridor("C6", edge(rs["simulation"],"-y"), edge(rs["conclusion"],"+y"), 8, 5)
    corridor("C7", edge(rs["conclusion"],"-y"), edge(rs["future"],"+y"), 8, 5)
    sliding_door("Gate", LAYOUT["gate"])
    bridge("B1", (32,-132,0), (96,-132,0), 5)
    bridge("B2", (128,-168,0), (128,-224,0), 5)
    create = lambda n,p: torus(n,2.2,0.1,p,rot=(math.radians(90),0,0),mat=mat_emit(n+"M",THEME["cyan"],8))
    create("Portal1", (0,-106,3.5)); create("Portal2", (128,-248,3.5))
    # hall and devices
    cylinder("HallOuter",10.5,13.5,(0,-72,6.75),verts=64,mat=mat_pbr("HallW",THEME["white"],0.3,0.1))
    create_server = lambda c: [box(f"Rack_{i}",(2.2,1.3,5.5),(c[0]-7.5+i*3,c[1],c[2]+2.75),mat=mat_pbr("RackM",(0.12,0.14,0.18,1),0.48,0.5)) for i in range(6)]
    create_server(LAYOUT["programming"])
    for i in range(5):
        cylinder(f"Pipe_{i}",0.2,5.5,(LAYOUT["formula"][0]-7+i*3.5,LAYOUT["formula"][1]+5.5,2.75),mat=mat_pbr("PipeM",(0.78,0.83,0.92,1),0.2,0.92))
    o1=torus("EnergyOuter",3.2,0.18,(LAYOUT["simulation"][0],LAYOUT["simulation"][1],3.6),rot=(math.radians(90),0,0),mat=mat_emit("EM1",THEME["cyan"],15)); o1.keyframe_insert(data_path="rotation_euler", frame=1); o1.rotation_euler.z += math.radians(360); o1.keyframe_insert(data_path="rotation_euler", frame=160)
    fade_panel(cam); overlay_png(OVERLAY_PATH)

def optional_module_1(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt1_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt1_M2", THEME["cyan"], 5.0)
    box("Opt1_Box", (1.0, 1.0, 0.35), (ox+1*0.45, oy+1*0.31, oz+0.18), mat=m1)
    torus("Opt1_Ring", 0.24, 0.04, (ox+1*0.45, oy+1*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_2(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt2_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt2_M2", THEME["cyan"], 5.0)
    box("Opt2_Box", (1.0, 1.0, 0.35), (ox+2*0.45, oy+2*0.31, oz+0.18), mat=m1)
    torus("Opt2_Ring", 0.24, 0.04, (ox+2*0.45, oy+2*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_3(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt3_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt3_M2", THEME["cyan"], 5.0)
    box("Opt3_Box", (1.0, 1.0, 0.35), (ox+3*0.45, oy+3*0.31, oz+0.18), mat=m1)
    torus("Opt3_Ring", 0.24, 0.04, (ox+3*0.45, oy+3*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_4(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt4_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt4_M2", THEME["cyan"], 5.0)
    box("Opt4_Box", (1.0, 1.0, 0.35), (ox+4*0.45, oy+4*0.31, oz+0.18), mat=m1)
    torus("Opt4_Ring", 0.24, 0.04, (ox+4*0.45, oy+4*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_5(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt5_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt5_M2", THEME["cyan"], 5.0)
    box("Opt5_Box", (1.0, 1.0, 0.35), (ox+5*0.45, oy+5*0.31, oz+0.18), mat=m1)
    torus("Opt5_Ring", 0.24, 0.04, (ox+5*0.45, oy+5*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_6(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt6_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt6_M2", THEME["cyan"], 5.0)
    box("Opt6_Box", (1.0, 1.0, 0.35), (ox+6*0.45, oy+6*0.31, oz+0.18), mat=m1)
    torus("Opt6_Ring", 0.24, 0.04, (ox+6*0.45, oy+6*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_7(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt7_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt7_M2", THEME["cyan"], 5.0)
    box("Opt7_Box", (1.0, 1.0, 0.35), (ox+7*0.45, oy+7*0.31, oz+0.18), mat=m1)
    torus("Opt7_Ring", 0.24, 0.04, (ox+7*0.45, oy+7*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_8(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt8_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt8_M2", THEME["cyan"], 5.0)
    box("Opt8_Box", (1.0, 1.0, 0.35), (ox+8*0.45, oy+8*0.31, oz+0.18), mat=m1)
    torus("Opt8_Ring", 0.24, 0.04, (ox+8*0.45, oy+8*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_9(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt9_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt9_M2", THEME["cyan"], 5.0)
    box("Opt9_Box", (1.0, 1.0, 0.35), (ox+0*0.45, oy+9*0.31, oz+0.18), mat=m1)
    torus("Opt9_Ring", 0.24, 0.04, (ox+0*0.45, oy+9*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_10(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt10_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt10_M2", THEME["cyan"], 5.0)
    box("Opt10_Box", (1.0, 1.0, 0.35), (ox+1*0.45, oy+10*0.31, oz+0.18), mat=m1)
    torus("Opt10_Ring", 0.24, 0.04, (ox+1*0.45, oy+10*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_11(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt11_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt11_M2", THEME["cyan"], 5.0)
    box("Opt11_Box", (1.0, 1.0, 0.35), (ox+2*0.45, oy+11*0.31, oz+0.18), mat=m1)
    torus("Opt11_Ring", 0.24, 0.04, (ox+2*0.45, oy+11*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_12(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt12_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt12_M2", THEME["cyan"], 5.0)
    box("Opt12_Box", (1.0, 1.0, 0.35), (ox+3*0.45, oy+12*0.31, oz+0.18), mat=m1)
    torus("Opt12_Ring", 0.24, 0.04, (ox+3*0.45, oy+12*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_13(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt13_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt13_M2", THEME["cyan"], 5.0)
    box("Opt13_Box", (1.0, 1.0, 0.35), (ox+4*0.45, oy+0*0.31, oz+0.18), mat=m1)
    torus("Opt13_Ring", 0.24, 0.04, (ox+4*0.45, oy+0*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_14(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt14_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt14_M2", THEME["cyan"], 5.0)
    box("Opt14_Box", (1.0, 1.0, 0.35), (ox+5*0.45, oy+1*0.31, oz+0.18), mat=m1)
    torus("Opt14_Ring", 0.24, 0.04, (ox+5*0.45, oy+1*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_15(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt15_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt15_M2", THEME["cyan"], 5.0)
    box("Opt15_Box", (1.0, 1.0, 0.35), (ox+6*0.45, oy+2*0.31, oz+0.18), mat=m1)
    torus("Opt15_Ring", 0.24, 0.04, (ox+6*0.45, oy+2*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_16(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt16_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt16_M2", THEME["cyan"], 5.0)
    box("Opt16_Box", (1.0, 1.0, 0.35), (ox+7*0.45, oy+3*0.31, oz+0.18), mat=m1)
    torus("Opt16_Ring", 0.24, 0.04, (ox+7*0.45, oy+3*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_17(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt17_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt17_M2", THEME["cyan"], 5.0)
    box("Opt17_Box", (1.0, 1.0, 0.35), (ox+8*0.45, oy+4*0.31, oz+0.18), mat=m1)
    torus("Opt17_Ring", 0.24, 0.04, (ox+8*0.45, oy+4*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_18(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt18_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt18_M2", THEME["cyan"], 5.0)
    box("Opt18_Box", (1.0, 1.0, 0.35), (ox+0*0.45, oy+5*0.31, oz+0.18), mat=m1)
    torus("Opt18_Ring", 0.24, 0.04, (ox+0*0.45, oy+5*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_19(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt19_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt19_M2", THEME["cyan"], 5.0)
    box("Opt19_Box", (1.0, 1.0, 0.35), (ox+1*0.45, oy+6*0.31, oz+0.18), mat=m1)
    torus("Opt19_Ring", 0.24, 0.04, (ox+1*0.45, oy+6*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_20(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt20_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt20_M2", THEME["cyan"], 5.0)
    box("Opt20_Box", (1.0, 1.0, 0.35), (ox+2*0.45, oy+7*0.31, oz+0.18), mat=m1)
    torus("Opt20_Ring", 0.24, 0.04, (ox+2*0.45, oy+7*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_21(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt21_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt21_M2", THEME["cyan"], 5.0)
    box("Opt21_Box", (1.0, 1.0, 0.35), (ox+3*0.45, oy+8*0.31, oz+0.18), mat=m1)
    torus("Opt21_Ring", 0.24, 0.04, (ox+3*0.45, oy+8*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_22(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt22_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt22_M2", THEME["cyan"], 5.0)
    box("Opt22_Box", (1.0, 1.0, 0.35), (ox+4*0.45, oy+9*0.31, oz+0.18), mat=m1)
    torus("Opt22_Ring", 0.24, 0.04, (ox+4*0.45, oy+9*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_23(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt23_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt23_M2", THEME["cyan"], 5.0)
    box("Opt23_Box", (1.0, 1.0, 0.35), (ox+5*0.45, oy+10*0.31, oz+0.18), mat=m1)
    torus("Opt23_Ring", 0.24, 0.04, (ox+5*0.45, oy+10*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_24(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt24_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt24_M2", THEME["cyan"], 5.0)
    box("Opt24_Box", (1.0, 1.0, 0.35), (ox+6*0.45, oy+11*0.31, oz+0.18), mat=m1)
    torus("Opt24_Ring", 0.24, 0.04, (ox+6*0.45, oy+11*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_25(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt25_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt25_M2", THEME["cyan"], 5.0)
    box("Opt25_Box", (1.0, 1.0, 0.35), (ox+7*0.45, oy+12*0.31, oz+0.18), mat=m1)
    torus("Opt25_Ring", 0.24, 0.04, (ox+7*0.45, oy+12*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_26(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt26_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt26_M2", THEME["cyan"], 5.0)
    box("Opt26_Box", (1.0, 1.0, 0.35), (ox+8*0.45, oy+0*0.31, oz+0.18), mat=m1)
    torus("Opt26_Ring", 0.24, 0.04, (ox+8*0.45, oy+0*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_27(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt27_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt27_M2", THEME["cyan"], 5.0)
    box("Opt27_Box", (1.0, 1.0, 0.35), (ox+0*0.45, oy+1*0.31, oz+0.18), mat=m1)
    torus("Opt27_Ring", 0.24, 0.04, (ox+0*0.45, oy+1*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_28(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt28_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt28_M2", THEME["cyan"], 5.0)
    box("Opt28_Box", (1.0, 1.0, 0.35), (ox+1*0.45, oy+2*0.31, oz+0.18), mat=m1)
    torus("Opt28_Ring", 0.24, 0.04, (ox+1*0.45, oy+2*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_29(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt29_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt29_M2", THEME["cyan"], 5.0)
    box("Opt29_Box", (1.0, 1.0, 0.35), (ox+2*0.45, oy+3*0.31, oz+0.18), mat=m1)
    torus("Opt29_Ring", 0.24, 0.04, (ox+2*0.45, oy+3*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_30(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt30_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt30_M2", THEME["cyan"], 5.0)
    box("Opt30_Box", (1.0, 1.0, 0.35), (ox+3*0.45, oy+4*0.31, oz+0.18), mat=m1)
    torus("Opt30_Ring", 0.24, 0.04, (ox+3*0.45, oy+4*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_31(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt31_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt31_M2", THEME["cyan"], 5.0)
    box("Opt31_Box", (1.0, 1.0, 0.35), (ox+4*0.45, oy+5*0.31, oz+0.18), mat=m1)
    torus("Opt31_Ring", 0.24, 0.04, (ox+4*0.45, oy+5*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_32(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt32_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt32_M2", THEME["cyan"], 5.0)
    box("Opt32_Box", (1.0, 1.0, 0.35), (ox+5*0.45, oy+6*0.31, oz+0.18), mat=m1)
    torus("Opt32_Ring", 0.24, 0.04, (ox+5*0.45, oy+6*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_33(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt33_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt33_M2", THEME["cyan"], 5.0)
    box("Opt33_Box", (1.0, 1.0, 0.35), (ox+6*0.45, oy+7*0.31, oz+0.18), mat=m1)
    torus("Opt33_Ring", 0.24, 0.04, (ox+6*0.45, oy+7*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_34(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt34_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt34_M2", THEME["cyan"], 5.0)
    box("Opt34_Box", (1.0, 1.0, 0.35), (ox+7*0.45, oy+8*0.31, oz+0.18), mat=m1)
    torus("Opt34_Ring", 0.24, 0.04, (ox+7*0.45, oy+8*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_35(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt35_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt35_M2", THEME["cyan"], 5.0)
    box("Opt35_Box", (1.0, 1.0, 0.35), (ox+8*0.45, oy+9*0.31, oz+0.18), mat=m1)
    torus("Opt35_Ring", 0.24, 0.04, (ox+8*0.45, oy+9*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_36(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt36_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt36_M2", THEME["cyan"], 5.0)
    box("Opt36_Box", (1.0, 1.0, 0.35), (ox+0*0.45, oy+10*0.31, oz+0.18), mat=m1)
    torus("Opt36_Ring", 0.24, 0.04, (ox+0*0.45, oy+10*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_37(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt37_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt37_M2", THEME["cyan"], 5.0)
    box("Opt37_Box", (1.0, 1.0, 0.35), (ox+1*0.45, oy+11*0.31, oz+0.18), mat=m1)
    torus("Opt37_Ring", 0.24, 0.04, (ox+1*0.45, oy+11*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_38(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt38_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt38_M2", THEME["cyan"], 5.0)
    box("Opt38_Box", (1.0, 1.0, 0.35), (ox+2*0.45, oy+12*0.31, oz+0.18), mat=m1)
    torus("Opt38_Ring", 0.24, 0.04, (ox+2*0.45, oy+12*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_39(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt39_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt39_M2", THEME["cyan"], 5.0)
    box("Opt39_Box", (1.0, 1.0, 0.35), (ox+3*0.45, oy+0*0.31, oz+0.18), mat=m1)
    torus("Opt39_Ring", 0.24, 0.04, (ox+3*0.45, oy+0*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_40(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt40_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt40_M2", THEME["cyan"], 5.0)
    box("Opt40_Box", (1.0, 1.0, 0.35), (ox+4*0.45, oy+1*0.31, oz+0.18), mat=m1)
    torus("Opt40_Ring", 0.24, 0.04, (ox+4*0.45, oy+1*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_41(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt41_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt41_M2", THEME["cyan"], 5.0)
    box("Opt41_Box", (1.0, 1.0, 0.35), (ox+5*0.45, oy+2*0.31, oz+0.18), mat=m1)
    torus("Opt41_Ring", 0.24, 0.04, (ox+5*0.45, oy+2*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_42(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt42_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt42_M2", THEME["cyan"], 5.0)
    box("Opt42_Box", (1.0, 1.0, 0.35), (ox+6*0.45, oy+3*0.31, oz+0.18), mat=m1)
    torus("Opt42_Ring", 0.24, 0.04, (ox+6*0.45, oy+3*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_43(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt43_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt43_M2", THEME["cyan"], 5.0)
    box("Opt43_Box", (1.0, 1.0, 0.35), (ox+7*0.45, oy+4*0.31, oz+0.18), mat=m1)
    torus("Opt43_Ring", 0.24, 0.04, (ox+7*0.45, oy+4*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_44(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt44_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt44_M2", THEME["cyan"], 5.0)
    box("Opt44_Box", (1.0, 1.0, 0.35), (ox+8*0.45, oy+5*0.31, oz+0.18), mat=m1)
    torus("Opt44_Ring", 0.24, 0.04, (ox+8*0.45, oy+5*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_45(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt45_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt45_M2", THEME["cyan"], 5.0)
    box("Opt45_Box", (1.0, 1.0, 0.35), (ox+0*0.45, oy+6*0.31, oz+0.18), mat=m1)
    torus("Opt45_Ring", 0.24, 0.04, (ox+0*0.45, oy+6*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_46(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt46_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt46_M2", THEME["cyan"], 5.0)
    box("Opt46_Box", (1.0, 1.0, 0.35), (ox+1*0.45, oy+7*0.31, oz+0.18), mat=m1)
    torus("Opt46_Ring", 0.24, 0.04, (ox+1*0.45, oy+7*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_47(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt47_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt47_M2", THEME["cyan"], 5.0)
    box("Opt47_Box", (1.0, 1.0, 0.35), (ox+2*0.45, oy+8*0.31, oz+0.18), mat=m1)
    torus("Opt47_Ring", 0.24, 0.04, (ox+2*0.45, oy+8*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_48(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt48_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt48_M2", THEME["cyan"], 5.0)
    box("Opt48_Box", (1.0, 1.0, 0.35), (ox+3*0.45, oy+9*0.31, oz+0.18), mat=m1)
    torus("Opt48_Ring", 0.24, 0.04, (ox+3*0.45, oy+9*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_49(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt49_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt49_M2", THEME["cyan"], 5.0)
    box("Opt49_Box", (1.0, 1.0, 0.35), (ox+4*0.45, oy+10*0.31, oz+0.18), mat=m1)
    torus("Opt49_Ring", 0.24, 0.04, (ox+4*0.45, oy+10*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_50(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt50_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt50_M2", THEME["cyan"], 5.0)
    box("Opt50_Box", (1.0, 1.0, 0.35), (ox+5*0.45, oy+11*0.31, oz+0.18), mat=m1)
    torus("Opt50_Ring", 0.24, 0.04, (ox+5*0.45, oy+11*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_51(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt51_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt51_M2", THEME["cyan"], 5.0)
    box("Opt51_Box", (1.0, 1.0, 0.35), (ox+6*0.45, oy+12*0.31, oz+0.18), mat=m1)
    torus("Opt51_Ring", 0.24, 0.04, (ox+6*0.45, oy+12*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_52(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt52_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt52_M2", THEME["cyan"], 5.0)
    box("Opt52_Box", (1.0, 1.0, 0.35), (ox+7*0.45, oy+0*0.31, oz+0.18), mat=m1)
    torus("Opt52_Ring", 0.24, 0.04, (ox+7*0.45, oy+0*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_53(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt53_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt53_M2", THEME["cyan"], 5.0)
    box("Opt53_Box", (1.0, 1.0, 0.35), (ox+8*0.45, oy+1*0.31, oz+0.18), mat=m1)
    torus("Opt53_Ring", 0.24, 0.04, (ox+8*0.45, oy+1*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_54(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt54_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt54_M2", THEME["cyan"], 5.0)
    box("Opt54_Box", (1.0, 1.0, 0.35), (ox+0*0.45, oy+2*0.31, oz+0.18), mat=m1)
    torus("Opt54_Ring", 0.24, 0.04, (ox+0*0.45, oy+2*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_55(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt55_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt55_M2", THEME["cyan"], 5.0)
    box("Opt55_Box", (1.0, 1.0, 0.35), (ox+1*0.45, oy+3*0.31, oz+0.18), mat=m1)
    torus("Opt55_Ring", 0.24, 0.04, (ox+1*0.45, oy+3*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_56(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt56_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt56_M2", THEME["cyan"], 5.0)
    box("Opt56_Box", (1.0, 1.0, 0.35), (ox+2*0.45, oy+4*0.31, oz+0.18), mat=m1)
    torus("Opt56_Ring", 0.24, 0.04, (ox+2*0.45, oy+4*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_57(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt57_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt57_M2", THEME["cyan"], 5.0)
    box("Opt57_Box", (1.0, 1.0, 0.35), (ox+3*0.45, oy+5*0.31, oz+0.18), mat=m1)
    torus("Opt57_Ring", 0.24, 0.04, (ox+3*0.45, oy+5*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_58(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt58_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt58_M2", THEME["cyan"], 5.0)
    box("Opt58_Box", (1.0, 1.0, 0.35), (ox+4*0.45, oy+6*0.31, oz+0.18), mat=m1)
    torus("Opt58_Ring", 0.24, 0.04, (ox+4*0.45, oy+6*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_59(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt59_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt59_M2", THEME["cyan"], 5.0)
    box("Opt59_Box", (1.0, 1.0, 0.35), (ox+5*0.45, oy+7*0.31, oz+0.18), mat=m1)
    torus("Opt59_Ring", 0.24, 0.04, (ox+5*0.45, oy+7*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_60(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt60_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt60_M2", THEME["cyan"], 5.0)
    box("Opt60_Box", (1.0, 1.0, 0.35), (ox+6*0.45, oy+8*0.31, oz+0.18), mat=m1)
    torus("Opt60_Ring", 0.24, 0.04, (ox+6*0.45, oy+8*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_61(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt61_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt61_M2", THEME["cyan"], 5.0)
    box("Opt61_Box", (1.0, 1.0, 0.35), (ox+7*0.45, oy+9*0.31, oz+0.18), mat=m1)
    torus("Opt61_Ring", 0.24, 0.04, (ox+7*0.45, oy+9*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_62(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt62_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt62_M2", THEME["cyan"], 5.0)
    box("Opt62_Box", (1.0, 1.0, 0.35), (ox+8*0.45, oy+10*0.31, oz+0.18), mat=m1)
    torus("Opt62_Ring", 0.24, 0.04, (ox+8*0.45, oy+10*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_63(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt63_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt63_M2", THEME["cyan"], 5.0)
    box("Opt63_Box", (1.0, 1.0, 0.35), (ox+0*0.45, oy+11*0.31, oz+0.18), mat=m1)
    torus("Opt63_Ring", 0.24, 0.04, (ox+0*0.45, oy+11*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_64(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt64_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt64_M2", THEME["cyan"], 5.0)
    box("Opt64_Box", (1.0, 1.0, 0.35), (ox+1*0.45, oy+12*0.31, oz+0.18), mat=m1)
    torus("Opt64_Ring", 0.24, 0.04, (ox+1*0.45, oy+12*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_65(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt65_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt65_M2", THEME["cyan"], 5.0)
    box("Opt65_Box", (1.0, 1.0, 0.35), (ox+2*0.45, oy+0*0.31, oz+0.18), mat=m1)
    torus("Opt65_Ring", 0.24, 0.04, (ox+2*0.45, oy+0*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_66(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt66_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt66_M2", THEME["cyan"], 5.0)
    box("Opt66_Box", (1.0, 1.0, 0.35), (ox+3*0.45, oy+1*0.31, oz+0.18), mat=m1)
    torus("Opt66_Ring", 0.24, 0.04, (ox+3*0.45, oy+1*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_67(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt67_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt67_M2", THEME["cyan"], 5.0)
    box("Opt67_Box", (1.0, 1.0, 0.35), (ox+4*0.45, oy+2*0.31, oz+0.18), mat=m1)
    torus("Opt67_Ring", 0.24, 0.04, (ox+4*0.45, oy+2*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_68(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt68_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt68_M2", THEME["cyan"], 5.0)
    box("Opt68_Box", (1.0, 1.0, 0.35), (ox+5*0.45, oy+3*0.31, oz+0.18), mat=m1)
    torus("Opt68_Ring", 0.24, 0.04, (ox+5*0.45, oy+3*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_69(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt69_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt69_M2", THEME["cyan"], 5.0)
    box("Opt69_Box", (1.0, 1.0, 0.35), (ox+6*0.45, oy+4*0.31, oz+0.18), mat=m1)
    torus("Opt69_Ring", 0.24, 0.04, (ox+6*0.45, oy+4*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_70(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt70_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt70_M2", THEME["cyan"], 5.0)
    box("Opt70_Box", (1.0, 1.0, 0.35), (ox+7*0.45, oy+5*0.31, oz+0.18), mat=m1)
    torus("Opt70_Ring", 0.24, 0.04, (ox+7*0.45, oy+5*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_71(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt71_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt71_M2", THEME["cyan"], 5.0)
    box("Opt71_Box", (1.0, 1.0, 0.35), (ox+8*0.45, oy+6*0.31, oz+0.18), mat=m1)
    torus("Opt71_Ring", 0.24, 0.04, (ox+8*0.45, oy+6*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_72(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt72_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt72_M2", THEME["cyan"], 5.0)
    box("Opt72_Box", (1.0, 1.0, 0.35), (ox+0*0.45, oy+7*0.31, oz+0.18), mat=m1)
    torus("Opt72_Ring", 0.24, 0.04, (ox+0*0.45, oy+7*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_73(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt73_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt73_M2", THEME["cyan"], 5.0)
    box("Opt73_Box", (1.0, 1.0, 0.35), (ox+1*0.45, oy+8*0.31, oz+0.18), mat=m1)
    torus("Opt73_Ring", 0.24, 0.04, (ox+1*0.45, oy+8*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_74(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt74_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt74_M2", THEME["cyan"], 5.0)
    box("Opt74_Box", (1.0, 1.0, 0.35), (ox+2*0.45, oy+9*0.31, oz+0.18), mat=m1)
    torus("Opt74_Ring", 0.24, 0.04, (ox+2*0.45, oy+9*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_75(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt75_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt75_M2", THEME["cyan"], 5.0)
    box("Opt75_Box", (1.0, 1.0, 0.35), (ox+3*0.45, oy+10*0.31, oz+0.18), mat=m1)
    torus("Opt75_Ring", 0.24, 0.04, (ox+3*0.45, oy+10*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_76(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt76_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt76_M2", THEME["cyan"], 5.0)
    box("Opt76_Box", (1.0, 1.0, 0.35), (ox+4*0.45, oy+11*0.31, oz+0.18), mat=m1)
    torus("Opt76_Ring", 0.24, 0.04, (ox+4*0.45, oy+11*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_77(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt77_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt77_M2", THEME["cyan"], 5.0)
    box("Opt77_Box", (1.0, 1.0, 0.35), (ox+5*0.45, oy+12*0.31, oz+0.18), mat=m1)
    torus("Opt77_Ring", 0.24, 0.04, (ox+5*0.45, oy+12*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_78(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt78_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt78_M2", THEME["cyan"], 5.0)
    box("Opt78_Box", (1.0, 1.0, 0.35), (ox+6*0.45, oy+0*0.31, oz+0.18), mat=m1)
    torus("Opt78_Ring", 0.24, 0.04, (ox+6*0.45, oy+0*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_79(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt79_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt79_M2", THEME["cyan"], 5.0)
    box("Opt79_Box", (1.0, 1.0, 0.35), (ox+7*0.45, oy+1*0.31, oz+0.18), mat=m1)
    torus("Opt79_Ring", 0.24, 0.04, (ox+7*0.45, oy+1*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_80(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt80_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt80_M2", THEME["cyan"], 5.0)
    box("Opt80_Box", (1.0, 1.0, 0.35), (ox+8*0.45, oy+2*0.31, oz+0.18), mat=m1)
    torus("Opt80_Ring", 0.24, 0.04, (ox+8*0.45, oy+2*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_81(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt81_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt81_M2", THEME["cyan"], 5.0)
    box("Opt81_Box", (1.0, 1.0, 0.35), (ox+0*0.45, oy+3*0.31, oz+0.18), mat=m1)
    torus("Opt81_Ring", 0.24, 0.04, (ox+0*0.45, oy+3*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_82(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt82_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt82_M2", THEME["cyan"], 5.0)
    box("Opt82_Box", (1.0, 1.0, 0.35), (ox+1*0.45, oy+4*0.31, oz+0.18), mat=m1)
    torus("Opt82_Ring", 0.24, 0.04, (ox+1*0.45, oy+4*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_83(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt83_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt83_M2", THEME["cyan"], 5.0)
    box("Opt83_Box", (1.0, 1.0, 0.35), (ox+2*0.45, oy+5*0.31, oz+0.18), mat=m1)
    torus("Opt83_Ring", 0.24, 0.04, (ox+2*0.45, oy+5*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_84(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt84_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt84_M2", THEME["cyan"], 5.0)
    box("Opt84_Box", (1.0, 1.0, 0.35), (ox+3*0.45, oy+6*0.31, oz+0.18), mat=m1)
    torus("Opt84_Ring", 0.24, 0.04, (ox+3*0.45, oy+6*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_85(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt85_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt85_M2", THEME["cyan"], 5.0)
    box("Opt85_Box", (1.0, 1.0, 0.35), (ox+4*0.45, oy+7*0.31, oz+0.18), mat=m1)
    torus("Opt85_Ring", 0.24, 0.04, (ox+4*0.45, oy+7*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_86(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt86_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt86_M2", THEME["cyan"], 5.0)
    box("Opt86_Box", (1.0, 1.0, 0.35), (ox+5*0.45, oy+8*0.31, oz+0.18), mat=m1)
    torus("Opt86_Ring", 0.24, 0.04, (ox+5*0.45, oy+8*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_87(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt87_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt87_M2", THEME["cyan"], 5.0)
    box("Opt87_Box", (1.0, 1.0, 0.35), (ox+6*0.45, oy+9*0.31, oz+0.18), mat=m1)
    torus("Opt87_Ring", 0.24, 0.04, (ox+6*0.45, oy+9*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_88(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt88_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt88_M2", THEME["cyan"], 5.0)
    box("Opt88_Box", (1.0, 1.0, 0.35), (ox+7*0.45, oy+10*0.31, oz+0.18), mat=m1)
    torus("Opt88_Ring", 0.24, 0.04, (ox+7*0.45, oy+10*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_89(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt89_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt89_M2", THEME["cyan"], 5.0)
    box("Opt89_Box", (1.0, 1.0, 0.35), (ox+8*0.45, oy+11*0.31, oz+0.18), mat=m1)
    torus("Opt89_Ring", 0.24, 0.04, (ox+8*0.45, oy+11*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_90(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt90_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt90_M2", THEME["cyan"], 5.0)
    box("Opt90_Box", (1.0, 1.0, 0.35), (ox+0*0.45, oy+12*0.31, oz+0.18), mat=m1)
    torus("Opt90_Ring", 0.24, 0.04, (ox+0*0.45, oy+12*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_91(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt91_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt91_M2", THEME["cyan"], 5.0)
    box("Opt91_Box", (1.0, 1.0, 0.35), (ox+1*0.45, oy+0*0.31, oz+0.18), mat=m1)
    torus("Opt91_Ring", 0.24, 0.04, (ox+1*0.45, oy+0*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_92(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt92_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt92_M2", THEME["cyan"], 5.0)
    box("Opt92_Box", (1.0, 1.0, 0.35), (ox+2*0.45, oy+1*0.31, oz+0.18), mat=m1)
    torus("Opt92_Ring", 0.24, 0.04, (ox+2*0.45, oy+1*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_93(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt93_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt93_M2", THEME["cyan"], 5.0)
    box("Opt93_Box", (1.0, 1.0, 0.35), (ox+3*0.45, oy+2*0.31, oz+0.18), mat=m1)
    torus("Opt93_Ring", 0.24, 0.04, (ox+3*0.45, oy+2*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_94(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt94_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt94_M2", THEME["cyan"], 5.0)
    box("Opt94_Box", (1.0, 1.0, 0.35), (ox+4*0.45, oy+3*0.31, oz+0.18), mat=m1)
    torus("Opt94_Ring", 0.24, 0.04, (ox+4*0.45, oy+3*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_95(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt95_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt95_M2", THEME["cyan"], 5.0)
    box("Opt95_Box", (1.0, 1.0, 0.35), (ox+5*0.45, oy+4*0.31, oz+0.18), mat=m1)
    torus("Opt95_Ring", 0.24, 0.04, (ox+5*0.45, oy+4*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_96(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt96_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt96_M2", THEME["cyan"], 5.0)
    box("Opt96_Box", (1.0, 1.0, 0.35), (ox+6*0.45, oy+5*0.31, oz+0.18), mat=m1)
    torus("Opt96_Ring", 0.24, 0.04, (ox+6*0.45, oy+5*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_97(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt97_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt97_M2", THEME["cyan"], 5.0)
    box("Opt97_Box", (1.0, 1.0, 0.35), (ox+7*0.45, oy+6*0.31, oz+0.18), mat=m1)
    torus("Opt97_Ring", 0.24, 0.04, (ox+7*0.45, oy+6*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_98(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt98_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt98_M2", THEME["cyan"], 5.0)
    box("Opt98_Box", (1.0, 1.0, 0.35), (ox+8*0.45, oy+7*0.31, oz+0.18), mat=m1)
    torus("Opt98_Ring", 0.24, 0.04, (ox+8*0.45, oy+7*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_99(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt99_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt99_M2", THEME["cyan"], 5.0)
    box("Opt99_Box", (1.0, 1.0, 0.35), (ox+0*0.45, oy+8*0.31, oz+0.18), mat=m1)
    torus("Opt99_Ring", 0.24, 0.04, (ox+0*0.45, oy+8*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_100(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt100_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt100_M2", THEME["cyan"], 5.0)
    box("Opt100_Box", (1.0, 1.0, 0.35), (ox+1*0.45, oy+9*0.31, oz+0.18), mat=m1)
    torus("Opt100_Ring", 0.24, 0.04, (ox+1*0.45, oy+9*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_101(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt101_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt101_M2", THEME["cyan"], 5.0)
    box("Opt101_Box", (1.0, 1.0, 0.35), (ox+2*0.45, oy+10*0.31, oz+0.18), mat=m1)
    torus("Opt101_Ring", 0.24, 0.04, (ox+2*0.45, oy+10*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_102(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt102_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt102_M2", THEME["cyan"], 5.0)
    box("Opt102_Box", (1.0, 1.0, 0.35), (ox+3*0.45, oy+11*0.31, oz+0.18), mat=m1)
    torus("Opt102_Ring", 0.24, 0.04, (ox+3*0.45, oy+11*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_103(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt103_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt103_M2", THEME["cyan"], 5.0)
    box("Opt103_Box", (1.0, 1.0, 0.35), (ox+4*0.45, oy+12*0.31, oz+0.18), mat=m1)
    torus("Opt103_Ring", 0.24, 0.04, (ox+4*0.45, oy+12*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_104(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt104_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt104_M2", THEME["cyan"], 5.0)
    box("Opt104_Box", (1.0, 1.0, 0.35), (ox+5*0.45, oy+0*0.31, oz+0.18), mat=m1)
    torus("Opt104_Ring", 0.24, 0.04, (ox+5*0.45, oy+0*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_105(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt105_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt105_M2", THEME["cyan"], 5.0)
    box("Opt105_Box", (1.0, 1.0, 0.35), (ox+6*0.45, oy+1*0.31, oz+0.18), mat=m1)
    torus("Opt105_Ring", 0.24, 0.04, (ox+6*0.45, oy+1*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_106(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt106_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt106_M2", THEME["cyan"], 5.0)
    box("Opt106_Box", (1.0, 1.0, 0.35), (ox+7*0.45, oy+2*0.31, oz+0.18), mat=m1)
    torus("Opt106_Ring", 0.24, 0.04, (ox+7*0.45, oy+2*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_107(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt107_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt107_M2", THEME["cyan"], 5.0)
    box("Opt107_Box", (1.0, 1.0, 0.35), (ox+8*0.45, oy+3*0.31, oz+0.18), mat=m1)
    torus("Opt107_Ring", 0.24, 0.04, (ox+8*0.45, oy+3*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_108(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt108_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt108_M2", THEME["cyan"], 5.0)
    box("Opt108_Box", (1.0, 1.0, 0.35), (ox+0*0.45, oy+4*0.31, oz+0.18), mat=m1)
    torus("Opt108_Ring", 0.24, 0.04, (ox+0*0.45, oy+4*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_109(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt109_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt109_M2", THEME["cyan"], 5.0)
    box("Opt109_Box", (1.0, 1.0, 0.35), (ox+1*0.45, oy+5*0.31, oz+0.18), mat=m1)
    torus("Opt109_Ring", 0.24, 0.04, (ox+1*0.45, oy+5*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_110(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt110_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt110_M2", THEME["cyan"], 5.0)
    box("Opt110_Box", (1.0, 1.0, 0.35), (ox+2*0.45, oy+6*0.31, oz+0.18), mat=m1)
    torus("Opt110_Ring", 0.24, 0.04, (ox+2*0.45, oy+6*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_111(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt111_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt111_M2", THEME["cyan"], 5.0)
    box("Opt111_Box", (1.0, 1.0, 0.35), (ox+3*0.45, oy+7*0.31, oz+0.18), mat=m1)
    torus("Opt111_Ring", 0.24, 0.04, (ox+3*0.45, oy+7*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_112(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt112_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt112_M2", THEME["cyan"], 5.0)
    box("Opt112_Box", (1.0, 1.0, 0.35), (ox+4*0.45, oy+8*0.31, oz+0.18), mat=m1)
    torus("Opt112_Ring", 0.24, 0.04, (ox+4*0.45, oy+8*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_113(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt113_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt113_M2", THEME["cyan"], 5.0)
    box("Opt113_Box", (1.0, 1.0, 0.35), (ox+5*0.45, oy+9*0.31, oz+0.18), mat=m1)
    torus("Opt113_Ring", 0.24, 0.04, (ox+5*0.45, oy+9*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_114(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt114_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt114_M2", THEME["cyan"], 5.0)
    box("Opt114_Box", (1.0, 1.0, 0.35), (ox+6*0.45, oy+10*0.31, oz+0.18), mat=m1)
    torus("Opt114_Ring", 0.24, 0.04, (ox+6*0.45, oy+10*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_115(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt115_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt115_M2", THEME["cyan"], 5.0)
    box("Opt115_Box", (1.0, 1.0, 0.35), (ox+7*0.45, oy+11*0.31, oz+0.18), mat=m1)
    torus("Opt115_Ring", 0.24, 0.04, (ox+7*0.45, oy+11*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_116(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt116_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt116_M2", THEME["cyan"], 5.0)
    box("Opt116_Box", (1.0, 1.0, 0.35), (ox+8*0.45, oy+12*0.31, oz+0.18), mat=m1)
    torus("Opt116_Ring", 0.24, 0.04, (ox+8*0.45, oy+12*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_117(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt117_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt117_M2", THEME["cyan"], 5.0)
    box("Opt117_Box", (1.0, 1.0, 0.35), (ox+0*0.45, oy+0*0.31, oz+0.18), mat=m1)
    torus("Opt117_Ring", 0.24, 0.04, (ox+0*0.45, oy+0*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_118(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt118_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt118_M2", THEME["cyan"], 5.0)
    box("Opt118_Box", (1.0, 1.0, 0.35), (ox+1*0.45, oy+1*0.31, oz+0.18), mat=m1)
    torus("Opt118_Ring", 0.24, 0.04, (ox+1*0.45, oy+1*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_119(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt119_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt119_M2", THEME["cyan"], 5.0)
    box("Opt119_Box", (1.0, 1.0, 0.35), (ox+2*0.45, oy+2*0.31, oz+0.18), mat=m1)
    torus("Opt119_Ring", 0.24, 0.04, (ox+2*0.45, oy+2*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_120(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt120_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt120_M2", THEME["cyan"], 5.0)
    box("Opt120_Box", (1.0, 1.0, 0.35), (ox+3*0.45, oy+3*0.31, oz+0.18), mat=m1)
    torus("Opt120_Ring", 0.24, 0.04, (ox+3*0.45, oy+3*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_121(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt121_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt121_M2", THEME["cyan"], 5.0)
    box("Opt121_Box", (1.0, 1.0, 0.35), (ox+4*0.45, oy+4*0.31, oz+0.18), mat=m1)
    torus("Opt121_Ring", 0.24, 0.04, (ox+4*0.45, oy+4*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_122(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt122_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt122_M2", THEME["cyan"], 5.0)
    box("Opt122_Box", (1.0, 1.0, 0.35), (ox+5*0.45, oy+5*0.31, oz+0.18), mat=m1)
    torus("Opt122_Ring", 0.24, 0.04, (ox+5*0.45, oy+5*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_123(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt123_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt123_M2", THEME["cyan"], 5.0)
    box("Opt123_Box", (1.0, 1.0, 0.35), (ox+6*0.45, oy+6*0.31, oz+0.18), mat=m1)
    torus("Opt123_Ring", 0.24, 0.04, (ox+6*0.45, oy+6*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_124(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt124_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt124_M2", THEME["cyan"], 5.0)
    box("Opt124_Box", (1.0, 1.0, 0.35), (ox+7*0.45, oy+7*0.31, oz+0.18), mat=m1)
    torus("Opt124_Ring", 0.24, 0.04, (ox+7*0.45, oy+7*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_125(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt125_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt125_M2", THEME["cyan"], 5.0)
    box("Opt125_Box", (1.0, 1.0, 0.35), (ox+8*0.45, oy+8*0.31, oz+0.18), mat=m1)
    torus("Opt125_Ring", 0.24, 0.04, (ox+8*0.45, oy+8*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_126(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt126_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt126_M2", THEME["cyan"], 5.0)
    box("Opt126_Box", (1.0, 1.0, 0.35), (ox+0*0.45, oy+9*0.31, oz+0.18), mat=m1)
    torus("Opt126_Ring", 0.24, 0.04, (ox+0*0.45, oy+9*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_127(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt127_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt127_M2", THEME["cyan"], 5.0)
    box("Opt127_Box", (1.0, 1.0, 0.35), (ox+1*0.45, oy+10*0.31, oz+0.18), mat=m1)
    torus("Opt127_Ring", 0.24, 0.04, (ox+1*0.45, oy+10*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_128(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt128_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt128_M2", THEME["cyan"], 5.0)
    box("Opt128_Box", (1.0, 1.0, 0.35), (ox+2*0.45, oy+11*0.31, oz+0.18), mat=m1)
    torus("Opt128_Ring", 0.24, 0.04, (ox+2*0.45, oy+11*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_129(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt129_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt129_M2", THEME["cyan"], 5.0)
    box("Opt129_Box", (1.0, 1.0, 0.35), (ox+3*0.45, oy+12*0.31, oz+0.18), mat=m1)
    torus("Opt129_Ring", 0.24, 0.04, (ox+3*0.45, oy+12*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_130(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt130_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt130_M2", THEME["cyan"], 5.0)
    box("Opt130_Box", (1.0, 1.0, 0.35), (ox+4*0.45, oy+0*0.31, oz+0.18), mat=m1)
    torus("Opt130_Ring", 0.24, 0.04, (ox+4*0.45, oy+0*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_131(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt131_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt131_M2", THEME["cyan"], 5.0)
    box("Opt131_Box", (1.0, 1.0, 0.35), (ox+5*0.45, oy+1*0.31, oz+0.18), mat=m1)
    torus("Opt131_Ring", 0.24, 0.04, (ox+5*0.45, oy+1*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_132(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt132_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt132_M2", THEME["cyan"], 5.0)
    box("Opt132_Box", (1.0, 1.0, 0.35), (ox+6*0.45, oy+2*0.31, oz+0.18), mat=m1)
    torus("Opt132_Ring", 0.24, 0.04, (ox+6*0.45, oy+2*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_133(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt133_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt133_M2", THEME["cyan"], 5.0)
    box("Opt133_Box", (1.0, 1.0, 0.35), (ox+7*0.45, oy+3*0.31, oz+0.18), mat=m1)
    torus("Opt133_Ring", 0.24, 0.04, (ox+7*0.45, oy+3*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_134(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt134_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt134_M2", THEME["cyan"], 5.0)
    box("Opt134_Box", (1.0, 1.0, 0.35), (ox+8*0.45, oy+4*0.31, oz+0.18), mat=m1)
    torus("Opt134_Ring", 0.24, 0.04, (ox+8*0.45, oy+4*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_135(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt135_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt135_M2", THEME["cyan"], 5.0)
    box("Opt135_Box", (1.0, 1.0, 0.35), (ox+0*0.45, oy+5*0.31, oz+0.18), mat=m1)
    torus("Opt135_Ring", 0.24, 0.04, (ox+0*0.45, oy+5*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_136(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt136_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt136_M2", THEME["cyan"], 5.0)
    box("Opt136_Box", (1.0, 1.0, 0.35), (ox+1*0.45, oy+6*0.31, oz+0.18), mat=m1)
    torus("Opt136_Ring", 0.24, 0.04, (ox+1*0.45, oy+6*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_137(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt137_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt137_M2", THEME["cyan"], 5.0)
    box("Opt137_Box", (1.0, 1.0, 0.35), (ox+2*0.45, oy+7*0.31, oz+0.18), mat=m1)
    torus("Opt137_Ring", 0.24, 0.04, (ox+2*0.45, oy+7*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_138(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt138_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt138_M2", THEME["cyan"], 5.0)
    box("Opt138_Box", (1.0, 1.0, 0.35), (ox+3*0.45, oy+8*0.31, oz+0.18), mat=m1)
    torus("Opt138_Ring", 0.24, 0.04, (ox+3*0.45, oy+8*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_139(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt139_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt139_M2", THEME["cyan"], 5.0)
    box("Opt139_Box", (1.0, 1.0, 0.35), (ox+4*0.45, oy+9*0.31, oz+0.18), mat=m1)
    torus("Opt139_Ring", 0.24, 0.04, (ox+4*0.45, oy+9*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_140(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt140_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt140_M2", THEME["cyan"], 5.0)
    box("Opt140_Box", (1.0, 1.0, 0.35), (ox+5*0.45, oy+10*0.31, oz+0.18), mat=m1)
    torus("Opt140_Ring", 0.24, 0.04, (ox+5*0.45, oy+10*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_141(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt141_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt141_M2", THEME["cyan"], 5.0)
    box("Opt141_Box", (1.0, 1.0, 0.35), (ox+6*0.45, oy+11*0.31, oz+0.18), mat=m1)
    torus("Opt141_Ring", 0.24, 0.04, (ox+6*0.45, oy+11*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_142(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt142_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt142_M2", THEME["cyan"], 5.0)
    box("Opt142_Box", (1.0, 1.0, 0.35), (ox+7*0.45, oy+12*0.31, oz+0.18), mat=m1)
    torus("Opt142_Ring", 0.24, 0.04, (ox+7*0.45, oy+12*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_143(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt143_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt143_M2", THEME["cyan"], 5.0)
    box("Opt143_Box", (1.0, 1.0, 0.35), (ox+8*0.45, oy+0*0.31, oz+0.18), mat=m1)
    torus("Opt143_Ring", 0.24, 0.04, (ox+8*0.45, oy+0*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_144(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt144_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt144_M2", THEME["cyan"], 5.0)
    box("Opt144_Box", (1.0, 1.0, 0.35), (ox+0*0.45, oy+1*0.31, oz+0.18), mat=m1)
    torus("Opt144_Ring", 0.24, 0.04, (ox+0*0.45, oy+1*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_145(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt145_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt145_M2", THEME["cyan"], 5.0)
    box("Opt145_Box", (1.0, 1.0, 0.35), (ox+1*0.45, oy+2*0.31, oz+0.18), mat=m1)
    torus("Opt145_Ring", 0.24, 0.04, (ox+1*0.45, oy+2*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_146(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt146_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt146_M2", THEME["cyan"], 5.0)
    box("Opt146_Box", (1.0, 1.0, 0.35), (ox+2*0.45, oy+3*0.31, oz+0.18), mat=m1)
    torus("Opt146_Ring", 0.24, 0.04, (ox+2*0.45, oy+3*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_147(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt147_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt147_M2", THEME["cyan"], 5.0)
    box("Opt147_Box", (1.0, 1.0, 0.35), (ox+3*0.45, oy+4*0.31, oz+0.18), mat=m1)
    torus("Opt147_Ring", 0.24, 0.04, (ox+3*0.45, oy+4*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_148(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt148_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt148_M2", THEME["cyan"], 5.0)
    box("Opt148_Box", (1.0, 1.0, 0.35), (ox+4*0.45, oy+5*0.31, oz+0.18), mat=m1)
    torus("Opt148_Ring", 0.24, 0.04, (ox+4*0.45, oy+5*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_149(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt149_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt149_M2", THEME["cyan"], 5.0)
    box("Opt149_Box", (1.0, 1.0, 0.35), (ox+5*0.45, oy+6*0.31, oz+0.18), mat=m1)
    torus("Opt149_Ring", 0.24, 0.04, (ox+5*0.45, oy+6*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def optional_module_150(origin=(0,0,0)):
    ox, oy, oz = origin
    m1 = mat_pbr("Opt150_M1", (0.72,0.76,0.84,1), 0.36, 0.52)
    m2 = mat_emit("Opt150_M2", THEME["cyan"], 5.0)
    box("Opt150_Box", (1.0, 1.0, 0.35), (ox+6*0.45, oy+7*0.31, oz+0.18), mat=m1)
    torus("Opt150_Ring", 0.24, 0.04, (ox+6*0.45, oy+7*0.31, oz+0.54), rot=(math.radians(90),0,0), mat=m2)
    return True

def deploy_optional_modules(anchor=(0,-72,0), count=60):
    ax, ay, az = anchor
    for idx in range(1, count+1):
        fn = globals().get(f"optional_module_{idx}")
        if fn:
            col = idx % 10
            row = idx // 10
            fn((ax + col*2.0 - 10, ay + row*2.0 - 8, az + 0.1))

def export_glb(path=EXPORT_PATH):
    export_dir = os.path.dirname(path)
    if export_dir and not os.path.exists(export_dir):
        os.makedirs(export_dir, exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", export_apply=True, export_yup=True, export_animations=True)
    print("Exported GLB:", path)

def main():
    if not bpy.data.is_saved:
        print("Warning: .blend unsaved; exporting to temp.")
    build()
    deploy_optional_modules((0,-72,0), 60)
    export_glb(EXPORT_PATH)
    print("Overlay PNG:", OVERLAY_PATH)
    print("Done.")

if __name__ == "__main__":
    main()
