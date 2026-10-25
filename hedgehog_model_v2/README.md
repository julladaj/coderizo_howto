# Cyberpunk Hedgehog — version 2

Reference-driven static 3D bust, authored in Blender 5.2. Original version 1 files remain in `../hedgehog_model/`.

## Files

- `cyberpunk_hedgehog_v2.blend`: editable parts, UVs, packed full-resolution image textures, posed head, and a studio camera/light collection.
- `cyberpunk_hedgehog_v2.high.glb`: full-detail export with embedded textures.
- `cyberpunk_hedgehog_v2.web.glb`: grouped, reduced web asset with embedded JPEG color maps and PNG normal maps. No compression decoder or external texture download is needed.
- `compare.html`: local reference / version 1 / version 2 comparison, with adjustable reference overlay and alternate backgrounds.
- `preview_source.png`: editable-source render.
- `preview_reference.png`: **actual exported web GLB**, reimported and rendered with the same studio camera.
- `view_front.png`, `view_right.png`, `view_back.png`: source geometry inspection views.
- `asset_stats.json`, `structural_audit.json`, `visual_review.json`: export, structural, and visual/roundtrip checks.

## Changes from version 1

Continuous sculpted face and muzzle; raised head pose; tapered fur neck; fine geometry fibers; layered curved blue-to-ivory quills; angular full glasses frames and tinted lenses; denser knitted cap; layered outward-facing headphones; wider tailored jacket with shoulder panels, individual zipper teeth, stitched hood and metal details. Face, iris, fabric, knit, and quill textures are UV mapped, with normal maps for microdetail.

The reference is one image, so rear geometry is an inferred design. The model remains an artistic interpretation: facial anatomy, hair/fur density, garment construction, and cap shape are visibly different from the reference. Manual image-space anchor errors are recorded in `visual_review.json`; do not interpret the model as a certified 1:1 reconstruction. There is no rig or animation.

## Web use

Copy the `.web.glb` file into your website's public asset directory and load it with the runtime's standard glTF loader. Example inside an existing Three.js app:

```js
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

const { scene: hedgehog } = await new GLTFLoader()
  .loadAsync('/models/cyberpunk_hedgehog_v2.web.glb');
scene.add(hedgehog);
```

Use neutral key/fill lighting and tone mapping. Cyan material emission does not automatically add bloom. Glass lenses use standard alpha blending, not transmission. Hair uses actual narrow geometry and does not depend on Blender hair systems.

Source coordinates: front -Y, up +Z; glTF export converts to Y-up. Dimensions are artistic relative units, not measured human-scale dimensions. The bust is cropped at the torso. Scale and position the imported root uniformly to fit your page. Web mesh transforms are baked to avoid distortion from the posed source hierarchy.

The web asset targets a single hero character. Benchmark it on your actual mobile / desktop targets before using many instances.

## Validation and reproduction

`inspect_glb.py` checks the GLB header/chunks, embedded buffers/images, accessor bounds, finite values, index ranges, material references, and degenerate index triangles. This is a local structural audit, **not** the Khronos validator. Installing Khronos validation / glTF Transform dependencies was unavailable due to network restrictions; native Blender cleanup, grouping, texture encoding and decimation were used instead.

`review_hedgehog_v2.py` reimports the web GLB in Blender, compares actual world-space vertex bounds, and records rendered RGB/alpha differences. Browser automation was rejected by environment approval policy, so WebGL rendering and browser performance have not been tested.

To rebuild in a separate background Blender:

```powershell
& 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe' -b -t 8 --python .\build_hedgehog_v2.py -- --no-render
& 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe' -b -t 8 --python .\review_hedgehog_v2.py
```

Generated source textures are packed into `.blend`; web textures are embedded into GLB. Texture folders are supplied for editing and are not additional runtime dependencies.
