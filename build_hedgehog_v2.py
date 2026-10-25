"""Reproducible reference-driven Blender asset. Run in a separate background Blender."""
import bpy, math, random, os, json, sys
import numpy as np
from mathutils import Vector, Matrix
from math import sin, cos, pi
ROOT=os.path.dirname(os.path.abspath(__file__))
OUT=os.path.join(ROOT,'hedgehog_model_v2')
TEX=os.path.join(OUT,'textures')
os.makedirs(TEX,exist_ok=True)
random.seed(207); rng=np.random.default_rng(207)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
model=bpy.data.collections.new('Hedgehog_V2_Editable');scene.collection.children.link(model)
studio=bpy.data.collections.new('Studio_Not_Exported');scene.collection.children.link(studio)
reference=bpy.data.collections.new('Reference_Not_Exported');scene.collection.children.link(reference)
ref_image=bpy.data.images.load(os.path.join(ROOT,'Cyberpunk Hedgehog IT Expert.png'));ref_image.pack()
ref_empty=bpy.data.objects.new('Original_reference_image',None);reference.objects.link(ref_empty)
ref_empty.empty_display_type='IMAGE';ref_empty.data=ref_image;ref_empty.empty_display_size=4
ref_empty.location=(-3,1,2);ref_empty.rotation_euler.x=pi/2;ref_empty.hide_render=True;ref_empty.hide_set(True)
root=bpy.data.objects.new('Cyberpunk_Hedgehog_V2',None);model.objects.link(root)

def image(name,array,noncolor=False):
 h,w=array.shape[:2]
 if array.ndim==2: array=np.repeat(array[:,:,None],3,axis=2)
 rgba=np.ones((h,w,4),np.float32);rgba[:,:,:3]=np.clip(array,0,1)
 im=bpy.data.images.new(name,width=w,height=h,alpha=False)
 if noncolor: im.colorspace_settings.name='Non-Color'
 im.pixels.foreach_set(rgba.ravel());im.filepath_raw=os.path.join(TEX,name+'.png');im.file_format='PNG';im.save();im.pack()
 return im

def normal_image(name,h,strength=1):
 gy,gx=np.gradient(h)
 n=np.stack([-gx*strength,-gy*strength,np.ones_like(h)],axis=2)
 n/=np.linalg.norm(n,axis=2,keepdims=True)
 return image(name,n*.5+.5,True)

def texture_fields(n):
 v,u=np.mgrid[0:n,0:n].astype(np.float32)/n
 noise=rng.normal(0,1,(n,n)).astype(np.float32)
 return u,v,noise

# All final shading uses image textures / core PBR; no procedural-only shading.
u,v,noise=texture_fields(2048)
strokes=(.5+.5*np.sin(2*pi*(u*780+1.8*np.sin(v*28))))**14
strokes*=.4+.6*(.5+.5*np.sin(2*pi*(v*115+u*53)))
furheight=.45*strokes+.06*noise
fur_normal=normal_image('fur_micro_normal_2k',furheight,4)
z=2.72+.85*np.cos(v*pi);x=.82*np.cos(u*2*pi)*np.sin(v*pi);y=.7*np.sin(u*2*pi)*np.sin(v*pi)
brown=np.clip((z-2.86)*5,0,1)
# Cream brow markings and pale central blaze under the cuff.
blaze=np.exp(-(x/.115)**2)*np.clip((3.34-z)*5,0,1)
brown*=1-.85*blaze
cream=np.array([.83,.715,.57]);tan=np.array([.31,.18,.09])
face=cream[None,None,:]*(1-brown[:,:,None])+tan[None,None,:]*brown[:,:,None]
face*=np.clip(.91+strokes[:,:,None]*.16+noise[:,:,None]*.018,.72,1.15)
face_img=image('face_fur_basecolor_2k',face)
cream_tex=image('cream_fur_basecolor_2k',np.array([.86,.75,.61])[None,None,:]*np.clip(.94+strokes[:,:,None]*.12+noise[:,:,None]*.015,.7,1.1))

u,v,noise=texture_fields(1024)
weave=(np.sin(u*2*pi*180)*np.sin(v*2*pi*180))*.24+noise*.07
cloth_normal=normal_image('woven_fabric_normal_1k',weave,3.5)
cloth_rgb=np.array([.035,.55,.59])[None,None,:]*(.88+.10*np.sin(u*2*pi*180)[:,:,None]+noise[:,:,None]*.06)
cloth_img=image('jacket_teal_woven_1k',cloth_rgb)
navy_img=image('navy_fabric_1k',np.array([.025,.075,.135])[None,None,:]*(.94+weave[:,:,None]*.2))
rough_img=image('fabric_roughness_1k',np.clip(.74+weave*.12,.5,.95),True)
# A continuous chevron stitch field, rather than widely spaced rods.
wave=np.abs(((u*64)%1)-.5)*2
stitch=np.cos(2*pi*(v*80-wave*.7))*.4+np.cos(u*2*pi*64)*.17+noise*.035
knit_normal=normal_image('knitted_stitches_normal_1k',stitch,5)
knit_img=image('knitted_teal_1k',np.array([.028,.48,.50])[None,None,:]*(.91+stitch[:,:,None]*.19))
qbase=np.array([.015,.12,.18])[None,None,:]
qcyan=np.array([.045,.42,.47])[None,None,:]
stripe=(.5+.5*np.cos(u*2*pi*8+v*3))**8
q=qbase*(1-stripe[:,:,None]*.63)+qcyan*stripe[:,:,None]*.63
fade=np.clip((v-.65)/.34,0,1)**1.3
q=q*(1-fade[:,:,None])+np.array([.79,.81,.69])[None,None,:]*fade[:,:,None]
q*=.88+.10*np.sin(u*2*pi*155+np.sin(v*25)*2)[:,:,None]+noise[:,:,None]*.025
quill_img=image('quill_blue_ivory_1k',q)
quill_normal=normal_image('quill_fibers_normal_1k',np.sin(u*2*pi*155+np.sin(v*25)*2)*.15+noise*.035,3)
# Radial iris detail in disc UV coordinates.
dx=(u-.5)*2;dy=(v-.5)*2;r=np.sqrt(dx*dx+dy*dy);ang=np.arctan2(dy,dx)
rad=(.5+.5*np.sin(ang*180+np.sin(r*32)*3))*.36+(.5+.5*np.sin(ang*73-r*19))*.25
iv=np.array([.016,.42,.48])[None,None,:]*(.58+rad[:,:,None])
iv*=np.clip((1-r)*8, .12,1)[:,:,None]
iris_img=image('turquoise_radial_iris_1k',iv)

def mat(name,color,metal=0,rough=.5,base=None,normal=None,ns=.25,emit=0,alpha=1):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,alpha);m.use_nodes=True
 n=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');n.inputs['Base Color'].default_value=(*color,1)
 n.inputs['Metallic'].default_value=metal;n.inputs['Roughness'].default_value=rough
 if base:
  t=m.node_tree.nodes.new('ShaderNodeTexImage');t.image=base;m.node_tree.links.new(t.outputs['Color'],n.inputs['Base Color'])
 if normal:
  t=m.node_tree.nodes.new('ShaderNodeTexImage');t.image=normal
  b=m.node_tree.nodes.new('ShaderNodeNormalMap');b.inputs['Strength'].default_value=ns
  m.node_tree.links.new(t.outputs['Color'],b.inputs['Color']);m.node_tree.links.new(b.outputs['Normal'],n.inputs['Normal'])
 if emit:n.inputs['Emission Color'].default_value=(*color,1);n.inputs['Emission Strength'].default_value=emit
 if alpha<1:
  n.inputs['Alpha'].default_value=alpha
  try:m.surface_render_method='DITHERED'
  except:pass
  m.use_backface_culling=True
 return m
FUR=mat('01_Face_cream_and_brown',(.8,.65,.45),rough=.69,base=face_img,normal=fur_normal,ns=.32)
CREAM=mat('02_Neck_cream_fur',(.8,.7,.55),rough=.76,base=cream_tex,normal=fur_normal,ns=.3)
TEAL=mat('03_Teal_technical_fabric',(.02,.4,.43),rough=.67,base=cloth_img,normal=cloth_normal,ns=.42)
NAVY=mat('04_Navy_woven_panels',(.02,.06,.12),rough=.8,base=navy_img,normal=cloth_normal,ns=.5)
KNIT=mat('05_Teal_knitted_cuff',(.02,.35,.38),rough=.83,base=knit_img,normal=knit_normal,ns=.6)
DARK=mat('06_Gunmetal_frames',(.025,.033,.047),.78,.28)
SILVER=mat('07_Brushed_titanium',(.35,.40,.44),.85,.32)
CYAN=mat('08_Cyan_status_lights',(.005,.78,.9),.15,.25,emit=1.3)
QMAT=mat('09_Quills_blue_to_ivory',(.01,.15,.2),.16,.42,base=quill_img,normal=quill_normal,ns=.38)
PINK=mat('10_Ear_warm_interior',(.40,.19,.13),rough=.78,normal=fur_normal,ns=.15)
NOSE=mat('11_Nose_charcoal',(.016,.010,.009),rough=.38,normal=cloth_normal,ns=.12)
WHITE=mat('12_Warm_sclera',(.72,.77,.72),rough=.27)
IRIS=mat('13_Radial_turquoise_iris',(.01,.4,.45),rough=.22,base=iris_img)
PUPIL=mat('14_Pupil',(.002,.006,.009),rough=.13)
LENS=mat('15_Tinted_glasses_lens',(.05,.19,.23),.08,.14,alpha=.14)
HAIR_LIGHT=mat('16_Cream_fur_fibers',(.71,.56,.40),rough=.82)
HAIR_BROWN=mat('17_Brown_fur_fibers',(.19,.09,.037),rough=.82)
LID=mat('18_Lids_and_brows',(.085,.046,.026),rough=.72)

def mesh(name,verts,faces,m,uvs=None):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update()
 o=bpy.data.objects.new(name,me);model.objects.link(o);o.parent=root
 if m:me.materials.append(m)
 for p in me.polygons:p.use_smooth=True
 if uvs:
  layer=me.uv_layers.new(name='UVMap')
  for p in me.polygons:
   for li in p.loop_indices:layer.data[li].uv=uvs[me.loops[li].vertex_index]
 return o
def own(o,name,m):
 o.name=name
 for c in list(o.users_collection):c.objects.unlink(o)
 model.objects.link(o);o.parent=root;o.data.materials.append(m)
 for f in o.data.polygons:f.use_smooth=True
 return o
def ell(name,loc,scale,m,seg=48,rings=32):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=seg,ring_count=rings,location=loc)
 o=own(bpy.context.object,name,m);o.scale=scale
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 return o
def box(name,loc,scale,m,bevel=.025):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=own(bpy.context.object,name,m);o.scale=scale
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 if bevel:
  md=o.modifiers.new('Manufactured bevel','BEVEL');md.width=bevel;md.segments=3
  bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=md.name)
 return o
def curve(name,pts,r,m,res=5):
 cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.resolution_u=res;cu.bevel_depth=r;cu.bevel_resolution=2
 sp=cu.splines.new('BEZIER');sp.bezier_points.add(len(pts)-1)
 for i,(p,co) in enumerate(zip(sp.bezier_points,pts)):
  p.co=co;p.handle_left_type='AUTO';p.handle_right_type='AUTO'
  if 'brow' in name.lower():p.radius=.15 if i in [0,len(pts)-1] else 1
 o=bpy.data.objects.new(name,cu);model.objects.link(o);o.parent=root;cu.materials.append(m);return o
def apply(o,mod):
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name)
def smooth(o,factor=.6,iterations=4):
 md=o.modifiers.new('Sculpt smoothing','SMOOTH');md.factor=factor;md.iterations=iterations;apply(o,md)
def spherical_uv(o,center=(0,0,2.72)):
 uv=o.data.uv_layers.new(name='UVMap')
 for p in o.data.polygons:
  coords=[]
  for vi in p.vertices:
   co=o.matrix_world@o.data.vertices[vi].co-Vector(center)
   theta=math.atan2(co.y,co.x)/(2*pi)%1
   phi=math.acos(max(-1,min(1,co.z/max(co.length,.00001))))/pi
   coords.append([theta,phi])
  if max(a[0] for a in coords)-min(a[0] for a in coords)>.5:
   coords=[[a+1 if a<.5 else a,b] for a,b in coords]
  for li,co in zip(p.loop_indices,coords):uv.data[li].uv=co

# Sculpt a single continuous face: cheeks and muzzle blend into the jaw.
parts=[ell('Skull',(0,.015,2.88),(.76,.56,.70),FUR),
 ell('Jaw',(0,-.19,2.49),(.66,.49,.41),FUR),
 ell('Muzzle',(0,-.72,2.72),(.48,.48,.275),FUR),
 ell('Tapered_nose_bridge',(0,-1.085,2.845),(.17,.15,.135),FUR),
 ell('Left cheek',(-.44,-.34,2.63),(.32,.28,.29),FUR),
 ell('Right cheek',(.44,-.34,2.63),(.32,.28,.29),FUR)]
bpy.ops.object.select_all(action='DESELECT')
for o in parts:o.select_set(True)
bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();head=bpy.context.object;head.name='Sculpted_continuous_face'
rem=head.modifiers.new('Unified sculpt surface','REMESH');rem.mode='VOXEL';rem.voxel_size=.025;rem.use_smooth_shade=True;apply(head,rem);smooth(head,.9,6)
spherical_uv(head)
nv=[];nf=[];nu=[]
for k,(zz,rx,ry) in enumerate([(1.30,.36,.27),(1.55,.40,.30),(1.85,.45,.34),(2.12,.49,.37),(2.40,.53,.39)]):
 for j in range(65):
  a=j*2*pi/64;nv.append((rx*cos(a),-.015+ry*sin(a),zz));nu.append((j/64,zz))
for k in range(4):
 for j in range(64):b=k*65+j;nf.append((b,b+1,b+66,b+65))
neck=mesh('Tapered_fur_neck',nv,nf,CREAM,nu)
md=neck.modifiers.new('Smooth_neck_transition','SUBSURF');md.levels=2;apply(neck,md)
# Microfibers are geometry, so glTF reproduces the silhouette without hair systems.
def add_fibers(surface,count,name,neck=False):
 me=surface.data;me.calc_loop_triangles();tris=list(me.loop_triangles)
 areas=np.array([t.area for t in tris]);choices=rng.choice(len(tris),count,p=areas/areas.sum())
 vs=[];fs=[];mi=[]
 for ti in choices:
  t=tris[ti];a,b,c=[surface.matrix_world@me.vertices[i].co for i in t.vertices]
  w1,w2=random.random(),random.random()
  if w1+w2>1:w1,w2=1-w1,1-w2
  p=a+(b-a)*w1+(c-a)*w2;n=(b-a).cross(c-a).normalized()
  if not neck:
   if p.y> .28 or p.z>3.48:continue
   if p.y<-.40 and 2.80<p.z<3.09 and .09<abs(p.x)<.62:continue
   if p.y<-.91 and p.z>2.68:continue
  elif p.y>.15:continue
  flow=Vector((p.x*.25,.05,-1)) if p.z<3.0 else Vector((p.x*.15,.6,.35))
  tangent=flow-n*flow.dot(n)
  if tangent.length<.01:tangent=Vector((1,0,0))
  tangent.normalize();side=n.cross(tangent).normalized()
  length=random.uniform(.014,.036);width=random.uniform(.00045,.0011)
  start=p+n*.002;idx=len(vs)
  for k in range(3):
   tt=k/2;pos=start+tangent*(length*tt)+n*(length*.10*sin(tt*pi/2))
   rad=width*(1-tt)*.8+.00007
   vs.extend([tuple(pos-side*rad),tuple(pos+side*rad)])
  fs.extend([(idx,idx+1,idx+3,idx+2),(idx+2,idx+3,idx+5,idx+4)])
  mi.extend([1 if not neck and p.z>2.94 and abs(p.x)>.13 else 0]*2)
 o=mesh(name,vs,fs,HAIR_LIGHT);o.data.materials.append(HAIR_BROWN)
 for p,i in zip(o.data.polygons,mi):p.material_index=i
 return o
add_fibers(head,19000,'Face_fine_fur_geometry')
add_fibers(neck,7000,'Neck_fine_fur_geometry',True)

# Shape ears as recessed bowls with a thick softly curled rim.
for s in [-1,1]:
 center=Vector((s*.73,-.015,3.0));vs=[];fs=[];uv=[]
 for ri in range(9):
  rr=ri/8
  for j in range(49):
   a=2*pi*j/48
   vs.append(tuple(center+Vector((s*.170*rr*cos(a),-.075-.105*rr*rr,.22*rr*sin(a)))))
   uv.append((.5+.5*rr*cos(a),.5+.5*rr*sin(a)))
 for ri in range(8):
  for j in range(48):a=ri*49+j;fs.append((a,a+1,a+50,a+49))
 ear=mesh('Recessed_ear_interior',vs,fs,PINK,uv)
 pts=[tuple(center+Vector((s*.170*cos(j*2*pi/48),-.18,.22*sin(j*2*pi/48)))) for j in range(49)]
 curve('Furry_ear_rolled_rim',pts,.038,CREAM,3)
 # Short cream tufts along ear edge.
 for j in range(16):
  a=j*2*pi/16;p=center+Vector((s*.177*cos(a),-.17,.225*sin(a)))
  curve('Ear_edge_fiber',[p,p+Vector((s*.014*cos(a),-.008,.018*sin(a)))],.0018,HAIR_LIGHT,1)

# Eyes: restrained almond apertures, partially lowered upper lids.
def eye_patch(s):
 vs=[];uv=[];fs=[]
 for ri in range(9):
  rr=ri/8
  for j in range(49):
   a=j*2*pi/48;xx=.255*rr*cos(a);zz=.132*rr*sin(a)*(abs(sin(a))**.25)
   yy=-.705+.09*rr*rr+.07*abs(xx)
   vs.append((s*(.33+xx),yy,2.94+zz));uv.append((.5+.5*rr*cos(a),.5+.5*rr*sin(a)))
 for ri in range(8):
  for j in range(48):a=ri*49+j;fs.append((a,a+1,a+50,a+49) if s>0 else (a+49,a+50,a+1,a))
 return mesh('Almond_sclera',vs,fs,WHITE,uv)
def disc(name,c,rx,rz,m,normal=Vector((0,-1,0)),segments=64):
 n=Vector(normal).normalized();up=Vector((0,0,1));right=up.cross(n).normalized();up=n.cross(right).normalized()
 vs=[tuple(c)];uv=[(.5,.5)]
 for i in range(segments):
  a=i*2*pi/segments;vs.append(tuple(Vector(c)+right*(rx*cos(a))+up*(rz*sin(a))));uv.append((.5+.5*cos(a),.5+.5*sin(a)))
 fs=[(0,i+1,(i+1)%segments+1) for i in range(segments)]
 return mesh(name,vs,fs,m,uv)
for s in [-1,1]:
 eye_patch(s)
 disc('Iris_radial',Vector((s*.31-.018,-.718,2.975)),.094,.106,IRIS)
 ell('Pupil',(s*.31-.018,-.725,2.978),(.040,.012,.077),PUPIL,32,20)
 ell('Eye_catchlight',(s*.31-.043,-.742,3.020),(.017,.006,.022),WHITE,16,12)
 curve('Upper_eyelid',[(s*.08,-.623,2.948),(s*.21,-.669,3.047),(s*.38,-.67,3.061),(s*.585,-.60,2.968)],.021,LID)
 curve('Lower_eyelid',[(s*.08,-.623,2.925),(s*.31,-.65,2.817),(s*.585,-.60,2.95)],.018,CREAM)
 curve('Swept_brown_brow',[(s*.10,-.57,3.11),(s*.29,-.586,3.16),(s*.51,-.49,3.16)],.019,LID)
 # Cream eyebrow markings belong to the fur surface rather than raised cords.
nose=ell('Rounded_triangular_nose',(0,-1.265,2.882),(.145,.09,.10),NOSE,48,32)
for vtx in nose.data.vertices:
 zz=vtx.co.z/.1;vtx.co.x*=.68+.25*zz
for s in [-1,1]:ell('Nostril',(s*.073,-1.331,2.86),(.033,.013,.019),PUPIL,20,12)
curve('Mouth_smile',[(-.35,-.72,2.509),(-.22,-.854,2.475),(0,-.917,2.463),(.22,-.854,2.478),(.35,-.72,2.53)],.0085,NOSE,9)
curve('Subtle_lower_lip',[(-.20,-.838,2.452),(0,-.89,2.439),(.22,-.82,2.463)],.008,CREAM)

# Swept leaf-like quills with longitudinal UVs and pale tips.
qvs=[];qfs=[];quv=[]
for row in range(11):
 theta=.10+row*.225
 for j in range(18):
  phi=.02+j*pi/17 + random.uniform(-.04,.04)
  a=Vector((.70*sin(theta)*cos(phi),.17+.47*sin(theta)*sin(phi),2.87+.76*cos(theta)+max(0,.15-row*.04)))
  d=Vector((a.x*.55,.58,(a.z-3.02)*.68-.18)).normalized()
  length=random.uniform(.53,.80)*(1 if row<8 else .83)
  bend=Vector((a.x*.10,.13,-.10));side=Vector((0,0,1)).cross(d).normalized();up=d.cross(side).normalized()
  width=random.uniform(.145,.205);depth=width*.36;idx=len(qvs)
  for k in range(10):
   t=k/9;center=a+d*(length*t)+bend*(t*t);profile=(sin(pi*(.12+.88*t))**.78)*(.95-.30*t)
   if k==9:profile=.002
   for rj in range(9):
    aa=2*pi*rj/8;ridge=1+.15*cos(aa*3)
    p=center+side*(width*profile*cos(aa))+up*(depth*profile*sin(aa)*ridge)
    qvs.append(tuple(p));quv.append((rj/8,t))
  for k in range(9):
   for rj in range(8):b=idx+k*9+rj;qfs.append((b,b+1,b+10,b+9))
quills=mesh('Layered_swept_blue_quills',qvs,qfs,QMAT,quv)

# Continuous knitted band following the forehead, with densely spaced ribs.
vs=[];fs=[];uv=[]
for k in range(9):
 t=k/8
 for j in range(161):
  a=j*2*pi/160;rx=.75-.045*t+.015*sin(t*pi);ry=.575-.025*t
  zz=3.38+.255*t+.035*sin(a)
  vs.append((rx*cos(a),.025+ry*sin(a),zz));uv.append((j/160,t*.65))
for k in range(8):
 for j in range(160):b=k*161+j;fs.append((b,b+1,b+162,b+161))
mesh('Continuous_folded_knit_cuff',vs,fs,KNIT,uv)
crown=ell('Navy_beanie_crown',(0,.08,3.59),(.70,.53,.19),NAVY)
for j in range(128):
 a=j*2*pi/128
 pts=[]
 for t in [0,.33,.66,1]:
  rx=.753-.045*t+.015*sin(t*pi);ry=.579-.025*t
  pts.append((rx*cos(a),.025+ry*sin(a),3.38+.255*t+.035*sin(a)))
 curve('Fine_cuff_rib',pts,.0035,KNIT,2)
badge=box('Beanie_clipped_badge',(.58,-.387,3.58),(.22,.045,.085),DARK,.012);badge.rotation_euler.y=.42;badge.rotation_euler.z=.40
curve('Beanie_badge_inlay',[(.53,-.426,3.60),(.61,-.388,3.565)],.009,CYAN)

# Angular full frames with inset lenses and short HUD graphics.
def round_poly(poly):
 out=[]
 for i,p in enumerate(poly):
  q=poly[(i+1)%len(poly)];out.extend([(p[0]*.8+q[0]*.2,p[1]*.8+q[1]*.2),(p[0]*.2+q[0]*.8,p[1]*.2+q[1]*.8)])
 return out
for s in [-1,1]:
 poly=round_poly([(.065,3.118),(.22,3.16),(.52,3.13),(.643,3.055),(.60,2.793),(.43,2.758),(.15,2.80),(.065,2.90)])
 n=len(poly);cx=.345;cz=2.957;vs=[];uv=[]
 for depth in [0,.052]:
  for inset in [0,1]:
   for x,z in poly:
    if inset:x=cx+(x-cx)*.86;z=cz+(z-cz)*.80
    y=-.837+.30*x*x+depth
    vs.append((s*x,y,z));uv.append((x,z))
 fs=[]
 for j in range(n):
  k=(j+1)%n
  fs.extend([(j,k,n+k,n+j),(2*n+j,3*n+j,3*n+k,2*n+k),(j,2*n+j,2*n+k,k),(n+j,n+k,3*n+k,3*n+j)])
 frame=mesh('Angular_glasses_frame',vs,fs,DARK,uv)
 # Correct outward normals after mirrored construction.
 bpy.context.view_layer.objects.active=frame;frame.select_set(True)
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.normals_make_consistent(inside=False);bpy.ops.object.mode_set(mode='OBJECT');frame.select_set(False)
 rim=[(s*x,-.841+.30*x*x,z) for x,z in poly];rim.append(rim[0]);curve('Frame_edge_titanium',rim,.0045,SILVER,2)
 lensvs=[(s*(cx+(x-cx)*.86),-.818+.30*(cx+(x-cx)*.86)**2,cz+(z-cz)*.80) for x,z in poly]
 lens=mesh('Blue_tinted_lens',lensvs,[tuple(range(n))] if s>0 else [tuple(reversed(range(n)))],LENS,[(x,z) for x,z in poly])
 hinge=box('Angular_hinge',(s*.638,-.703,3.067),(.12,.09,.10),DARK,.013)
 box('Hinge_cyan_status',(s*.645,-.756,3.075),(.075,.013,.024),CYAN,.005)
 curve('Wide_glasses_temple',[(s*.64,-.68,3.06),(s*.79,-.35,3.04),(s*.79,.03,2.95)],.035,DARK)
 curve('Temple_titanium_edge',[(s*.66,-.68,3.09),(s*.81,-.35,3.075),(s*.81,-.02,2.995)],.008,SILVER)
 curve('Temple_Cyan_panel',[(s*.74,-.49,3.065),(s*.78,-.35,3.035)],.016,CYAN)
 for i in range(3):
  x=.43+i*.045;box('Lens_HUD_bottom',(s*x,-.825+.30*x*x,2.815),(.027,.003,.008),CYAN,.002)
 for i in range(3):box('Lens_HUD_side',(s*.13,-.821,2.91+i*.022),(.016,.003,.006),CYAN,.001)
curve('Glasses_nose_bridge',[(-.075,-.83,3.075),(0,-.868,3.09),(.075,-.83,3.075)],.027,DARK)
# Keep all eyewear in front of the projecting muzzle; prevent frame/cheek clipping.
for o in model.objects:
 if o.name.startswith(('Angular_glasses_frame','Frame_edge_titanium','Blue_tinted_lens','Angular_hinge','Hinge_cyan','Wide_glasses_temple','Temple_titanium','Temple_Cyan','Lens_HUD','Glasses_nose_bridge')):
  o.location.y-=.10

# Lift the chin and turn the head slightly independently of the shoulders.
headpivot=bpy.data.objects.new('Head_pose_pivot',None);model.objects.link(headpivot);headpivot.parent=root;headpivot.location=(0,0,2.85)
bpy.context.view_layer.update()
for o in list(model.objects):
 if o.type in ['MESH','CURVE'] and o not in [neck] and not o.name.startswith('Neck_fine'):
  matrix=o.matrix_world.copy();o.parent=headpivot;o.matrix_world=matrix
headpivot.rotation_euler.x=-.14
headpivot.rotation_euler.z=-.035
headpivot.location.x=.07

# Tailored torso loft: broad cropped shoulders, no separate balloon-shaped chest pieces.
before_body=set(model.objects)
levels=[(0,1.37,.49),(.22,1.35,.50),(.50,1.24,.49),(.80,1.10,.46),(1.06,.89,.42),(1.26,.61,.36),(1.43,.46,.32)]
vs=[];fs=[];uv=[]
for k,(z,w,d) in enumerate(levels):
 for j in range(97):
  a=j*2*pi/96;xx=w*cos(a);yy=d*sin(a)
  if yy<0:yy-=.015*sin(9*a+z*7)*sin(z*pi/1.5)
  vs.append((xx,yy,z));uv.append((j/96*2,z))
for k in range(len(levels)-1):
 for j in range(96):b=k*97+j;fs.append((b,b+1,b+98,b+97))
fs.extend([tuple(reversed(range(97))),tuple((len(levels)-1)*97+j for j in range(97))])
torso=mesh('Tailored_navy_jacket_and_shirt',vs,fs,NAVY,uv)
md=torso.modifiers.new('Cloth surface subdivision','SUBSURF');md.levels=2;apply(torso,md)
def front_y(x,z):
 w=float(np.interp(z,[a[0] for a in levels],[a[1] for a in levels]));d=float(np.interp(z,[a[0] for a in levels],[a[2] for a in levels]))
 return -d*math.sqrt(max(.02,1-(x/w)**2))-.025
for s in [-1,1]:
 vs=[];fs=[];uv=[]
 for k in range(25):
  z=k/24*1.16;inside=.10+.22*(z/1.16)**1.5
  outside=float(np.interp(z,[a[0] for a in levels],[a[1] for a in levels]))*.92
  for j in range(17):
   t=j/16;x=inside*(1-t)+outside*t;y=front_y(x,z)-.009*sin(t*pi)*sin(z*12+t*5)
   vs.append((s*x,y,z));uv.append((t,z*1.4))
 for k in range(24):
  for j in range(16):b=k*17+j;fs.append((b,b+1,b+18,b+17) if s>0 else (b+17,b+18,b+1,b))
 panel=mesh('Shaped_teal_jacket_front',vs,fs,TEAL,uv)
 md=panel.modifiers.new('Fabric thickness','SOLIDIFY');md.thickness=.014;apply(panel,md)
 zippts=[]
 for k in range(13):
  z=k/12*1.16;x=.10+.22*(z/1.16)**1.5;zippts.append((s*x,front_y(x,z)-.025,z))
 curve('Dark_zipper_tape',zippts,.026,DARK)
 for k in range(43):
  z=.025+k*.0255;x=.10+.22*(z/1.16)**1.5
  tooth=box('Individual_zipper_tooth',(s*x,front_y(x,z)-.055,z),(.030,.018,.012),SILVER,.002)
 curve('Inner_jacket_piping',[(s*.18,-.53,.02),(s*.25,-.50,.65),(s*.41,-.37,1.17)],.012,TEAL)
 # Tall collar folding around the headphones.
 curve('Raised_hood_outer_roll',[(s*.40,.19,1.56),(s*.65,.03,1.45),(s*.69,-.21,1.22),(s*.47,-.39,1.04)],.083,TEAL)
 curve('Hood_navy_lining',[(s*.36,.15,1.56),(s*.56,-.04,1.44),(s*.60,-.24,1.23),(s*.44,-.38,1.06)],.047,NAVY)
 curve('Hood_edge_stitch',[(s*.43,.14,1.59),(s*.67,-.03,1.43),(s*.70,-.24,1.22),(s*.49,-.40,1.05)],.005,SILVER)
 # Sleeve cross sections maintain a shoulder-to-crop silhouette.
 sv=[];sf=[];su=[]
 for k in range(13):
  t=k/12;center=Vector((s*(.75+.53*t),.045,1.03-.98*t));rw=.28+.03*t;rd=.34-.035*t
  for j in range(49):
   a=j*2*pi/48;p=center+Vector((rw*cos(a),rd*sin(a),.13*cos(a)*s))
   sv.append(tuple(p));su.append((j/48,t*1.5))
 for k in range(12):
  for j in range(48):b=k*49+j;sf.append((b,b+1,b+50,b+49))
 sf.extend([tuple(reversed(range(49))),tuple(12*49+j for j in range(49))])
 sleeve=mesh('Tailored_navy_sleeve',sv,sf,NAVY,su)
 sleeve.data.materials.append(TEAL)
 for p in sleeve.data.polygons:
  cen=p.center
  if cen.y<-.07 and abs(cen.x)<1.16 and cen.z>.62:p.material_index=1
 md=sleeve.modifiers.new('Smooth_shoulders','SUBSURF');md.levels=2;apply(sleeve,md)
 # Overlaid angular shoulder fabric patches and tech armor.
 pts=[(s*.64,-.25,1.15),(s*.90,-.28,1.06),(s*1.10,-.29,.87),(s*1.29,-.28,.45)]
 curve('Sleeve_teal_seam',pts,.036,TEAL)
 curve('Shoulder_double_stitch',[(s*.66,-.293,1.13),(s*.90,-.321,1.04),(s*1.10,-.331,.85)],.0045,SILVER)
 armor=box('Upper_arm_angular_armor',(s*1.15,-.28,.66),(.19,.07,.33),DARK,.025);armor.rotation_euler.y=s*-.25
 trim=box('Arm_armor_titanium_insert',(s*1.15,-.323,.66),(.13,.016,.25),SILVER,.018);trim.rotation_euler.y=s*-.25
 inner=box('Arm_armor_dark_insert',(s*1.15,-.335,.66),(.09,.015,.21),DARK,.012);inner.rotation_euler.y=s*-.25
 led=box('Arm_armor_cyan_LED',(s*1.15,-.347,.66),(.027,.008,.15),CYAN,.005);led.rotation_euler.y=s*-.25
 strap=box('Shoulder_strap',(s*.89,-.22,1.06),(.22,.13,.07),TEAL,.014);strap.rotation_euler.y=s*.3
 clasp=box('Shoulder_strap_buckle',(s*.91,-.29,1.075),(.10,.055,.075),SILVER,.01);clasp.rotation_euler.y=s*.3
 # Distinct diagonal chest applique and inset dark panel.
 pp=[(s*.50,front_y(.50,.10)-.024,.10),(s*.71,front_y(.71,.38)-.024,.38),(s*.74,front_y(.74,.69)-.024,.69),(s*.57,front_y(.57,.53)-.024,.53)]
 mesh('Angular_chest_applique',pp,[(0,1,2,3)],NAVY,[(0,0),(1,0),(1,1),(0,1)])
 curve('Chest_panel_metal_edge',[pp[0],pp[1],pp[2]],.012,SILVER)
 curve('Etched_chest_circuit',[(s*.43,front_y(.43,.08)-.035,.08),(s*.43,front_y(.43,.25)-.035,.25),(s*.53,front_y(.53,.34)-.035,.34),(s*.53,front_y(.53,.45)-.035,.45)],.0045,TEAL)
 # Tension folds rather than inflated chest masses.
 # Folds are sculpted into panel vertices above; do not draw raised cords.
curve('Shirt_collar_teal',[(-.33,-.265,1.38),(0,-.365,1.30),(.33,-.265,1.38)],.021,TEAL)
curve('Shirt_circuit_emblem',[(-.13,-.509,.75),(.04,-.52,.64),(.04,-.53,.42),(.13,-.53,.35)],.009,TEAL)

# Headphone earcups use layered machined profiles and outward-facing axes.
def cup_profile(name,center,normal,profile,m):
 n=Vector(normal).normalized();up=Vector((0,0,1));right=up.cross(n).normalized();up=n.cross(right).normalized()
 vs=[];fs=[];uv=[]
 for k,(r,depth) in enumerate(profile):
  for j in range(65):
   a=j*2*pi/64;p=Vector(center)+n*depth+right*(r*cos(a))+up*(r*1.20*sin(a));vs.append(tuple(p));uv.append((j/64,k/(len(profile)-1)))
 for k in range(len(profile)-1):
  for j in range(64):b=k*65+j;fs.append((b,b+1,b+66,b+65))
 return mesh(name,vs,fs,m,uv)
curve('Headphone_padded_headband',[(-.42,-.25,1.35),(-.60,.13,1.70),(0,.36,1.73),(.60,.13,1.70),(.69,-.31,1.53)],.047,DARK)
curve('Headphone_band_titanium',[(-.44,-.20,1.40),(-.61,.17,1.75),(0,.38,1.78),(.61,.17,1.75),(.71,-.26,1.58)],.014,SILVER)
for s in [-1,1]:
 c=Vector((.65,-.37,1.48) if s>0 else (-.38,-.30,1.30));n=Vector((s*.56,-.82,.08)).normalized()
 cup_profile('Thick_woven_ear_cushion',c,n,[(.18,-.06),(.25,-.045),(.275,.015),(.275,.10),(.24,.135),(.19,.10)],KNIT)
 cup_profile('Headphone_navy_chassis',c,n,[(.246,.09),(.27,.12),(.266,.17),(.24,.19)],DARK)
 cup_profile('Headphone_titanium_bezel',c,n,[(.232,.18),(.249,.19),(.246,.215),(.224,.22)],SILVER)
 cup_profile('Headphone_cyan_light_ring',c,n,[(.208,.217),(.220,.22),(.219,.231),(.207,.233)],CYAN)
 cup_profile('Headphone_machined_face',c,n,[(.001,.255),(.075,.255),(.19,.239),(.205,.231)],DARK)
 cup_profile('Headphone_center_ring',c,n,[(.035,.257),(.047,.257),(.047,.263),(.035,.263)],TEAL)
 disc('Headphone_center_button',c+n*.265,.032,.038,DARK,n,32)
 # Hardware details on the side of each cup.
 right=Vector((0,0,1)).cross(n).normalized()
 for k in [-1,1]:
  p=c+right*(k*.235)+n*.17
  box('Headphone_housing_tab',p,(.035,.04,.16),SILVER,.012)
 curve('Headphone_yoke_connector',[c+Vector((0,.04,.33)),c+Vector((s*.09,.08,.38)),c+Vector((s*.12,.16,.31))],.025,SILVER)

# Raise jacket / headphones to the neck and broaden the reference silhouette.
bpy.context.view_layer.update()
for o in model.objects:
 if o not in before_body and o.type in ['MESH','CURVE']:
  o.location.z*=1.13
  if o.type=='MESH':
   for vtx in o.data.vertices:vtx.co.z*=1.13
  else:
   for spline in o.data.splines:
    for p in spline.bezier_points:
     p.co.z*=1.13;p.handle_left.z*=1.13;p.handle_right.z*=1.13
root.scale=(1.22,1.30,1)
# Flat cropped bust underside; no display pedestal in the reference.
root['reference']='Cyberpunk Hedgehog IT Expert.png';root['version']='2.0';root['rigged']=False
root['units_note']='Relative artistic scale, not measured physical dimensions.'
print('GEOMETRY_COMPLETE',flush=True)
# Normalize, convert curves, UV fallback, and triangulate only for export.
bpy.ops.object.select_all(action='DESELECT')
for o in list(model.objects):
 if o.type=='CURVE':
  o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH');o.select_set(False)
for o in model.objects:
 if o.type=='MESH':
  o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.select_set(False)
  if not o.data.uv_layers:
   uv=o.data.uv_layers.new(name='UVMap')
   for loop in o.data.loops:
    p=o.data.vertices[loop.vertex_index].co;uv.data[loop.index].uv=(p.x,p.z)
  # Remove degenerate faces produced at polar rings before export.
  import bmesh
  bm=bmesh.new();bm.from_mesh(o.data)
  bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000001)
  bmesh.ops.dissolve_degenerate(bm,dist=.0000001,edges=list(bm.edges))
  bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()

def studio_obj(o):
 for c in list(o.users_collection):c.objects.unlink(o)
 studio.objects.link(o)
def aim(o,p):o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(5.8,-9.0,3.65));cam=bpy.context.object;studio_obj(cam);cam.name='Reference_ThreeQuarter';cam.data.type='ORTHO';cam.data.ortho_scale=4.12;aim(cam,(0,-.03,2.02));scene.camera=cam
for name,loc,power,color,size in [('Large_neutral_key',(-3,-5,6),520,(1,.91,.82),4),('Neutral_fill',(4,-3,4),340,(.83,.93,1),3),('Cyan_rim',(2,3,5),650,(.25,.8,1),3)]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;studio_obj(o);o.name=name;o.data.energy=power;o.data.color=color;o.data.shape='DISK';o.data.size=size;aim(o,(0,0,2.2))
world=bpy.data.worlds.new('Neutral_studio_world');scene.world=world;world.use_nodes=True
world.node_tree.nodes.get('Background').inputs['Color'].default_value=(.16,.18,.21,1);world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.3
scene.render.engine='CYCLES';scene.cycles.samples=48;scene.cycles.use_denoising=True
scene.view_settings.view_transform='AgX'
scene.view_settings.look='AgX - Medium High Contrast'
scene.view_settings.exposure=.65
scene.render.resolution_x=1248;scene.render.resolution_y=1262;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=True
scene.render.filepath=os.path.join(OUT,'preview_reference.png')
for area in bpy.context.screen.areas if bpy.context.screen else []:
 if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA'
for o in model.objects:o.select_set(True)
bpy.context.view_layer.objects.active=root
for o in studio.objects:o.select_set(False)
for o in reference.objects:o.select_set(False)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'cyberpunk_hedgehog_v2.blend'))
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'cyberpunk_hedgehog_v2.high.glb'),export_format='GLB',use_selection=True,export_cameras=False,export_lights=False)
print('HIGH_EXPORT_COMPLETE',flush=True)
# Web images: JPEG color, 8-bit PNG normals; preserve full-res maps in source.
webtex=os.path.join(OUT,'textures_web');os.makedirs(webtex,exist_ok=True)
old_view=(scene.view_settings.view_transform,scene.view_settings.look,scene.view_settings.exposure)
scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=0
texture_errors={}
for im in list(bpy.data.images):
 if im.name not in [i.name for i in [face_img,cream_tex,fur_normal,cloth_img,navy_img,cloth_normal,knit_img,knit_normal,quill_img,quill_normal,iris_img]]:continue
 is_normal='normal' in im.name
 copy=im.copy()
 if is_normal:
  limit=512 if any(s in im.name for s in ['woven','quill_fibers']) else 1024
  if copy.size[0]>limit:copy.scale(limit,limit)
 scene.render.image_settings.color_depth='8';scene.render.image_settings.color_mode='RGB'
 scene.render.image_settings.file_format='PNG' if is_normal else 'JPEG';scene.render.image_settings.quality=92;scene.render.image_settings.compression=70
 path=os.path.join(webtex,im.name+('.png' if is_normal else '.jpg'))
 copy.save_render(path,scene=scene)
 loaded=bpy.data.images.load(path,check_existing=False)
 if is_normal:loaded.colorspace_settings.name='Non-Color'
 # Ensure encoding has not applied the studio exposure to texture values.
 if copy.size[:]==loaded.size[:]:
  pa=np.array(copy.pixels[:],dtype=np.float32).reshape(-1,4)[::101,:3]
  pb=np.array(loaded.pixels[:],dtype=np.float32).reshape(-1,4)[::101,:3]
  texture_errors[im.name]=float(np.mean(np.abs(pa-pb)))
 for m in bpy.data.materials:
  if m.use_nodes:
   for node in m.node_tree.nodes:
    if node.type=='TEX_IMAGE' and node.image==im:node.image=loaded
 bpy.data.images.remove(copy)
scene.view_settings.view_transform=old_view[0];scene.view_settings.look=old_view[1];scene.view_settings.exposure=old_view[2]
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.image_settings.color_depth='8'
# Material-grouped runtime variant keeps face, eye and lens geometry unchanged.
web=bpy.data.collections.new('Web_Export_Temporary');scene.collection.children.link(web)
groups={}
for o in list(model.objects):
 if o.type=='MESH':
  c=o.copy();c.data=o.data.copy();web.objects.link(c)
  # Bake world coordinates before dropping parents. Root nonuniform scale plus
  # head rotation would otherwise lose shear during matrix decomposition.
  c.data.transform(o.matrix_world);c.parent=None;c.matrix_parent_inverse=Matrix.Identity(4);c.matrix_world=Matrix.Identity(4)
  key=tuple(m.name for m in c.data.materials);groups.setdefault(key,[]).append(c)
bpy.ops.object.select_all(action='DESELECT')
for key,objects in groups.items():
 for o in objects:o.select_set(True)
 bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();o=bpy.context.object;o.name='Web_'+key[0]
 bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
 # Preserve fine fur and sculpt, simplify manufactured curves and dense band geometry.
 if key[0] in [KNIT.name,DARK.name,SILVER.name,TEAL.name,NAVY.name,CYAN.name]:
  md=o.modifiers.new('Runtime_detail_reduction','DECIMATE');md.ratio=.65;apply(o,md)
 o.select_set(False)
for o in web.objects:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'cyberpunk_hedgehog_v2.web.glb'),export_format='GLB',use_selection=True,export_cameras=False,export_lights=False)
def stats(objects):
 meshes=[o for o in objects if o.type=='MESH']
 return {'meshes':len(meshes),'triangles':sum(len(p.vertices)-2 for o in meshes for p in o.data.polygons),'materials':len(set(m.name for o in meshes for m in o.data.materials))}
report={'source':stats(model.objects),'web':stats(web.objects),'texture_encoding_mean_error':texture_errors}
for typ in ['high','web']:report[typ+'_bytes']=os.path.getsize(os.path.join(OUT,'cyberpunk_hedgehog_v2.'+typ+'.glb'))
with open(os.path.join(OUT,'asset_stats.json'),'w') as f:json.dump(report,f,indent=2)
for o in list(web.objects):bpy.data.objects.remove(o,do_unlink=True)
bpy.data.collections.remove(web)
print('EXPORT_COMPLETE',report,flush=True)
if '--no-render' not in sys.argv:
 bpy.ops.render.render(write_still=True)
 print('RENDER_COMPLETE',flush=True)
