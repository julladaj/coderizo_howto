import bpy, math, random, os, json
from mathutils import Vector
OUT = r'C:\Users\Admin\Desktop\coderizo\hedgehog_model'
os.makedirs(OUT, exist_ok=True)
random.seed(18)
scene=bpy.context.scene
col=bpy.data.collections.new('Cyberpunk_Hedgehog'); scene.collection.children.link(col)
root=bpy.data.objects.new('Cyberpunk_Hedgehog_Root',None); col.objects.link(root)
def mat(name,color,metal=0,rough=.45,emit=0):
 m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
 n=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
 n.inputs['Base Color'].default_value=(*color,1); n.inputs['Metallic'].default_value=metal; n.inputs['Roughness'].default_value=rough
 if emit: n.inputs['Emission Color'].default_value=(*color,1); n.inputs['Emission Strength'].default_value=emit
 return m
navy=mat('Midnight blue',(.018,.055,.10)); teal=mat('Jacket petrol',(.015,.36,.40),.2); fur=mat('Warm ivory fur',(.76,.57,.35)); cream=mat('Muzzle cream',(.95,.79,.54)); dark=mat('Graphite hardware',(.025,.035,.05),.75,.28); cyan=mat('Cyan LEDs',(.005,.8,1),.3,.22,2); silver=mat('Brushed titanium',(.36,.44,.50),.8,.28); pink=mat('Inner ears',(.44,.22,.16)); white=mat('Eye white',(.88,.94,.91)); black=mat('Pupils and nose',(.008,.012,.018),.1,.2); iris=mat('Turquoise iris',(.005,.48,.56),.3,.18); quill=mat('Blue quills',(.015,.15,.23),.25); tip=mat('Ivory quill tips',(.68,.76,.68)); hat=mat('Beanie teal',(.015,.30,.33))
def own(o,name,m):
 o.name=name
 for c in list(o.users_collection): c.objects.unlink(o)
 col.objects.link(o); o.parent=root
 o.data.materials.append(m)
 if o.type=='MESH':
  for f in o.data.polygons:f.use_smooth=True
 return o
def ell(name,loc,scale,m,seg=32,rings=20):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=seg,ring_count=rings,location=loc);o=own(bpy.context.object,name,m);o.scale=scale;return o
def cube(name,loc,scale,m,bevel=.06):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=own(bpy.context.object,name,m);o.scale=scale
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 if bevel:
  mod=o.modifiers.new('Soft manufactured edges','BEVEL');mod.width=bevel;mod.segments=3
  bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name)
 return o
def line(name,pts,r,m):
 cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.resolution_u=12;cu.bevel_depth=r;cu.bevel_resolution=3
 sp=cu.splines.new('BEZIER');sp.bezier_points.add(len(pts)-1)
 for p,co in zip(sp.bezier_points,pts):p.co=co;p.handle_left_type='AUTO';p.handle_right_type='AUTO'
 o=bpy.data.objects.new(name,cu);col.objects.link(o);o.parent=root;cu.materials.append(m);return o
def cone_between(name,a,b,r1,r2,m):
 d=Vector(b)-Vector(a);bpy.ops.mesh.primitive_cone_add(vertices=10,radius1=r1,radius2=r2,depth=d.length,location=(Vector(a)+Vector(b))/2)
 o=own(bpy.context.object,name,m);o.rotation_euler=d.to_track_quat('Z','Y').to_euler();return o
# Bust front faces -Y; base at Z=0.
ell('Jacket torso',(0,0,.55),(1.02,.48,.69),navy)
for s in [-1,1]:
 o=ell('Jacket shoulder',(s*.82,.015,.48),(.43,.47,.57),teal);o.rotation_euler.y=s*-.3
 o=ell('Front jacket panel',(s*.48,-.34,.56),(.39,.18,.58),teal);o.rotation_euler.y=s*-.18
 line('Jacket lapel',[(s*.24,-.51,.08),(s*.35,-.56,.55),(s*.58,-.43,1.04)],.065,navy)
 line('Zipper rail',[(s*.18,-.50,.08),(s*.27,-.56,.55),(s*.49,-.48,.98)],.018,silver)
 for i in range(17):cube('Zipper tooth',(s*(.18+i*.016),-.575,.12+i*.047),(.035,.018,.014),silver,.003)
 line('Shoulder seam',[(s*.63,-.39,.95),(s*.94,-.37,.77),(s*1.12,-.24,.51)],.018,navy)
 cube('Shoulder armor',(s*1.08,-.22,.62),(.16,.12,.30),dark)
 cube('Sleeve LED',(s*1.08,-.29,.64),(.045,.018,.17),cyan,.012)
 line('Chest circuit',[(s*.6,-.535,.20),(s*.6,-.535,.35),(s*.73,-.49,.46)],.012,cyan)
ell('Neck',(0,-.02,1.12),(.43,.35,.66),cream)
ell('Head',(0,0,1.94),(.70,.57,.76),fur)
# Layered swept quills, actual tapered geometry on back and silhouette.
for row in range(7):
 theta=.20+row*.37
 for j in range(13):
  phi=2*math.pi*j/13 + (row%2)*.22
  x=.67*math.sin(theta)*math.cos(phi);z=2.00+.77*math.cos(theta);y=.13+.44*math.sin(theta)*math.sin(phi)
  if y<-.02:continue
  a=Vector((x,y,z));direction=Vector((x*.65,.45+max(y,0)*.5,(z-2)*.38-.16)).normalized();length=random.uniform(.38,.62)
  b=a+direction*length;mid=a+direction*length*.79
  cone_between('Swept blue quill',a,mid,.12, .035,quill if j%3 else navy)
  cone_between('Pale quill tip',mid,b,.035,0,tip)
for s in [-1,1]:
 ell('Ear',(s*.66,-.07,2.17),(.22,.13,.29),fur)
 ell('Inner ear',(s*.68,-.173,2.18),(.145,.035,.205),pink)
 ell('Cheek',(s*.37,-.41,1.77),(.35,.24,.31),cream)
 ell('Eye white',(s*.285,-.508,2.04),(.225,.10,.18),white)
 ell('Iris',(s*.28,-.597,2.045),(.091,.035,.117),iris)
 ell('Pupil',(s*.28,-.626,2.048),(.043,.015,.084),black)
 ell('Eye glint',(s*.28-.025,-.642,2.092),(.022,.009,.029),white,16,12)
 line('Eyebrow',[(s*.10,-.55,2.24),(s*.28,-.56,2.29),(s*.47,-.49,2.25)],.041,navy)
ell('Chin',(0,-.36,1.58),(.43,.29,.23),cream)
ell('Muzzle',(0,-.61,1.84),(.33,.27,.21),cream)
ell('Nose',(0,-.862,1.92),(.13,.075,.085),black)
line('Smile',[(-.34,-.61,1.72),(-.19,-.72,1.675),(0,-.75,1.66),(.22,-.71,1.70),(.34,-.62,1.76)],.012,black)
# Open glasses preserve eye visibility without transmission sorting.
for s in [-1,1]:
 pts=[(s*.075,-.64,2.19),(s*.28,-.66,2.235),(s*.535,-.57,2.17),(s*.52,-.59,1.955),(s*.30,-.674,1.90),(s*.10,-.655,1.96),(s*.075,-.64,2.19)]
 line('Glasses frame',pts,.035,dark)
 line('Glasses temple',[(s*.52,-.58,2.16),(s*.70,-.25,2.15),(s*.71,.015,2.10)],.033,dark)
 cube('Glasses LED',(s*.53,-.607,2.16),(.078,.025,.035),cyan,.008)
line('Glasses bridge',[(-.08,-.65,2.17),(0,-.68,2.19),(.08,-.65,2.17)],.027,dark)
# Beanie crown and ribbed cuff.
ell('Beanie crown',(0,.055,2.43),(.64,.51,.36),navy)
for i in range(56):
 a=2*math.pi*i/56;x=.645*math.cos(a);y=.515*math.sin(a)+.045
 line('Knitted cuff rib',[(x,y,2.38),(x*1.01,y,2.49),(x*.94,y*.95,2.60)],.021,hat)
badge=cube('Beanie titanium badge',(.49,-.32,2.56),(.19,.05,.08),dark,.015);badge.rotation_euler.y=.3
cube('Hat status light',(.49,-.355,2.56),(.055,.012,.022),cyan,.005)
# Headphones around neck, cups face diagonally forward.
line('Headphone headband',[(-.57,-.26,1.10),(-.65,.16,1.27),(0,.36,1.38),(.65,.16,1.27),(.57,-.26,1.10)],.07,dark)
for s in [-1,1]:
 ell('Headphone cushion',(s*.53,-.38,1.02),(.23,.17,.32),navy)
 ell('Headphone metal housing',(s*.55,-.52,1.03),(.21,.075,.275),silver)
 ell('Headphone shell',(s*.55,-.585,1.03),(.18,.055,.24),dark)
 pts=[(s*.55+.145*math.cos(a*math.pi/24),-.638,1.03+.205*math.sin(a*math.pi/24)) for a in range(49)]
 line('Headphone illuminated ring',pts,.017,cyan)
 ell('Headphone center',(s*.55,-.645,1.03),(.055,.012,.065),teal)
# Stable base, no environment geometry exported.
cube('Bust flat base',(0,0,.035),(1.64,.72,.07),dark,.035)
for o in list(col.objects):
 if o.type=='CURVE':
  bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.convert(target='MESH');o.select_set(False)
for o in col.objects:
 if o.type=='MESH':
  bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.select_set(False)
root['description']='Reference-inspired stylized cyberpunk hedgehog bust; static mesh, no rig.'
root['reference']='Cyberpunk Hedgehog IT Expert.png'
# Studio setup in a separate collection.
studio=bpy.data.collections.new('Studio_not_exported');scene.collection.children.link(studio)
def studio_obj(o):
 for c in list(o.users_collection):c.objects.unlink(o)
 studio.objects.link(o)
def aim(o,p):o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(3.3,-6.5,3.05));cam=bpy.context.object;studio_obj(cam);aim(cam,(0,0,1.45));cam.data.type='ORTHO';cam.data.ortho_scale=3.6;scene.camera=cam
for name,loc,power,color,size in [('Key',(-3,-4,6),700,(.75,.9,1),4),('Fill',(4,-2,3),500,(.4,.85,1),3),('Rim',(1,3,4),900,(.1,.8,1),3)]:
 bpy.ops.object.light_add(type='AREA',location=loc);l=bpy.context.object;studio_obj(l);l.name=name;l.data.energy=power;l.data.color=color;l.data.shape='DISK';l.data.size=size;aim(l,(0,0,1.5))
scene.world.color=(.08,.08,.08)
scene.render.resolution_x=900;scene.render.resolution_y=900;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=True
try:scene.render.engine='CYCLES';scene.cycles.samples=32
except:pass
bpy.ops.object.select_all(action='DESELECT')
for o in col.objects:o.select_set(True)
bpy.context.view_layer.objects.active=root
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'cyberpunk_hedgehog.glb'),export_format='GLB',use_selection=True,export_cameras=False,export_lights=False)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'cyberpunk_hedgehog.blend'))
scene.render.filepath=os.path.join(OUT,'preview.png')
meshes=[o for o in col.objects if o.type=='MESH']
stats={'mesh_objects':len(meshes),'triangles':sum(len(p.vertices)-2 for o in meshes for p in o.data.polygons),'materials':len(set(m.name for o in meshes for m in o.data.materials)), 'glb_bytes':os.path.getsize(os.path.join(OUT,'cyberpunk_hedgehog.glb'))}
with open(os.path.join(OUT,'asset_stats.json'),'w') as f:json.dump(stats,f,indent=2)
print(stats)
