
from __future__ import annotations

from pathlib import Path
import json
import math
import numpy as np
import trimesh
from trimesh.transformations import rotation_matrix, translation_matrix
from trimesh.visual.material import PBRMaterial
from trimesh.visual.texture import TextureVisuals

ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / "frontend" / "public" / "models" / "uav" / "v1_1"
THUMB_DIR = MODEL_DIR / "thumbnails"
MODEL_DIR.mkdir(parents=True, exist_ok=True)
THUMB_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# PBR material system
# ---------------------------------------------------------------------------
def mat(name, rgba, metallic=0.0, roughness=0.5, emissive=None):
    r, g, b, a = rgba
    ef = None if emissive is None else emissive
    return PBRMaterial(
        name=name,
        baseColorFactor=[r/255, g/255, b/255, a/255],
        metallicFactor=metallic,
        roughnessFactor=roughness,
        emissiveFactor=ef,
        doubleSided=False,
    )

M = {
    "carbon": mat("CarbonFiber", (27, 31, 36, 255), 0.12, 0.32),
    "carbon_edge": mat("CarbonEdge", (11, 13, 16, 255), 0.18, 0.24),
    "black_metal": mat("BlackAnodizedAluminium", (22, 25, 29, 255), 0.88, 0.24),
    "dark_metal": mat("DarkMetal", (48, 54, 61, 255), 0.90, 0.22),
    "aluminium": mat("MachinedAluminium", (170, 178, 188, 255), 0.94, 0.18),
    "steel": mat("SteelFasteners", (128, 136, 145, 255), 0.95, 0.18),
    "red_anod": mat("RedAnodized", (145, 27, 31, 255), 0.82, 0.22),
    "blue_anod": mat("BlueAnodized", (31, 82, 158, 255), 0.82, 0.22),
    "copper": mat("Copper", (184, 87, 42, 255), 0.88, 0.23),
    "pcb": mat("PCBGreen", (18, 75, 52, 255), 0.20, 0.48),
    "pcb_black": mat("PCBBlack", (23, 28, 32, 255), 0.22, 0.42),
    "gold": mat("GoldContacts", (218, 165, 54, 255), 0.86, 0.20),
    "rubber": mat("Rubber", (18, 20, 22, 255), 0.02, 0.88),
    "plastic_black": mat("BlackPlastic", (28, 31, 35, 255), 0.02, 0.58),
    "plastic_white": mat("WhitePlastic", (219, 224, 229, 255), 0.02, 0.42),
    "battery_blue": mat("BatteryWrapBlue", (25, 73, 142, 255), 0.03, 0.40),
    "battery_darkblue": mat("BatteryWrapDarkBlue", (17, 52, 106, 255), 0.03, 0.40),
    "yellow": mat("ConnectorYellow", (233, 179, 34, 255), 0.04, 0.46),
    "red_wire": mat("RedWire", (182, 31, 37, 255), 0.02, 0.72),
    "black_wire": mat("BlackWire", (20, 22, 25, 255), 0.02, 0.74),
    "blue_wire": mat("BlueWire", (35, 95, 179, 255), 0.02, 0.72),
    "glass": mat("LensGlass", (13, 27, 45, 210), 0.10, 0.06),
    "ceramic": mat("CeramicAntenna", (223, 226, 221, 255), 0.04, 0.34),
    "label_white": mat("PrintedLabel", (237, 241, 246, 255), 0.00, 0.70),
    "label_blue": mat("BlueInk", (37, 95, 179, 255), 0.00, 0.60),
    "prop": mat("CarbonPropeller", (38, 42, 47, 255), 0.12, 0.28),
    "led_green": mat("GreenLED", (60, 220, 128, 255), 0.0, 0.15, emissive=[0.05, 0.55, 0.18]),
    "led_red": mat("RedLED", (240, 70, 70, 255), 0.0, 0.15, emissive=[0.65, 0.04, 0.03]),
}

def apply_mat(mesh: trimesh.Trimesh, material: PBRMaterial):
    mesh.visual = TextureVisuals(material=material)
    return mesh

def add(scene: trimesh.Scene, name: str, mesh: trimesh.Trimesh):
    scene.add_geometry(mesh, geom_name=name, node_name=name)

def box(ext, pos=(0, 0, 0), material=M["plastic_black"]):
    mesh = trimesh.creation.box(extents=ext)
    apply_mat(mesh, material)
    mesh.apply_translation(pos)
    return mesh

def cyl(radius, height, pos=(0,0,0), material=M["aluminium"], axis="y", sections=40):
    mesh = trimesh.creation.cylinder(radius=radius, height=height, sections=sections)
    apply_mat(mesh, material)
    if axis == "y":
        mesh.apply_transform(rotation_matrix(-math.pi/2, [1,0,0]))
    elif axis == "x":
        mesh.apply_transform(rotation_matrix(math.pi/2, [0,1,0]))
    # z is native
    mesh.apply_translation(pos)
    return mesh

def sphere(radius, pos=(0,0,0), material=M["plastic_black"], subdivisions=2):
    mesh = trimesh.creation.icosphere(subdivisions=subdivisions, radius=radius)
    apply_mat(mesh, material)
    mesh.apply_translation(pos)
    return mesh

def torus(major, minor, pos=(0,0,0), material=M["aluminium"], axis="y", major_sections=40, minor_sections=12):
    mesh = trimesh.creation.torus(
        major_radius=major, minor_radius=minor,
        major_sections=major_sections, minor_sections=minor_sections
    )
    apply_mat(mesh, material)
    if axis == "y":
        mesh.apply_transform(rotation_matrix(math.pi/2, [1,0,0]))
    elif axis == "x":
        mesh.apply_transform(rotation_matrix(math.pi/2, [0,1,0]))
    mesh.apply_translation(pos)
    return mesh

def cyl_between(p0, p1, radius, material=M["carbon"], sections=22):
    p0 = np.asarray(p0, float); p1 = np.asarray(p1, float)
    v = p1 - p0
    h = float(np.linalg.norm(v))
    if h < 1e-8:
        return sphere(radius, p0, material, 1)
    mesh = trimesh.creation.cylinder(radius=radius, height=h, sections=sections)
    apply_mat(mesh, material)
    T = trimesh.geometry.align_vectors([0,0,1], v/h)
    mesh.apply_transform(T)
    mesh.apply_translation((p0+p1)/2)
    return mesh

def rounded_wire(points, radius, material, sections=12):
    scene = trimesh.Scene()
    points = [np.asarray(p, float) for p in points]
    for i in range(len(points)-1):
        add(scene, f"seg_{i}", cyl_between(points[i], points[i+1], radius, material, sections))
    for i, p in enumerate(points[1:-1], start=1):
        add(scene, f"joint_{i}", sphere(radius*1.05, p, material, 1))
    return scene

def add_screw(scene, name, pos, r=0.0023, h=0.0035, axis="y"):
    add(scene, name, cyl(r, h, pos, M["steel"], axis=axis, sections=20))
    # dark cap recess gives the screw head visible structure
    px, py, pz = pos
    if axis == "y":
        add(scene, name+"_recess", box((r*1.25, 0.0008, r*0.36), (px, py+h*0.50, pz), M["carbon_edge"]))

def add_pin_header(scene, prefix, start, count=6, spacing=0.00254, axis="x"):
    sx, sy, sz = start
    for i in range(count):
        offset = (i - (count-1)/2)*spacing
        if axis == "x":
            pos = (sx+offset, sy, sz)
        else:
            pos = (sx, sy, sz+offset)
        add(scene, f"{prefix}_{i}", box((0.0011,0.0045,0.0011), pos, M["gold"]))

def copy_scene(dst: trimesh.Scene, src: trimesh.Scene, prefix: str, T=None):
    T = np.eye(4) if T is None else np.asarray(T)
    for node in src.graph.nodes_geometry:
        trans, gname = src.graph[node]
        geom = src.geometry[gname].copy()
        geom.apply_transform(T @ trans)
        add(dst, prefix + node, geom)

# ---------------------------------------------------------------------------
# High-fidelity parts
# ---------------------------------------------------------------------------

def build_frame(diagonal=0.65, landing=True, detail=2):
    s = trimesh.Scene()
    scale = diagonal / 0.65
    plate_x, plate_z = .225*scale, .182*scale

    # carbon sandwich plates
    add(s, "bottom_plate", box((plate_x,.006,plate_z),(0,.008,0),M["carbon"]))
    add(s, "bottom_edge", box((plate_x*.96,.0012,plate_z*.96),(0,.0116,0),M["carbon_edge"]))
    add(s, "top_plate", box((plate_x*.88,.0055,plate_z*.90),(0,.062*scale,0),M["carbon"]))
    add(s, "battery_tray", box((.175*scale,.004,.080*scale),(-.032*scale,-.036*scale,0),M["carbon"]))
    # battery anti-slip pad and straps
    add(s, "battery_pad", box((.145*scale,.002,.067*scale),(-.032*scale,-.039*scale,0),M["rubber"]))
    for x in (-.062,.010):
        add(s, f"battery_strap_{x}", box((.020*scale,.004,.095*scale),(x*scale,-.031*scale,0),M["red_anod"]))

    # standoffs and fasteners
    for xi, x in enumerate((-plate_x*.34, plate_x*.34)):
        for zi, z in enumerate((-plate_z*.31, plate_z*.31)):
            add(s, f"standoff_{xi}_{zi}", cyl(.0046*scale,.049*scale,(x,.035*scale,z),M["red_anod"],sections=28))
            add_screw(s, f"screw_top_{xi}_{zi}", (x,.066*scale,z), r=.0025*scale, h=.003*scale)
            add_screw(s, f"screw_bottom_{xi}_{zi}", (x,.004*scale,z), r=.0025*scale, h=.003*scale)

    offset = diagonal/2/math.sqrt(2)
    mpos = {
        "M1": ( offset,.067*scale,-offset),
        "M2": ( offset,.067*scale, offset),
        "M3": (-offset,.067*scale, offset),
        "M4": (-offset,.067*scale,-offset),
    }
    for name, p in mpos.items():
        sx=(.052 if p[0]>0 else -.052)*scale
        sz=(.042 if p[2]>0 else -.042)*scale
        # round carbon arm
        add(s, f"arm_{name}", cyl_between((sx,.052*scale,sz),(p[0],p[1]-.005*scale,p[2]),.0118*scale,M["carbon"],28))
        # root clamp
        cp = np.asarray([p[0],p[1],p[2]])*.34
        cp[1]=.053*scale
        add(s, f"root_clamp_{name}", cyl(.0165*scale,.021*scale,cp,M["red_anod"],axis="x" if abs(p[2])>abs(p[0]) else "z",sections=28))
        # motor plate
        add(s, f"motor_plate_{name}", cyl(.0345*scale,.006*scale,p,M["carbon"],sections=44))
        # motor plate center / screw pattern visual
        add(s, f"motor_center_{name}", cyl(.010*scale,.0072*scale,(p[0],p[1]+.0005*scale,p[2]),M["dark_metal"],sections=32))
        for a in (0, math.pi/2, math.pi, 3*math.pi/2):
            rr=.0235*scale
            px=p[0]+rr*math.cos(a); pz=p[2]+rr*math.sin(a)
            add_screw(s, f"motor_screw_{name}_{a:.2f}", (px,p[1]+.0042*scale,pz), r=.0019*scale,h=.0025*scale)

    # top electronics rails
    for z in (-.055*scale,.055*scale):
        add(s, f"electronics_rail_{z}", box((.130*scale,.005,.008*scale),(0,.072*scale,z),M["black_metal"]))

    if landing:
        rail_z=.103*scale
        y0=.006*scale; y1=-.150*scale
        foot_x=.145*scale
        for ix, x in enumerate((.060,-.060)):
            for iz, z in enumerate((-.074,.074)):
                xe=x*1.72; ze=math.copysign(rail_z,z)
                add(s, f"leg_{ix}_{iz}", cyl_between((x*scale,y0,z*scale),(xe,y1,ze),.0062*scale,M["carbon"],20))
                add(s, f"leg_joint_{ix}_{iz}", cyl(.010*scale,.014*scale,(x*scale,-.010*scale,z*scale),M["red_anod"],axis="x",sections=24))
        add(s, "rail_left", cyl_between((foot_x,y1,-rail_z),(-foot_x,y1,-rail_z),.007*scale,M["carbon"],24))
        add(s, "rail_right", cyl_between((foot_x,y1,rail_z),(-foot_x,y1,rail_z),.007*scale,M["carbon"],24))
        for x in (-foot_x*.88, foot_x*.88):
            add(s, f"foot_l_{x}", cyl(.010*scale,.018*scale,(x,y1,-rail_z),M["rubber"],axis="x",sections=20))
            add(s, f"foot_r_{x}", cyl(.010*scale,.018*scale,(x,y1, rail_z),M["rubber"],axis="x",sections=20))

    return s

def build_motor(radius=.030, height=.054, accent="red", detail=2):
    s=trimesh.Scene()
    accent_mat = M["red_anod"] if accent=="red" else M["blue_anod"]
    # base / bearing housing / stator
    add(s,"mount_base",cyl(radius*1.08,.006,(0,.003,0),M["black_metal"],sections=48))
    add(s,"bearing_housing",cyl(radius*.46,.020,(0,.015,0),M["aluminium"],sections=40))
    add(s,"stator_core",cyl(radius*.83,height*.34,(0,height*.27,0),M["dark_metal"],sections=48))
    # visible copper windings
    for i,a in enumerate(np.linspace(0,2*math.pi,12,endpoint=False)):
        rr=radius*.70
        x=rr*math.cos(a); z=rr*math.sin(a)
        add(s,f"coil_{i}",torus(radius*.075,radius*.027,(x,height*.29,z),M["copper"],axis="y",major_sections=18,minor_sections=8))
    # ventilated outrunner bell: two rings + twelve shell pillars.  This keeps
    # the copper winding visible instead of hiding it inside a solid cylinder.
    add(s,"bell_lower_ring",torus(radius*.91,radius*.045,(0,height*.405,0),accent_mat,axis="y",major_sections=48,minor_sections=10))
    add(s,"bell_upper_ring",torus(radius*.87,radius*.045,(0,height*.80,0),M["aluminium"],axis="y",major_sections=48,minor_sections=10))
    add(s,"bell_top",cyl(radius*.88,.006,(0,height*.835,0),M["black_metal"],sections=56))
    for i,a in enumerate(np.linspace(0,2*math.pi,12,endpoint=False)):
        rr=radius*.88
        x=rr*math.cos(a); z=rr*math.sin(a)
        pillar=box((radius*.16,height*.34,radius*.12),(x,height*.61,z),M["black_metal"])
        pillar.apply_transform(rotation_matrix(-a,[0,1,0],point=[x,height*.61,z]))
        add(s,f"bell_pillar_{i}",pillar)
    # top cap / shaft / prop adapter / nut
    add(s,"top_cap",cyl(radius*.58,.007,(0,height*.88,0),M["aluminium"],sections=48))
    add(s,"shaft",cyl(.0035,height*.43,(0,height*1.07,0),M["steel"],sections=32))
    add(s,"prop_adapter",cyl(.0075,.015,(0,height*1.17,0),M["aluminium"],sections=36))
    add(s,"prop_nut",cyl(.0068,.009,(0,height*1.29,0),accent_mat,sections=6))

    # four mounting ears + screws
    for i,a in enumerate((0, math.pi/2, math.pi, 3*math.pi/2)):
        x=radius*1.02*math.cos(a); z=radius*1.02*math.sin(a)
        ear=box((.016,.004,.010),(x,.002,z),M["black_metal"])
        ear.apply_transform(rotation_matrix(-a,[0,1,0],point=[x,.002,z]))
        add(s,f"ear_{i}",ear)
        add_screw(s,f"mount_screw_{i}",(x,.005,z),r=.0019,h=.0028)

    # three motor phase wires exiting aft
    wire_x = -radius*.72
    for i,(dz,material) in enumerate(((-.004,M["red_wire"]),(0,M["blue_wire"]),(.004,M["black_wire"]))):
        w=rounded_wire([(wire_x,.010,dz),(wire_x-.025,.004,dz),(wire_x-.050,-.005,dz*1.6)],.0015,material,10)
        copy_scene(s,w,f"phase_wire_{i}/")
    return s

def build_esc(length=.056,width=.027,accent="blue",detail=2):
    s=trimesh.Scene()
    accent_mat=M["blue_anod"] if accent=="blue" else M["red_anod"]
    # PCB and heatspreaders
    add(s,"pcb",box((length,.0038,width),(0,0,0),M["pcb_black"]))
    add(s,"bottom_pad",box((length*.90,.002,width*.84),(0,-.003,0),M["rubber"]))
    # MOSFET bank
    for ix,x in enumerate(np.linspace(-length*.30,length*.30,4)):
        for iz,z in enumerate((-width*.20,width*.20)):
            add(s,f"mosfet_{ix}_{iz}",box((.009,.0038,.006),(x,.004,z),M["dark_metal"]))
    # heatsink and fins
    add(s,"heatsink_base",box((length*.76,.004,width*.78),(0,.009,0),M["black_metal"]))
    for i,z in enumerate(np.linspace(-width*.32,width*.32,7)):
        add(s,f"fin_{i}",box((length*.70,.008,.0012),(0,.015,z),M["aluminium"]))
    # capacitors
    add(s,"cap_1",cyl(.0055,.015,(-length*.30,.013,-width*.29),M["black_metal"],axis="y",sections=28))
    add(s,"cap_2",cyl(.0055,.015,(-length*.30,.013,width*.29),M["black_metal"],axis="y",sections=28))
    # status LED
    add(s,"status_led",box((.004,.002,.004),(length*.31,.018,0),M["led_green"]))
    # phase wires
    for i,(z,material) in enumerate(((-width*.24,M["red_wire"]),(0,M["blue_wire"]),(width*.24,M["black_wire"]))):
        wire=rounded_wire([(length*.47,.004,z),(length*.65,.003,z),(length*.84,.000,z*1.15)],.00145,material,10)
        copy_scene(s,wire,f"motor_wire_{i}/")
    # battery leads
    for i,(z,material) in enumerate(((-width*.15,M["red_wire"]),(width*.15,M["black_wire"]))):
        wire=rounded_wire([(-length*.47,.002,z),(-length*.62,-.002,z),(-length*.80,-.006,z*1.25)],.0017,material,10)
        copy_scene(s,wire,f"power_wire_{i}/")
    # signal lead / connector
    copy_scene(s,rounded_wire([(-length*.10,-.002,width*.45),(-length*.22,-.006,width*.66)],.00075,M["plastic_white"],8),"signal/")
    add(s,"servo_plug",box((.010,.006,.006),(-length*.24,-.006,width*.71),M["plastic_black"]))
    return s

def twisted_blade(length, root_chord, tip_chord, thickness=.0048, direction=1, material=M["prop"], stations=12):
    # Blade grows along +X, chord across Z, thickness Y. Pitch twist tilts chord into Y.
    verts=[]
    faces=[]
    radii=np.linspace(length*.10,length,stations)
    for si,r in enumerate(radii):
        t=(r-radii[0])/(radii[-1]-radii[0])
        chord=root_chord*(1-t)+tip_chord*t
        pitch=math.radians((23*(1-t)+7*t)*direction)
        sweep=0.012*math.sin(t*math.pi)
        for surface in (-1,1):
            for edge in (-1,1):
                z=edge*chord/2
                y=surface*thickness/2
                # rotate chord/thickness about local X
                yy=y*math.cos(pitch)-z*math.sin(pitch)
                zz=y*math.sin(pitch)+z*math.cos(pitch)
                verts.append([r, yy, zz+sweep*edge])
    # 4 verts / station: [-surf,-edge],[-surf,+edge],[+surf,-edge],[+surf,+edge]
    def idx(si,surf,edge):
        return si*4 + surf*2 + edge
    for si in range(stations-1):
        # top and bottom
        for surf in (0,1):
            a=idx(si,surf,0); b=idx(si,surf,1); c=idx(si+1,surf,1); d=idx(si+1,surf,0)
            faces += [[a,b,c],[a,c,d]]
        # leading/trailing edges
        for edge in (0,1):
            a=idx(si,0,edge); b=idx(si+1,0,edge); c=idx(si+1,1,edge); d=idx(si,1,edge)
            faces += [[a,b,c],[a,c,d]]
    # caps
    faces += [[0,2,3],[0,3,1]]
    n=(stations-1)*4
    faces += [[n,n+1,n+3],[n,n+3,n+2]]
    mesh=trimesh.Trimesh(vertices=np.asarray(verts),faces=np.asarray(faces),process=False)
    apply_mat(mesh,material)
    return mesh

def build_prop(diameter_in=15.0,direction="ccw",detail=2):
    s=trimesh.Scene()
    sign=1 if direction=="ccw" else -1
    radius=diameter_in*0.0254/2
    add(s,"hub_lower",cyl(.0175,.009,(0,0,0),M["black_metal"],sections=44))
    add(s,"hub_ring",torus(.013,.003,(0,.005,0),M["aluminium"],axis="y",major_sections=40,minor_sections=10))
    add(s,"hub_cap",cyl(.0105,.009,(0,.011,0),M["dark_metal"],sections=40))
    # two twisted, slightly swept blades
    base=twisted_blade(radius*.94,radius*.22,radius*.085,.0048 if diameter_in>=15 else .0043,sign,M["prop"],14)
    for idx,angle in enumerate((0,math.pi)):
        b=base.copy()
        b.apply_transform(rotation_matrix(angle,[0,1,0]))
        add(s,f"blade_{idx}",b)
    # center nut/washer
    add(s,"washer",cyl(.008,.0025,(0,.017,0),M["steel"],sections=32))
    add(s,"nut",cyl(.0065,.006,(0,.021,0),M["aluminium"],sections=6))
    return s

def build_battery(length=.165,width=.070,height=.060,dark=False,detail=2):
    s=trimesh.Scene()
    body=M["battery_darkblue"] if dark else M["battery_blue"]
    # subtle cell rib structure under shrink wrap
    add(s,"body",box((length,height,width),(0,0,0),body))
    for i,x in enumerate(np.linspace(-length*.39,length*.39,5)):
        add(s,f"cell_rib_{i}",box((.0022,height*1.01,width*1.012),(x,0,0),M["blue_anod"]))
    add(s,"front_cap",box((.010,height*1.025,width*1.025),(length/2,0,0),M["rubber"]))
    add(s,"rear_cap",box((.010,height*1.025,width*1.025),(-length/2,0,0),M["rubber"]))
    # straps
    for i,x in enumerate((-length*.24,length*.24)):
        add(s,f"strap_{i}",box((.024,height*1.06,width*1.08),(x,0,0),M["rubber"]))
        add(s,f"strap_tab_{i}",box((.018,.006,.018),(x,height*.55,width*.47),M["red_anod"]))
    # top label layers
    add(s,"label",box((length*.48,.0015,width*.64),(.012,height/2+.001,0),M["label_white"]))
    add(s,"label_stripe",box((length*.34,.0008,width*.09),(.012,height/2+.002,length*0),M["label_blue"]))
    # balance connector
    add(s,"balance_header",box((.020,.010,.010),(-length*.43,height*.39,-width*.30),M["plastic_white"]))
    for i in range(7):
        add(s,f"balance_pin_{i}",box((.0012,.003,.0012),(-length*.43+(i-3)*.0025,height*.445,-width*.30),M["gold"]))
    # power cables and XT90
    copy_scene(s,rounded_wire([(-length*.42,height*.18,width*.27),(-length*.58,height*.34,width*.38),(-length*.70,height*.42,width*.42)],.0032,M["red_wire"],14),"wire_red/")
    copy_scene(s,rounded_wire([(-length*.42,height*.12,width*.13),(-length*.59,height*.29,width*.26),(-length*.70,height*.37,width*.30)],.0032,M["black_wire"],14),"wire_black/")
    add(s,"xt90_body",box((.026,.019,.024),(-length*.76,height*.42,width*.36),M["yellow"]))
    add(s,"xt90_socket_a",cyl(.0037,.010,(-length*.765,height*.423,width*.353),M["gold"],axis="x",sections=24))
    add(s,"xt90_socket_b",cyl(.0037,.010,(-length*.765,height*.423,width*.369),M["gold"],axis="x",sections=24))
    return s

def build_power(length=.060,width=.045,heavy=False,detail=2):
    s=trimesh.Scene()
    add(s,"pcb",box((length,.004,width),(0,0,0),M["pcb"]))
    add(s,"hall_sensor",box((length*.28,.018,width*.36),(0,.011,0),M["plastic_black"]))
    add(s,"shunt",box((length*.20,.004,width*.12),(length*.20,.007,-width*.28),M["copper"]))
    add(s,"processor",box((.012,.004,.012),(-length*.18,.006,width*.18),M["dark_metal"]))
    add(s,"label",box((length*.24,.001,width*.18),(0,.021,0),M["label_white"]))
    # large current terminals
    for i,z in enumerate((-width*.36,width*.36)):
        add(s,f"terminal_{i}",box((.014,.010,.012),(length*.36,.008,z),M["gold"]))
        add_screw(s,f"terminal_screw_{i}",(length*.36,.015,z),r=.0022,h=.0025)
    # output leads
    copy_scene(s,rounded_wire([(-length*.36,.005,-width*.23),(-length*.55,-.002,-width*.30)],.0025,M["red_wire"],12),"power_red/")
    copy_scene(s,rounded_wire([(-length*.36,.005,width*.23),(-length*.55,-.002,width*.30)],.0025,M["black_wire"],12),"power_black/")
    # telemetry connector + 4 pins
    add(s,"telemetry_socket",box((.013,.007,.008),(-length*.28,.007,0),M["plastic_white"]))
    add_pin_header(s,"telemetry_pin",(-length*.28,.011,0),count=4,axis="z")
    return s

def build_fc(size=.050,variant=1,detail=2):
    s=trimesh.Scene()
    add(s,"pcb",box((size,.0038,size),(0,0,0),M["pcb_black"] if variant==2 else M["pcb"]))
    # vibration dampers / mounting holes
    for ix,x in enumerate((-size*.43,size*.43)):
        for iz,z in enumerate((-size*.43,size*.43)):
            add(s,f"damper_{ix}_{iz}",cyl(.0036,.013,(x,.002,z),M["rubber"],sections=28))
            add(s,f"washer_{ix}_{iz}",cyl(.0050,.0015,(x,.009,z),M["aluminium"],sections=28))
    # main MCU + IMU stack
    add(s,"mcu",box((.015,.004,.015),(-.006,.006,0),M["dark_metal"]))
    add(s,"imu",box((.008,.003,.008),(.012,.006,-.010),M["black_metal"]))
    add(s,"baro",box((.006,.003,.006),(.013,.006,.012),M["aluminium"]))
    add(s,"flash",box((.008,.003,.006),(-.015,.006,.015),M["dark_metal"]))
    # USB-C style port on front edge (+X)
    add(s,"usb_shell",box((.010,.005,.007),(size*.51,.004,0),M["aluminium"]))
    add(s,"usb_hole",box((.006,.002,.0035),(size*.516,.004,0),M["carbon_edge"]))
    # JST ports
    for i,z in enumerate(np.linspace(-size*.30,size*.30,4)):
        add(s,f"jst_{i}",box((.008,.006,.006),(-size*.48,.005,z),M["plastic_white"]))
    # headers and directional arrow
    add_pin_header(s,"header_front",(size*.30,.006,size*.35),count=5,axis="x")
    add(s,"arrow_stem",box((size*.24,.0016,.0038),(size*.03,.0085,0),M["label_white"]))
    tip=trimesh.creation.cone(radius=.0055,height=.010,sections=20)
    apply_mat(tip,M["label_white"])
    tip.apply_transform(rotation_matrix(math.pi/2,[0,0,1]))
    tip.apply_translation((size*.20,.0085,0))
    add(s,"arrow_tip",tip)
    add(s,"status_led",box((.004,.0016,.004),(-size*.16,.0085,-size*.20),M["led_green"]))
    return s

def build_gnss(radius=.032,detail=2):
    s=trimesh.Scene()
    add(s,"housing_lower",cyl(radius,.008,(0,0,0),M["plastic_black"],sections=48))
    add(s,"housing_upper",cyl(radius*.96,.015,(0,.011,0),M["plastic_white"],sections=48))
    add(s,"antenna_patch",box((radius*1.20,.003,radius*1.20),(0,.020,0),M["ceramic"]))
    add(s,"top_cap",cyl(radius*.70,.003,(0,.024,0),M["plastic_white"],sections=44))
    add(s,"north_arrow",box((radius*.75,.0012,.0035),(radius*.05,.026,0),M["carbon_edge"]))
    # cable gland and cable
    add(s,"gland",cyl(.006,.012,(-radius*.80,.004,0),M["rubber"],axis="x",sections=28))
    copy_scene(s,rounded_wire([(-radius*.90,.004,0),(-radius*1.45,-.006,.004),(-radius*1.90,-.015,.008)],.0017,M["black_wire"],12),"cable/")
    return s

def build_camera(detail=2):
    s=trimesh.Scene()
    # upper mount + yaw motor
    add(s,"mount_plate",box((.060,.006,.055),(0,.052,0),M["carbon"]))
    add(s,"yaw_motor",cyl(.019,.018,(0,.036,0),M["black_metal"],sections=40))
    add(s,"yaw_ring",torus(.015,.0025,(0,.027,0),M["red_anod"],axis="y",major_sections=36,minor_sections=9))
    # roll frame arms
    add(s,"left_arm",box((.010,.056,.010),(0,-.002,-.039),M["black_metal"]))
    add(s,"right_arm",box((.010,.056,.010),(0,-.002,.039),M["black_metal"]))
    add(s,"roll_motor_l",cyl(.013,.013,(0,-.032,-.039),M["dark_metal"],axis="z",sections=36))
    add(s,"roll_motor_r",cyl(.013,.013,(0,-.032,.039),M["dark_metal"],axis="z",sections=36))
    # camera body / grip / screen hint
    add(s,"camera_body",box((.075,.054,.086),(.006,-.052,0),M["plastic_black"]))
    add(s,"body_top",box((.055,.012,.066),(.002,-.019,0),M["dark_metal"]))
    add(s,"grip",box((.023,.050,.028),(-.043,-.055,-.028),M["rubber"]))
    add(s,"rear_screen",box((.002,.030,.050),(-.032,-.050,.010),M["glass"]))
    # lens train
    add(s,"lens_mount",cyl(.033,.010,(.032,-.052,0),M["black_metal"],axis="x",sections=48))
    add(s,"lens_barrel",cyl(.028,.034,(.049,-.052,0),M["dark_metal"],axis="x",sections=52))
    add(s,"focus_ring",torus(.026,.0025,(.059,-.052,0),M["aluminium"],axis="x",major_sections=44,minor_sections=10))
    add(s,"front_glass",cyl(.023,.002,(.067,-.052,0),M["glass"],axis="x",sections=48))
    add(s,"record_led",box((.002,.004,.004),(.045,-.022,.030),M["led_red"]))
    return s

def build_complete_650(detail=2):
    s=trimesh.Scene()
    copy_scene(s,build_frame(.65,True,detail),"frame/")
    off=.65/2/math.sqrt(2)
    mpos={
        "M1":(off,.067,-off),
        "M2":(off,.067,off),
        "M3":(-off,.067,off),
        "M4":(-off,.067,-off)
    }
    for name,p in mpos.items():
        copy_scene(s,build_motor(.030,.054,"red",detail),f"motor/{name}/",translation_matrix(p))
        ep=np.array(p,float)*.64; ep[1]=.073
        copy_scene(s,build_esc(.056,.027,"blue",detail),f"esc/{name}/",translation_matrix(ep))
        direction="ccw" if name in ("M1","M3") else "cw"
        copy_scene(s,build_prop(15,direction,detail),f"prop/{name}/",translation_matrix((p[0],p[1]+.070,p[2])))
    copy_scene(s,build_power(.060,.045,False,detail),"power/",translation_matrix((0,.020,0)))
    copy_scene(s,build_fc(.050,1,detail),"fc/",translation_matrix((0,.083,0)))
    copy_scene(s,build_battery(.165,.070,.060,False,detail),"battery/",translation_matrix((-.030,-.100,0)))
    add(s,"gnss_mast",cyl(.0038,.105,(-.16,.140,0),M["black_metal"],sections=28))
    copy_scene(s,build_gnss(.032,detail),"gnss/",translation_matrix((-.16,.193,0)))
    copy_scene(s,build_camera(detail),"payload/",translation_matrix((.08,-.12,0)))
    return s

BUILDERS = {
    "frame_650.glb": lambda: build_frame(.65, True),
    "frame_450.glb": lambda: build_frame(.45, False),
    "motor_5010_360kv.glb": lambda: build_motor(.030,.054,"red"),
    "motor_4008_500kv.glb": lambda: build_motor(.024,.046,"blue"),
    "esc_30a.glb": lambda: build_esc(.048,.023,"red"),
    "esc_40a.glb": lambda: build_esc(.056,.027,"blue"),
    "prop_15_cw.glb": lambda: build_prop(15,"cw"),
    "prop_15_ccw.glb": lambda: build_prop(15,"ccw"),
    "prop_14_cw.glb": lambda: build_prop(14,"cw"),
    "prop_14_ccw.glb": lambda: build_prop(14,"ccw"),
    "battery_6s_10000.glb": lambda: build_battery(.165,.070,.060,False),
    "battery_6s_16000.glb": lambda: build_battery(.195,.082,.070,True),
    "power_120a.glb": lambda: build_power(.060,.045,False),
    "power_160a.glb": lambda: build_power(.070,.052,True),
    "fc_v1.glb": lambda: build_fc(.050,1),
    "fc_v2.glb": lambda: build_fc(.046,2),
    "gnss_m8n.glb": lambda: build_gnss(.032),
    "payload_camera_300g.glb": build_camera,
    "eduquad650_reference.glb": build_complete_650,
}

def export_scene(name, builder):
    scene=builder()
    data=scene.export(file_type="glb")
    path=MODEL_DIR/name
    path.write_bytes(data)
    loaded=trimesh.load(path,force="scene")
    assert len(loaded.geometry)>0, name
    return scene,len(data),sum(len(g.faces) for g in loaded.geometry.values())

# ---------------------------------------------------------------------------
# Honest thumbnails rendered from generated geometry
# ---------------------------------------------------------------------------
def render_scene(scene: trimesh.Scene, path: Path, elev=24, azim=-48):
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    fig=plt.figure(figsize=(4,4),dpi=128)
    ax=fig.add_subplot(111,projection="3d")
    all_pts=[]
    for geom in scene.geometry.values():
        v=np.asarray(geom.vertices)
        f=np.asarray(geom.faces)
        if len(v)==0 or len(f)==0:
            continue
        vd=v[:,[0,2,1]]   # screen x, screen depth, up
        all_pts.append(vd)
        # keep thumbnail generation bounded but representative
        step=max(1,len(f)//900)
        tris=vd[f[::step]]
        material=getattr(getattr(geom.visual,"material",None),"baseColorFactor",None)
        if material is None:
            rgba=np.array([.32,.34,.38,1.0])
        else:
            rgba=np.asarray(material,dtype=float)
            if float(np.max(rgba)) > 1.0:
                rgba = rgba / 255.0
        poly=Poly3DCollection(tris,facecolor=rgba,edgecolor="none",alpha=float(rgba[3]))
        ax.add_collection3d(poly)

    pts=np.vstack(all_pts) if all_pts else np.array([[-1,-1,-1],[1,1,1]])
    lo=pts.min(axis=0); hi=pts.max(axis=0); c=(lo+hi)/2
    span=max(float(np.max(hi-lo)),.04)
    ax.set_xlim(c[0]-span*.57,c[0]+span*.57)
    ax.set_ylim(c[1]-span*.57,c[1]+span*.57)
    ax.set_zlim(c[2]-span*.48,c[2]+span*.48)
    ax.view_init(elev=elev,azim=azim)
    ax.set_box_aspect((1,1,.82))
    ax.set_axis_off()
    fig.patch.set_facecolor("#f3f7fc")
    ax.set_facecolor("#f3f7fc")
    plt.subplots_adjust(0,0,1,1)
    plt.savefig(path,dpi=128,bbox_inches="tight",pad_inches=.03,facecolor=fig.get_facecolor())
    plt.close(fig)

scenes={}
metrics={}
for filename,builder in BUILDERS.items():
    sc,size,faces=export_scene(filename,builder)
    scenes[filename]=sc
    metrics[filename]={"bytes":size,"triangles":faces}
    print(f"{filename:32s} {faces:8d} triangles {size/1024:8.1f} KiB")

THUMB_MAP = {
    "frame_650.glb":"frame_650.png",
    "frame_450.glb":"frame_450.png",
    "motor_5010_360kv.glb":"motor_5010.png",
    "motor_4008_500kv.glb":"motor_4008.png",
    "esc_30a.glb":"esc_30a.png",
    "esc_40a.glb":"esc_40a.png",
    "prop_15_ccw.glb":"prop_15.png",
    "prop_14_ccw.glb":"prop_14.png",
    "battery_6s_10000.glb":"battery_10000.png",
    "battery_6s_16000.glb":"battery_16000.png",
    "power_120a.glb":"power_120.png",
    "power_160a.glb":"power_160.png",
    "fc_v1.glb":"fc_v1.png",
    "fc_v2.glb":"fc_v2.png",
    "gnss_m8n.glb":"gnss_m8n.png",
    "payload_camera_300g.glb":"payload_camera.png",
    "eduquad650_reference.glb":"eduquad650_reference.png",
}
for glb,png in THUMB_MAP.items():
    render_scene(scenes[glb],THUMB_DIR/png,elev=28 if "prop_" not in glb else 62)

manifest={
    "assetVersion":"1.1.0",
    "visualEdition":"EduQuad-650 Realistic Edition 2.0",
    "units":"meter",
    "axes":{"x":"+X forward","y":"+Y up","z":"+Z right"},
    "scope":"教学级工程数字样机。几何、材质和结构用于教学可视化，不代表任何厂商制造级CAD。",
    "materialSystem":"glTF 2.0 PBR metallic-roughness",
    "features":[
        "carbon frame plates and round arms",
        "machined/anodized mounts and fasteners",
        "outrunner motors with visible copper windings and phase wires",
        "ESC MOSFET/heatsink/capacitor/lead details",
        "twisted swept propeller blades with CW/CCW variants",
        "LiPo pack straps, balance connector, power leads and XT90",
        "flight-controller ICs, ports, headers and vibration dampers",
        "GNSS ceramic antenna and cable",
        "3-axis gimbal camera with lens train"
    ],
    "componentMap":{
        "1":{"type":"frame","file":"frame_650.glb","thumbnail":"thumbnails/frame_650.png"},
        "2":{"type":"frame","file":"frame_450.glb","thumbnail":"thumbnails/frame_450.png"},
        "10":{"type":"motor","file":"motor_5010_360kv.glb","thumbnail":"thumbnails/motor_5010.png"},
        "11":{"type":"motor","file":"motor_4008_500kv.glb","thumbnail":"thumbnails/motor_4008.png"},
        "20":{"type":"esc","file":"esc_30a.glb","thumbnail":"thumbnails/esc_30a.png"},
        "21":{"type":"esc","file":"esc_40a.glb","thumbnail":"thumbnails/esc_40a.png"},
        "30":{"type":"propeller","cw":"prop_15_cw.glb","ccw":"prop_15_ccw.glb","thumbnail":"thumbnails/prop_15.png"},
        "31":{"type":"propeller","cw":"prop_14_cw.glb","ccw":"prop_14_ccw.glb","thumbnail":"thumbnails/prop_14.png"},
        "40":{"type":"battery","file":"battery_6s_10000.glb","thumbnail":"thumbnails/battery_10000.png"},
        "41":{"type":"battery","file":"battery_6s_16000.glb","thumbnail":"thumbnails/battery_16000.png"},
        "50":{"type":"power_module","file":"power_120a.glb","thumbnail":"thumbnails/power_120.png"},
        "51":{"type":"power_module","file":"power_160a.glb","thumbnail":"thumbnails/power_160.png"},
        "60":{"type":"flight_controller","file":"fc_v1.glb","thumbnail":"thumbnails/fc_v1.png"},
        "61":{"type":"flight_controller","file":"fc_v2.glb","thumbnail":"thumbnails/fc_v2.png"},
        "70":{"type":"gnss","file":"gnss_m8n.glb","thumbnail":"thumbnails/gnss_m8n.png"},
        "80":{"type":"payload","file":"payload_camera_300g.glb","thumbnail":"thumbnails/payload_camera.png"},
    },
    "motorDirection":{"M1":"CCW","M2":"CW","M3":"CCW","M4":"CW"},
    "referenceComplete":"eduquad650_reference.glb",
    "metrics":metrics,
}
(MODEL_DIR/"asset_manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
(MODEL_DIR/"REALISTIC_EDITION.md").write_text(
    "# EduQuad-650 Realistic Edition 2.0\n\n"
    "这些 GLB 与原 V1.1 文件名保持一致，因此现有 Component.visual、组件库、装配页、爆炸视图和 Replay 不需要修改即可使用。\n\n"
    "模型采用 glTF 2.0 PBR metallic-roughness 材质，目标是教学级工程数字样机，不是制造级 CAD。\n",
    encoding="utf-8"
)
(ROOT/"docs").mkdir(parents=True,exist_ok=True)
render_scene(scenes["eduquad650_reference.glb"], ROOT/"docs"/"eduquad650_realistic_preview.png", elev=26, azim=-42)
(ROOT/"docs"/"17_REALISTIC_ASSET_EDITION_CN.md").write_text(
    """# UAV Studio — EduQuad-650 Realistic Edition 2.0

## 定位

本资产包把原有“教学示意模型”升级为教学级工程数字样机，同时保持原文件名和数据契约不变。

## 视觉升级

- 碳纤维机架板、圆管机臂、金属夹具、紧固件、落地架；
- 外转子电机：铜绕组、通风结构、轴、桨夹、安装耳、三相线；
- ESC：PCB、MOSFET、散热片、电容、电机三相线、电源线、信号线；
- 螺旋桨：带径向扭转和扫掠的叶片，而非平板；
- 电池：电芯筋、热缩外皮、绑带、平衡头、电源线、XT90；
- 电源模块：霍尔传感器、分流器、端子、遥测接口；
- 飞控：MCU、IMU、气压计、USB、JST、排针、减震柱、方向箭头；
- GNSS：塑料外壳、陶瓷天线、电缆；
- 相机载荷：三轴云台结构、机身、镜头组、前镜片。

## 兼容性

文件路径仍为：

`frontend/public/models/uav/v1_1/`

并保持现有文件名，因此无需修改现有 Component.visual 或数据库。

## 真实性边界

这些模型是“物理上合理、教学上可解释”的通用部件，不对应具体厂商的制造级 CAD。
""",
    encoding="utf-8"
)
print("generated", MODEL_DIR)
