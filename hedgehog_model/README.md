# Cyberpunk Hedgehog

Reference-inspired stylized static bust, authored in Blender 5.2. This is an interpretation of the supplied image, with simplified fur and clothing; no rig or animation is included.

- `cyberpunk_hedgehog.blend`: editable source with separate parts and studio camera/lights.
- `cyberpunk_hedgehog.glb`: full-detail export.
- `cyberpunk_hedgehog.web.glb`: web variant, 14 meshes/material groups and 53,194 triangles. Materials are embedded, with no external texture files or compression decoder requirements.
- `preview0001.png`: transparent studio render of the source model.

The web variant uses Blender material grouping and mesh decimation. glTF Transform was unavailable during preparation. Validate visual quality and performance in the target website before production use.

Blender coordinates: front -Y, up +Z, base Z=0. GLB export converts to glTF Y-up. The asset is approximately 3.2 units tall; scale uniformly to fit your scene. Studio lights and cameras are excluded from GLB.

Example with Three.js in an existing project:

```js
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
const loader = new GLTFLoader();
const { scene: mascot } = await loader.loadAsync('/models/cyberpunk_hedgehog.web.glb');
scene.add(mascot);
```

Provide scene lighting and tone mapping. Cyan materials use emission, but bloom requires a postprocessing effect in your renderer.
