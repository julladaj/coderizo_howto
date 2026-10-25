"""Local glTF binary, accessor, buffer and image audit; no network dependencies."""
import json,struct,sys,os,math

def inspect(path):
 b=open(path,'rb').read();magic,version,total=struct.unpack_from('<III',b)
 assert magic==0x46546c67 and version==2 and total==len(b),'Invalid GLB header'
 chunks=[];pos=12
 while pos<len(b):
  n,t=struct.unpack_from('<II',b,pos);pos+=8
  assert n%4==0 and pos+n<=len(b),'Invalid chunk length'
  chunks.append((t,b[pos:pos+n]));pos+=n
 assert chunks[0][0]==0x4e4f534a
 j=json.loads(chunks[0][1]);binary=next(data for t,data in chunks if t==0x004e4942)
 assert j['asset']['version']=='2.0'
 assert all('uri' not in x for x in j.get('buffers',[]))
 assert j['buffers'][0]['byteLength']<=len(binary)
 for bv in j.get('bufferViews',[]):
  assert bv.get('byteOffset',0)+bv['byteLength']<=len(binary)
 sizes={5120:1,5121:1,5122:2,5123:2,5125:4,5126:4};types={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16,'MAT3':9,'MAT2':4}
 formats={5120:'b',5121:'B',5122:'h',5123:'H',5125:'I',5126:'f'}
 def values(ai):
  a=j['accessors'][ai];bv=j['bufferViews'][a['bufferView']];w=sizes[a['componentType']]*types[a['type']]
  stride=bv.get('byteStride',w);off=bv.get('byteOffset',0)+a.get('byteOffset',0)
  assert a.get('byteOffset',0)+max(0,a['count']-1)*stride+w<=bv['byteLength']
  fmt='<'+formats[a['componentType']]*types[a['type']]
  return [struct.unpack_from(fmt,binary,off+i*stride) for i in range(a['count'])]
 for i,a in enumerate(j.get('accessors',[])):
  if 'bufferView' not in a:continue
  assert all(all(math.isfinite(x) for x in row) for row in values(i)),'Nonfinite accessor'
 tris=0;degenerate=0;max_normal_error=0
 for m in j['meshes']:
  for p in m['primitives']:
   assert p.get('mode',4)==4
   pos=values(p['attributes']['POSITION']);idx=[v[0] for v in values(p['indices'])]
   assert max(idx)<len(pos) and len(idx)%3==0
   accessor=j['accessors'][p['attributes']['POSITION']]
   for axis in range(3):
    assert abs(min(v[axis] for v in pos)-accessor['min'][axis])<.0001
    assert abs(max(v[axis] for v in pos)-accessor['max'][axis])<.0001
   if 'NORMAL' in p['attributes']:
    max_normal_error=max(max_normal_error,max(abs(math.sqrt(sum(x*x for x in n))-1) for n in values(p['attributes']['NORMAL'])))
    assert max_normal_error<.005,'Non-unit normal'
   tris+=len(idx)//3
   degenerate+=sum(len(set(idx[i:i+3]))<3 for i in range(0,len(idx),3))
   if 'material' in p:assert p['material']<len(j['materials'])
 images=[]
 for im in j.get('images',[]):
  assert 'uri' not in im and 'bufferView' in im
  bv=j['bufferViews'][im['bufferView']];data=binary[bv.get('byteOffset',0):bv.get('byteOffset',0)+bv['byteLength']]
  if im['mimeType']=='image/png':
   assert data.startswith(b'\x89PNG\r\n\x1a\n');dim=struct.unpack_from('>II',data,16);depth=data[24]
  elif im['mimeType']=='image/jpeg':
   assert data[:2]==b'\xff\xd8';dim=None;depth=8;k=2
   while k<len(data):
    if data[k]!=255:k+=1;continue
    marker=data[k+1];k+=2
    if marker in [0xd8,0xd9] or 0xd0<=marker<=0xd7:continue
    seglen=struct.unpack_from('>H',data,k)[0]
    if marker in [0xc0,0xc1,0xc2]:
     depth=data[k+2];height,width=struct.unpack_from('>HH',data,k+3);dim=[width,height];break
    k+=seglen
  else:raise AssertionError('Unexpected image format')
  images.append({'name':im.get('name'),'bytes':len(data),'mime':im['mimeType'],'dimensions':dim,'bit_depth':depth})
 return {'file':os.path.basename(path),'bytes':len(b),'meshes':len(j['meshes']),'materials':len(j['materials']),'triangles':tris,'degenerate_index_triangles':degenerate,'max_normal_length_error':max_normal_error,'images':images,'extensions':j.get('extensionsUsed',[]),'audit_passed':True,'audit_note':'Local structural audit, not Khronos conformance validation.'}

if __name__=='__main__':
 result=inspect(sys.argv[1]);print(json.dumps(result,indent=2))
 if len(sys.argv)>2:open(sys.argv[2],'w').write(json.dumps(result,indent=2))
