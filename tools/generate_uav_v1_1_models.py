from pathlib import Path
import json, math, shutil
import numpy as np
import trimesh
from trimesh.transformations import rotation_matrix, translation_matrix

ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT/'frontend'/'public'/'models'/'uav'/'v1_1'
THUMB_DIR = MODEL_DIR/'thumbnails'
MODEL_DIR.mkdir(parents=True, exist_ok=True)
THUMB_DIR.mkdir(parents=True, exist_ok=True)

COL = {
    'carbon': [30, 35, 41, 255], 'carbon2':[45, 51, 58, 255], 'black':[16,19,23,255],
    'dark':[39,45,52,255], 'metal':[104,112,121,255], 'silver':[178,186,194,255],
    'red':[196,45,52,255], 'red2':[117,25,30,255], 'blue':[45,101,188,255],
    'blue2':[25,72,150,255], 'green':[31,125,83,255], 'pcb':[25,83,61,255],
    'gold':[204,158,55,255], 'white':[220,226,232,255], 'prop':[47,52,59,255],
    'lens':[11,20,32,255], 'copper':[172,83,42,255], 'yellow':[231,180,43,255],
    'orange':[220,110,30,255], 'gray':[90,98,108,255]
}

def color(mesh, rgba):
    mesh.visual.face_colors = np.tile(np.asarray(rgba, dtype=np.uint8), (len(mesh.faces), 1)); return mesh

def box(ext, pos=(0,0,0), rgba=COL['dark']):
    m = trimesh.creation.box(extents=ext); color(m,rgba); m.apply_translation(pos); return m

def cyl(radius,height,pos=(0,0,0),rgba=COL['metal'],axis='y',sections=32):
    m=trimesh.creation.cylinder(radius=radius,height=height,sections=sections); color(m,rgba)
    if axis=='y': m.apply_transform(rotation_matrix(-math.pi/2,[1,0,0]))
    elif axis=='x': m.apply_transform(rotation_matrix(math.pi/2,[0,1,0]))
    m.apply_translation(pos); return m

def cyl_between(p0,p1,radius,rgba=COL['carbon'],sections=20):
    p0=np.array(p0,float); p1=np.array(p1,float); v=p1-p0; h=np.linalg.norm(v)
    m=trimesh.creation.cylinder(radius=radius,height=h,sections=sections); color(m,rgba)
    T=trimesh.geometry.align_vectors([0,0,1],v/h); m.apply_transform(T); m.apply_translation((p0+p1)/2); return m

def add(scene,name,mesh): scene.add_geometry(mesh,geom_name=name,node_name=name)

def add_fastener(scene,name,pos,r=.0033,h=.004):
    add(scene,name,cyl(r,h,pos,COL['silver']))

def prop_blade(length,root,tip,thickness,direction=1):
    x0=max(.012,length*.09); x1=length; z0=root/2; z1=tip/2; y=thickness/2
    verts=np.array([[x0,-y,-z0],[x0,-y,z0],[x1,-y,z1],[x1,-y,-z1],[x0,y,-z0],[x0,y,z0],[x1,y,z1],[x1,y,-z1]],float)
    faces=np.array([[0,1,2],[0,2,3],[4,6,5],[4,7,6],[0,4,5],[0,5,1],[3,2,6],[3,6,7],[1,5,6],[1,6,2],[0,3,7],[0,7,4]])
    m=trimesh.Trimesh(vertices=verts,faces=faces,process=False); color(m,COL['prop'])
    m.apply_transform(rotation_matrix(direction*math.radians(6),[1,0,0])); return m

def build_prop(diameter_in=15.0,direction='ccw'):
    s=trimesh.Scene(); sign=1 if direction=='ccw' else -1
    radius=diameter_in*0.0254/2
    add(s,'hub_lower',cyl(.017,.008,(0,0,0),COL['black']))
    add(s,'hub_cap',cyl(.011,.009,(0,.008,0),COL['metal']))
    for idx,angle in enumerate([math.radians(10)*sign, math.pi+math.radians(10)*sign]):
        b=prop_blade(radius*.92, radius*.22, radius*.11, .0055 if diameter_in>=15 else .0048, sign)
        b.apply_transform(rotation_matrix(angle,[0,1,0])); add(s,f'blade_{idx}',b)
    return s

def build_motor(radius=.0275,height=.050,accent=COL['red']):
    s=trimesh.Scene()
    add(s,'base',cyl(radius*1.08,.006,(0,0,0),COL['black']))
    add(s,'stator',cyl(radius*.96,height*.45,(0,height*.24,0),COL['red2']))
    add(s,'bell',cyl(radius,height*.52,(0,height*.55,0),COL['black']))
    add(s,'accent_ring',cyl(radius*1.02,.004,(0,height*.34,0),accent))
    add(s,'cap',cyl(radius*.62,.006,(0,height*.84,0),COL['metal']))
    add(s,'shaft',cyl(.0032,height*.40,(0,height*1.08,0),COL['silver']))
    # vertical bell slots give a recognizable outrunner look
    for i,a in enumerate(np.linspace(0,2*math.pi,8,endpoint=False)):
        x=radius*.83*math.cos(a); z=radius*.83*math.sin(a)
        add(s,f'groove_{i}',box((.004,height*.28,.010),(x,height*.57,z),COL['gray']))
    for i,a in enumerate([0,math.pi/2,math.pi,3*math.pi/2]):
        x=radius*1.10*math.cos(a); z=radius*1.10*math.sin(a)
        add(s,f'tab_{i}',box((.015,.004,.010),(x,.002,z),COL['dark']))
        add_fastener(s,f'screw_{i}',(x,.005,z),r=.002)
    return s

def build_esc(length=.052,width=.025,accent=COL['green']):
    s=trimesh.Scene(); add(s,'board',box((length,.007,width),(0,0,0),COL['pcb']))
    add(s,'cover',box((length*.92,.010,width*.84),(0,.009,0),COL['black']))
    for i,z in enumerate(np.linspace(-width*.32,width*.32,5)):
        add(s,f'fin_{i}',box((length*.78,.004,.0014),(0,.016,z),COL['metal']))
    for i,z in enumerate([-width*.28,0,width*.28]):
        add(s,f'phase_{i}',cyl_between((length*.48,.003,z),(length*.78,.003,z),.0014,COL['copper'],10))
    add(s,'status',box((.005,.002,.005),(-length*.30,.018,0),accent)); return s

def build_battery(length=.165,width=.070,height=.060,body=COL['blue']):
    s=trimesh.Scene(); add(s,'body',box((length,height,width),(0,0,0),body))
    add(s,'front_cap',box((.012,height*1.03,width*1.03),(length/2,0,0),COL['black']))
    add(s,'rear_cap',box((.012,height*1.03,width*1.03),(-length/2,0,0),COL['black']))
    for x in (-length*.24,length*.24): add(s,f'strap_{x}',box((.026,height*1.06,width*1.08),(x,0,0),COL['black']))
    add(s,'label',box((length*.44,.0018,width*.60),(.015,height/2+.002,0),COL['white']))
    add(s,'wire_red',cyl_between((-length*.44,height*.18,width*.28),(-length*.68,height*.40,width*.43),.003,COL['red'],12))
    add(s,'wire_black',cyl_between((-length*.44,height*.12,width*.15),(-length*.68,height*.34,width*.30),.003,COL['black'],12))
    add(s,'xt90',box((.021,.017,.020),(-length*.72,height*.42,width*.36),COL['yellow'])); return s

def build_fc(size=.050,accent=COL['white']):
    s=trimesh.Scene(); add(s,'pcb',box((size,.004,size),(0,0,0),COL['pcb']))
    add(s,'case',box((size*.86,.011,size*.86),(0,.008,0),COL['dark']))
    for x in (-size*.43,size*.43):
      for z in (-size*.43,size*.43): add(s,f'damper_{x}_{z}',cyl(.0035,.012,(x,.002,z),COL['red']))
    add(s,'arrow_shaft',box((size*.38,.0028,.004),(size*.05,.015,0),accent))
    cone=trimesh.creation.cone(radius=.006,height=.012,sections=16); color(cone,accent); cone.apply_transform(rotation_matrix(math.pi/2,[0,0,1])); cone.apply_translation((size*.30,.015,0)); add(s,'arrow_tip',cone)
    return s

def build_power(length=.060,width=.045,big=False):
    s=trimesh.Scene(); add(s,'pdb',box((length,.005,width),(0,0,0),COL['pcb']))
    add(s,'case',box((length*.58,.013,width*.58),(0,.009,0),COL['dark']))
    add(s,'label',box((length*.38,.001,width*.26),(.002,.016,0),COL['white']))
    for i,z in enumerate([-width*.36,width*.36]): add(s,f'terminal_{i}',box((.012,.008,.010),(length*.38,.006,z),COL['gold']))
    return s

def build_gnss(radius=.032):
    s=trimesh.Scene(); add(s,'base',cyl(radius,.008,(0,0,0),COL['dark']))
    add(s,'puck',cyl(radius*.94,.018,(0,.012,0),COL['white'])); add(s,'top',cyl(radius*.73,.004,(0,.023,0),COL['silver']))
    add(s,'arrow',box((radius*.75,.0018,.004),(radius*.05,.026,0),COL['black'])); return s

def build_camera():
    s=trimesh.Scene(); add(s,'mount',box((.058,.012,.052),(0,.044,0),COL['dark']))
    add(s,'yaw_joint',cyl(.018,.020,(0,.027,0),COL['metal']))
    add(s,'left_arm',box((.010,.058,.010),(0,-.009,-.038),COL['dark'])); add(s,'right_arm',box((.010,.058,.010),(0,-.009,.038),COL['dark']))
    add(s,'joint_l',cyl(.012,.012,(0,-.038,-.038),COL['metal'],axis='z')); add(s,'joint_r',cyl(.012,.012,(0,-.038,.038),COL['metal'],axis='z'))
    add(s,'camera_body',box((.072,.052,.090),(.006,-.050,0),COL['black']))
    add(s,'grip',box((.022,.046,.026),(-.040,-.055,-.030),COL['dark']))
    add(s,'lens_ring',cyl(.031,.008,(.030,-.050,0),COL['metal'],axis='x')); add(s,'lens',cyl(.025,.030,(.045,-.050,0),COL['lens'],axis='x'))
    add(s,'sensor_mark',box((.0018,.012,.018),(.043,-.020,.030),COL['red'])); return s

def build_frame(diagonal=.65, landing=True):
    s=trimesh.Scene(); scale=diagonal/.65
    plate_x=.22*scale; plate_z=.18*scale
    add(s,'bottom_plate',box((plate_x,.006,plate_z),(0,.006,0),COL['carbon']))
    add(s,'top_plate',box((plate_x*.86,.006,plate_z*.88),(0,.061*scale,0),COL['carbon2']))
    for x in (-plate_x*.34,plate_x*.34):
      for z in (-plate_z*.30,plate_z*.30):
        add(s,f'spacer_{x}_{z}',cyl(.0048*scale,.050*scale,(x,.034*scale,z),COL['red']))
        add_fastener(s,f'top_screw_{x}_{z}',(x,.065*scale,z),r=.0025*scale)
    offset=diagonal/2/math.sqrt(2)
    mpos={'M1':(offset,.066*scale,-offset),'M2':(offset,.066*scale,offset),'M3':(-offset,.066*scale,offset),'M4':(-offset,.066*scale,-offset)}
    for name,p in mpos.items():
        sx=(.052 if p[0]>0 else -.052)*scale; sz=(.042 if p[2]>0 else -.042)*scale
        add(s,f'arm_{name}',cyl_between((sx,.052*scale,sz),(p[0],p[1]-.005*scale,p[2]),.0115*scale,COL['carbon'],20))
        add(s,f'motor_mount_{name}',cyl(.034*scale,.006*scale,p,COL['carbon2']))
        # red clamp near root
        cp=np.array([p[0],p[1],p[2]])*.36
        cp[1]=.052*scale
        add(s,f'arm_clamp_{name}',cyl(.015*scale,.018*scale,cp,COL['red2'],axis='x' if abs(p[2])>abs(p[0]) else 'z',sections=16))
    if landing:
        rail_z=.10*scale; y0=.005*scale; y1=-.145*scale
        for x,z in [( .055,-.072),( .055,.072),(-.055,-.072),(-.055,.072)]:
            x*=scale; z*=scale; xe=x*1.65; ze=math.copysign(rail_z,z)
            add(s,f'leg_{x}_{z}',cyl_between((x,y0,z),(xe,y1,ze),.006*scale,COL['carbon'],16))
        add(s,'rail_left',cyl_between((.13*scale,y1,-rail_z),(-.13*scale,y1,-rail_z),.007*scale,COL['carbon'],18))
        add(s,'rail_right',cyl_between((.13*scale,y1,rail_z),(-.13*scale,y1,rail_z),.007*scale,COL['carbon'],18))
    return s

def copy_scene(dst, src, prefix, T=None):
    T=np.eye(4) if T is None else T
    for node in src.graph.nodes_geometry:
        trans,gname=src.graph[node]; geom=src.geometry[gname].copy(); geom.apply_transform(T@trans); add(dst,prefix+node,geom)

def build_complete_650():
    s=trimesh.Scene(); copy_scene(s,build_frame(.65,True),'frame/')
    off=.65/2/math.sqrt(2); mpos={'M1':(off,.066,-off),'M2':(off,.066,off),'M3':(-off,.066,off),'M4':(-off,.066,-off)}
    for name,p in mpos.items():
        copy_scene(s,build_motor(.029,.052),'motor/'+name+'/',translation_matrix(p))
        ep=np.array(p)*.64; ep[1]=.075; copy_scene(s,build_esc(.055,.026),'esc/'+name+'/',translation_matrix(ep))
        copy_scene(s,build_prop(15,'ccw' if name in ('M1','M3') else 'cw'),'prop/'+name+'/',translation_matrix((p[0],p[1]+.064,p[2])))
    copy_scene(s,build_power(.060,.045),'power/',translation_matrix((0,.020,0)))
    copy_scene(s,build_fc(.050),'fc/',translation_matrix((.0,.082,0)))
    copy_scene(s,build_battery(.165,.070,.060),'battery/',translation_matrix((-.030,-.100,0)))
    add(s,'gnss_mast',cyl(.0038,.11,(-.16,.135,0),COL['black']))
    copy_scene(s,build_gnss(.032),'gnss/',translation_matrix((-.16,.190,0)))
    copy_scene(s,build_camera(),'payload/',translation_matrix((.08,-.12,0)))
    return s

builders={
 'frame_650.glb':lambda:build_frame(.65,True), 'frame_450.glb':lambda:build_frame(.45,False),
 'motor_5010_360kv.glb':lambda:build_motor(.030,.054,COL['red']), 'motor_4008_500kv.glb':lambda:build_motor(.024,.044,COL['orange']),
 'esc_30a.glb':lambda:build_esc(.048,.023,COL['green']), 'esc_40a.glb':lambda:build_esc(.056,.027,COL['blue']),
 'prop_15_cw.glb':lambda:build_prop(15,'cw'), 'prop_15_ccw.glb':lambda:build_prop(15,'ccw'),
 'prop_14_cw.glb':lambda:build_prop(14,'cw'), 'prop_14_ccw.glb':lambda:build_prop(14,'ccw'),
 'battery_6s_10000.glb':lambda:build_battery(.165,.070,.060,COL['blue']), 'battery_6s_16000.glb':lambda:build_battery(.195,.082,.070,COL['blue2']),
 'power_120a.glb':lambda:build_power(.060,.045,False), 'power_160a.glb':lambda:build_power(.070,.052,True),
 'fc_v1.glb':lambda:build_fc(.050,COL['white']), 'fc_v2.glb':lambda:build_fc(.046,COL['yellow']),
 'gnss_m8n.glb':lambda:build_gnss(.032), 'payload_camera_300g.glb':build_camera,
 'eduquad650_reference.glb':build_complete_650,
}

def export_scene(filename,builder):
    sc=builder(); data=sc.export(file_type='glb'); p=MODEL_DIR/filename; p.write_bytes(data)
    loaded=trimesh.load(p,force='scene'); assert len(loaded.geometry)>0
    return sc,len(data)

scenes={}
for fn,b in builders.items():
    sc,size=export_scene(fn,b); scenes[fn]=sc; print(fn,size)

# Render simple honest thumbnails from the same generated geometry (not AI concept art)
def render_scene(scene,path,limits=None,elev=24,azim=-48):
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    fig=plt.figure(figsize=(3.2,2.4),dpi=120); ax=fig.add_subplot(111,projection='3d')
    pts=[]
    for geom in scene.geometry.values():
        v=np.asarray(geom.vertices); f=np.asarray(geom.faces)
        # display coordinates x, z(right), y(up)
        vd=v[:,[0,2,1]]; pts.append(vd)
        step=max(1,len(f)//600); tris=vd[f[::step]]
        rgba=np.asarray(geom.visual.face_colors[0])/255.0 if hasattr(geom.visual,'face_colors') and len(geom.visual.face_colors) else np.array([.3,.3,.3,1])
        ax.add_collection3d(Poly3DCollection(tris,facecolor=rgba,edgecolor='none',alpha=rgba[3]))
    allp=np.vstack(pts) if pts else np.array([[-1,-1,-1],[1,1,1]])
    mins=allp.min(axis=0); maxs=allp.max(axis=0); center=(mins+maxs)/2; span=max(maxs-mins); span=max(span,.05)
    ax.set_xlim(center[0]-span*.58,center[0]+span*.58); ax.set_ylim(center[1]-span*.58,center[1]+span*.58); ax.set_zlim(center[2]-span*.42,center[2]+span*.42)
    ax.view_init(elev=elev,azim=azim); ax.set_box_aspect((1,1,.75)); ax.set_axis_off(); fig.patch.set_facecolor('#f3f6fa'); ax.set_facecolor('#f3f6fa')
    plt.tight_layout(pad=0); plt.savefig(path,bbox_inches='tight',pad_inches=.02,facecolor=fig.get_facecolor()); plt.close(fig)

thumb_map={
 'frame_650.glb':'frame_650.png','frame_450.glb':'frame_450.png','motor_5010_360kv.glb':'motor_5010.png','motor_4008_500kv.glb':'motor_4008.png',
 'esc_30a.glb':'esc_30a.png','esc_40a.glb':'esc_40a.png','prop_15_ccw.glb':'prop_15.png','prop_14_ccw.glb':'prop_14.png',
 'battery_6s_10000.glb':'battery_10000.png','battery_6s_16000.glb':'battery_16000.png','power_120a.glb':'power_120.png','power_160a.glb':'power_160.png',
 'fc_v1.glb':'fc_v1.png','fc_v2.glb':'fc_v2.png','gnss_m8n.glb':'gnss_m8n.png','payload_camera_300g.glb':'payload_camera.png','eduquad650_reference.glb':'eduquad650_reference.png'
}
for fn,png in thumb_map.items(): render_scene(scenes[fn],THUMB_DIR/png,elev=22 if 'prop_' not in fn else 55)

manifest={
 'assetVersion':'1.1.0','units':'meter','axes':{'x':'+X forward','y':'+Y up','z':'+Z right'},
 'scope':'教学用中等精度通用模型；不对应任何厂商精确CAD。所有缩略图均由本包GLB几何直接渲染。',
 'componentMap':{
   '1':{'type':'frame','file':'frame_650.glb','thumbnail':'thumbnails/frame_650.png'},
   '2':{'type':'frame','file':'frame_450.glb','thumbnail':'thumbnails/frame_450.png'},
   '10':{'type':'motor','file':'motor_5010_360kv.glb','thumbnail':'thumbnails/motor_5010.png'},
   '11':{'type':'motor','file':'motor_4008_500kv.glb','thumbnail':'thumbnails/motor_4008.png'},
   '20':{'type':'esc','file':'esc_30a.glb','thumbnail':'thumbnails/esc_30a.png'},
   '21':{'type':'esc','file':'esc_40a.glb','thumbnail':'thumbnails/esc_40a.png'},
   '30':{'type':'propeller','cw':'prop_15_cw.glb','ccw':'prop_15_ccw.glb','thumbnail':'thumbnails/prop_15.png'},
   '31':{'type':'propeller','cw':'prop_14_cw.glb','ccw':'prop_14_ccw.glb','thumbnail':'thumbnails/prop_14.png'},
   '40':{'type':'battery','file':'battery_6s_10000.glb','thumbnail':'thumbnails/battery_10000.png'},
   '41':{'type':'battery','file':'battery_6s_16000.glb','thumbnail':'thumbnails/battery_16000.png'},
   '50':{'type':'power_module','file':'power_120a.glb','thumbnail':'thumbnails/power_120.png'},
   '51':{'type':'power_module','file':'power_160a.glb','thumbnail':'thumbnails/power_160.png'},
   '60':{'type':'flight_controller','file':'fc_v1.glb','thumbnail':'thumbnails/fc_v1.png'},
   '61':{'type':'flight_controller','file':'fc_v2.glb','thumbnail':'thumbnails/fc_v2.png'},
   '70':{'type':'gnss','file':'gnss_m8n.glb','thumbnail':'thumbnails/gnss_m8n.png'},
   '80':{'type':'payload','file':'payload_camera_300g.glb','thumbnail':'thumbnails/payload_camera.png'}
 },
 'motorDirection':{'M1':'CCW','M2':'CW','M3':'CCW','M4':'CW'},
 'referenceComplete':'eduquad650_reference.glb'
}
(MODEL_DIR/'asset_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print('generated at', MODEL_DIR)
