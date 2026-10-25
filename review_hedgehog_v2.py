import bpy, os, json, math, sys
import numpy as np
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
ROOT=os.path.dirname(os.path.abspath(__file__));OUT=os.path.join(ROOT,'hedgehog_model_v2')
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,'cyberpunk_hedgehog_v2.blend'))
scene=bpy.context.scene;cam=scene.camera
ref_loc=cam.location.copy();ref_rot=cam.rotation_euler.copy();ref_scale=cam.data.ortho_scale
scene.cycles.samples=32;scene.cycles.use_denoising=True
source=bpy.data.collections['Hedgehog_V2_Editable']
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.image_settings.color_depth='8'
def render(name):
 scene.render.filepath=os.path.join(OUT,name);bpy.ops.render.render(write_still=True)
 im=bpy.data.images.load(scene.render.filepath,check_existing=False)
 p=np.array(im.pixels[:],np.float32).reshape(im.size[1],im.size[0],4);bpy.data.images.remove(im);return p
def bounds(objects):
 p=np.array([tuple(o.matrix_world@v.co) for o in objects if o.type=='MESH' for v in o.data.vertices]);return p.min(axis=0),p.max(axis=0)
srcbounds=bounds(source.objects)
# Hand-annotated reference anchors. Report error honestly rather than asserting likeness.
ref={'nose':(.280,.283),'near_iris':(.494,.278),'far_iris':(.308,.258),'near_ear':(.698,.287),'near_headphone':(.610,.621),'far_headphone':(.276,.638)}
objects={
 'nose':bpy.data.objects['Rounded_triangular_nose'],
 'near_iris':bpy.data.objects['Iris_radial.001'],
 'far_iris':bpy.data.objects['Iris_radial'],
 'near_ear':bpy.data.objects['Recessed_ear_interior.001'],
}
points={key:o.matrix_world.translation for key,o in objects.items()}
for key in ['near_iris','far_iris']:
 o=objects[key];points[key]=o.matrix_world@o.data.vertices[0].co
headphone_scale=1.13
for key,s in [('near_headphone',1),('far_headphone',-1)]:
 p=Vector((.65,-.37,1.48) if s>0 else (-.38,-.30,1.30))+Vector((s*.56,-.82,.08)).normalized()*.255
 points[key]=Vector((p.x*1.22,p.y*1.30,p.z*headphone_scale))
# Ear mesh coordinates are authored in world coordinates before parenting.
ear=objects['near_ear'];points['near_ear']=ear.matrix_world@Vector((.73,-.12,3.0))
anchors={}
for key,p in points.items():
 co=world_to_camera_view(scene,cam,p);xy=(co.x,1-co.y);target=ref[key]
 anchors[key]={'reference_normalized_xy':target,'model_normalized_xy':xy,'error_percent_image_width':100*math.sqrt((xy[0]-target[0])**2+((xy[1]-target[1])*1262/1248)**2)}
report={'reference_anchor_note':'Manual approximate annotations; comparison is image-space, not measured anatomy.','anchors':anchors,'target_3_percent_all_anchors_met':all(x['error_percent_image_width']<=3 for x in anchors.values())}
print('ANCHOR_REVIEW',report,flush=True)
with open(os.path.join(OUT,'visual_review.json'),'w') as f:json.dump(report,f,indent=2)
if '--anchors-only' in sys.argv:sys.exit(0)
srcpixels=render('preview_source.png')
scene.render.resolution_x=800;scene.render.resolution_y=800
for name,loc in [('front',(0,-10,2.3)),('right',(10,0,2.3)),('back',(0,10,2.3))]:
 cam.location=loc;cam.rotation_euler=(Vector((0,0,2))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=4.5
 render('view_'+name+'.png')
cam.location=ref_loc;cam.rotation_euler=ref_rot;cam.data.ortho_scale=ref_scale
scene.render.resolution_x=1248;scene.render.resolution_y=1262
before=set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=os.path.join(OUT,'cyberpunk_hedgehog_v2.web.glb'))
imported=set(bpy.data.objects)-before
source.hide_render=True
webbounds=bounds(imported)
report['roundtrip']={'import_succeeded':True,'imported_meshes':sum(o.type=='MESH' for o in imported),'source_bounds':[a.tolist() for a in srcbounds],'web_bounds':[a.tolist() for a in webbounds],'max_bounds_error_units':float(max(np.max(np.abs(a-b)) for a,b in zip(srcbounds,webbounds)))}
webpixels=render('preview_reference.png')
mask=(srcpixels[:,:,3]>.5)&(webpixels[:,:,3]>.5)
report['roundtrip']['mean_absolute_rgb_difference']=float(np.abs(srcpixels[:,:,:3]-webpixels[:,:,:3])[mask].mean())
report['roundtrip']['alpha_difference_mean']=float(np.abs(srcpixels[:,:,3]-webpixels[:,:,3]).mean())
report['roundtrip']['note']='Blender glTF importer and Cycles; this does not replace a browser/WebGL test.'
with open(os.path.join(OUT,'visual_review.json'),'w') as f:json.dump(report,f,indent=2)
print('REVIEW_COMPLETE',report,flush=True)
