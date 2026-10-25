import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

/**
 * The GLB is a single static scan-style mesh (no skeleton, no morph targets),
 * so the "rig" is procedural: the vertex shader bends everything above the neck
 * around a pivot, and the fragment shader warps the iris texture and paints an
 * eyelid inside two elliptical eye regions measured in rest-pose model space.
 */
export const RIG = {
  pivot: new THREE.Vector3(0, 0.5, 0.1),
  neck: new THREE.Vector2(0.47, 0.63),
  eyeL: new THREE.Vector4(-0.093, 0.702, 0.047, 0.022),
  eyeR: new THREE.Vector4(0.092, 0.689, 0.048, 0.023),
  eyeFrontZ: 0.17,
  headCenter: new THREE.Vector3(0, 0.7, 0.2),
};

const VERT_HEAD = /* glsl */ `
uniform vec3 uHead;
uniform vec3 uPivot;
uniform vec2 uNeck;
varying vec3 vRest;
mat3 czRot(vec3 a) {
  float cx = cos(a.x), sx = sin(a.x), cy = cos(a.y), sy = sin(a.y), cz = cos(a.z), sz = sin(a.z);
  mat3 rx = mat3(1., 0., 0., 0., cx, sx, 0., -sx, cx);
  mat3 ry = mat3(cy, 0., -sy, 0., 1., 0., sy, 0., cy);
  mat3 rz = mat3(cz, sz, 0., -sz, cz, 0., 0., 0., 1.);
  return ry * rx * rz;
}
`;

const FRAG_HEAD = /* glsl */ `
uniform vec4 uEyeL;
uniform vec4 uEyeR;
uniform vec2 uLook;
uniform float uBlink;
uniform float uEyeFrontZ;
uniform vec3 uLidColor;
varying vec3 vRest;
`;

const FRAG_MAP = /* glsl */ `
#ifdef USE_MAP
  vec2 czUv = vMapUv;
  vec2 czEL = (vRest.xy - uEyeL.xy) / uEyeL.zw;
  vec2 czER = (vRest.xy - uEyeR.xy) / uEyeR.zw;
  float czFront = smoothstep(uEyeFrontZ, uEyeFrontZ + 0.03, vRest.z);
  bool czLeft = length(czEL) < length(czER);
  vec2 czE = czLeft ? czEL : czER;
  vec4 czEye = czLeft ? uEyeL : uEyeR;
  float czD = length(czE);
  // Per-triangle Jacobian (uv w.r.t. rest-pose xy) from screen-space derivatives.
  vec2 czDpx = dFdx(vRest.xy), czDpy = dFdy(vRest.xy);
  vec2 czDux = dFdx(vMapUv), czDuy = dFdy(vMapUv);
  float czDet = czDpx.x * czDpy.y - czDpy.x * czDpx.y;
  float czInner = (1.0 - smoothstep(0.25, 0.92, czD)) * czFront;
  if (czInner > 0.0 && abs(czDet) > 1e-16) {
    mat2 czPinv = mat2(czDpy.y, -czDpx.y, -czDpy.x, czDpx.x) / czDet;
    vec2 czShift = uLook * czEye.zw * vec2(0.36, 0.30) * czInner;
    vec2 czDelta = mat2(czDux, czDuy) * (czPinv * czShift);
    if (dot(czDelta, czDelta) < 0.0004) czUv -= czDelta;
  }
  vec4 sampledDiffuseColor = texture2D( map, czUv );
  #ifdef DECODE_VIDEO_TEXTURE
    sampledDiffuseColor = sRGBTransferEOTF( sampledDiffuseColor );
  #endif
  diffuseColor *= sampledDiffuseColor;
  if (uBlink > 0.001) {
    float czLidY = mix(1.25, -0.95, uBlink) - 0.38 * (1.0 - czE.x * czE.x) * (1.0 - 0.35 * uBlink);
    float czCover = smoothstep(-0.06, 0.06, czE.y - czLidY);
    float czMask = (1.0 - smoothstep(0.92, 1.08, czD)) * czFront;
    float czLash = 1.0 - smoothstep(0.0, 0.22, czE.y - czLidY);
    vec3 czLid = uLidColor * (0.78 + 0.32 * clamp(czE.y * 0.5 + 0.5, 0.0, 1.0));
    czLid = mix(czLid, vec3(0.012, 0.016, 0.02), czLash * 0.85);
    diffuseColor.rgb = mix(diffuseColor.rgb, czLid, czCover * czMask);
  }
#endif
`;

function patchMaterial(material, uniforms) {
  material.onBeforeCompile = (shader) => {
    Object.assign(shader.uniforms, uniforms);
    shader.vertexShader = VERT_HEAD + shader.vertexShader
      .replace('#include <beginnormal_vertex>', `#include <beginnormal_vertex>
        float czW = smoothstep(uNeck.x, uNeck.y, position.y);
        czW = czW * czW * (3.0 - 2.0 * czW);
        mat3 czR = czRot(uHead * czW);
        objectNormal = czR * objectNormal;`)
      .replace('#include <begin_vertex>', `vec3 transformed = uPivot + czR * (position - uPivot);
        vRest = position;`);
    shader.fragmentShader = FRAG_HEAD + shader.fragmentShader.replace('#include <map_fragment>', FRAG_MAP);
  };
  material.customProgramCacheKey = () => 'coderizo-hedgehog-rig';
}

/** Dequantize meshopt/KHR_mesh_quantization attributes and bake the node transform. */
function bakeGeometry(mesh) {
  const geo = mesh.geometry;
  for (const name of Object.keys(geo.attributes)) {
    const a = geo.getAttribute(name);
    if (a.array instanceof Float32Array && !a.isInterleavedBufferAttribute) continue;
    const out = new Float32Array(a.count * a.itemSize);
    const get = [a.getX, a.getY, a.getZ, a.getW];
    for (let i = 0; i < a.count; i++) for (let k = 0; k < a.itemSize; k++) out[i * a.itemSize + k] = get[k].call(a, i);
    geo.setAttribute(name, new THREE.BufferAttribute(out, a.itemSize));
  }
  mesh.updateWorldMatrix(true, false);
  geo.applyMatrix4(mesh.matrixWorld);
  mesh.position.set(0, 0, 0);
  mesh.quaternion.identity();
  mesh.scale.set(1, 1, 1);
  mesh.removeFromParent();
  return mesh;
}

/* ---------------- motion helpers ---------------- */
class Spring {
  constructor(value = 0, stiffness = 60, damping = 14) {
    this.x = value; this.v = 0; this.k = stiffness; this.c = damping; this.target = value;
  }
  step(dt) {
    const a = this.k * (this.target - this.x) - this.c * this.v;
    this.v += a * dt; this.x += this.v * dt;
    return this.x;
  }
}
const rand = (a, b) => a + Math.random() * (b - a);
const clamp = (v, a, b) => Math.min(b, Math.max(a, v));

export class HedgehogStage {
  constructor({ canvas, container, onProgress, onState }) {
    this.canvas = canvas;
    this.container = container;
    this.onProgress = onProgress;
    this.onState = onState;
    this.reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
    this.debug = new URLSearchParams(location.search);

    this.renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true, powerPreference: 'high-performance' });
    this.renderer.setClearColor(0x000000, 0);
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.05;

    this.scene = new THREE.Scene();
    const pmrem = new THREE.PMREMGenerator(this.renderer);
    this.scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
    this.scene.environmentIntensity = 0.55;

    this.camera = new THREE.PerspectiveCamera(28, 1, 0.05, 20);
    this.root = new THREE.Group();
    this.scene.add(this.root);
    this.addLights();

    this.uniforms = {
      uHead: { value: new THREE.Vector3() },
      uPivot: { value: RIG.pivot },
      uNeck: { value: RIG.neck },
      uEyeL: { value: RIG.eyeL },
      uEyeR: { value: RIG.eyeR },
      uEyeFrontZ: { value: RIG.eyeFrontZ },
      uLook: { value: new THREE.Vector2() },
      uBlink: { value: 0 },
      uLidColor: { value: new THREE.Color('#a88a72').convertSRGBToLinear().multiplyScalar(0.62) },
    };

    // motion state
    this.yaw = new Spring(0, 34, 11);
    this.pitch = new Spring(0, 34, 11);
    this.roll = new Spring(0, 20, 9);
    this.eyeX = new Spring(0, 520, 46);
    this.eyeY = new Spring(0, 520, 46);
    this.pointer = new THREE.Vector2();
    this.lastPointer = -1e9;
    this.mode = 'idle';
    this.nextGlance = 0;
    this.glance = { yaw: 0, pitch: 0, ex: 0, ey: 0 };
    this.blink = { t: -1, next: 1.6, double: false };
    this.clock = new THREE.Clock();
    this.time = 0;
    this.visible = true;
    this.intro = 0;
    this.headScreen = new THREE.Vector2(0.5, 0.4);

    this.resize = this.resize.bind(this);
    this.tick = this.tick.bind(this);
    new ResizeObserver(this.resize).observe(container);
    this.resize();
    window.addEventListener('pointermove', (e) => this.onPointer(e), { passive: true });
    document.documentElement.addEventListener('pointerleave', () => { this.lastPointer = -1e9; });
    new IntersectionObserver(([en]) => { this.visible = en.isIntersecting; }, { threshold: 0 }).observe(container);
  }

  addLights() {
    const hemi = new THREE.HemisphereLight(0xcfe9ff, 0x0b1320, 0.9);
    const key = new THREE.DirectionalLight(0xfff4e8, 2.1);
    key.position.set(-1.2, 2.0, 2.4);
    const fill = new THREE.DirectionalLight(0x9fd6ff, 0.55);
    fill.position.set(1.6, 0.6, 1.8);
    const rimG = new THREE.DirectionalLight(0x1aab73, 5.5);
    rimG.position.set(-2.2, 1.2, -1.6);
    const rimB = new THREE.DirectionalLight(0x3b7bff, 5.0);
    rimB.position.set(2.2, 1.4, -1.4);
    this.cursorLight = new THREE.PointLight(0x5cf0b4, 0.0, 3.0, 1.6);
    this.cursorLight.position.set(0, 0.8, 1.2);
    this.scene.add(hemi, key, fill, rimG, rimB, this.cursorLight);
  }

  async load(url) {
    const loader = new GLTFLoader();
    loader.setMeshoptDecoder(MeshoptDecoder);
    const gltf = await loader.loadAsync(url, (e) => {
      if (e.lengthComputable && this.onProgress) this.onProgress(e.loaded / e.total);
    });
    const meshes = [];
    gltf.scene.traverse((o) => o.isMesh && meshes.push(o));
    for (const mesh of meshes) {
      bakeGeometry(mesh);
      const m = mesh.material;
      m.side = THREE.FrontSide;
      if (m.map) m.map.anisotropy = Math.min(8, this.renderer.capabilities.getMaxAnisotropy());
      patchMaterial(m, this.uniforms);
      mesh.frustumCulled = false;
      this.root.add(mesh);
    }
    this.onProgress?.(1);
    await this.renderer.compileAsync?.(this.scene, this.camera);
    this.loaded = true;
    this.clock.start();
    this.renderer.setAnimationLoop(this.tick);
    return this;
  }

  resize() {
    const w = this.container.clientWidth, h = this.container.clientHeight;
    if (!w || !h) return;
    const dpr = Math.min(window.devicePixelRatio || 1, w < 768 ? 1.6 : 2);
    this.renderer.setPixelRatio(dpr);
    this.renderer.setSize(w, h, false);
    const aspect = w / h;
    this.camera.aspect = aspect;
    const mobile = w < 900;
    // fit the bust: height-limited on wide screens, width-limited on narrow screens
    let viewH = mobile ? 1.06 / Math.min(aspect, 1.15) * 0.92 : 1.24;
    viewH = Math.max(viewH, 1.06);
    const fov = THREE.MathUtils.degToRad(this.camera.fov);
    const dist = viewH / (2 * Math.tan(fov / 2));
    const lookY = viewH / 2 - (mobile ? 0.0 : 0.03);
    this.baseCam = { y: lookY + 0.04, dist, lookY };
    this.camera.position.set(0, lookY + 0.04, dist);
    this.camera.lookAt(0, lookY, 0);
    this.camera.updateProjectionMatrix();
  }

  onPointer(e) {
    const r = this.container.getBoundingClientRect();
    if (e.clientY > r.bottom + 200) return;
    this.pointer.set(e.clientX, e.clientY);
    this.lastPointer = this.time;
  }

  updateTargets(dt) {
    const t = this.time;
    const tracking = t - this.lastPointer < 2.6;
    if (tracking !== (this.mode === 'tracking')) {
      this.mode = tracking ? 'tracking' : 'idle';
      this.nextGlance = t + 0.4;
    }
    let yawT, pitchT, ex, ey;
    if (tracking) {
      const r = this.container.getBoundingClientRect();
      const hx = r.left + this.headScreen.x * r.width;
      const hy = r.top + this.headScreen.y * r.height;
      const nx = clamp((this.pointer.x - hx) / (r.width * 0.5), -1.2, 1.2);
      const ny = clamp((hy - this.pointer.y) / (r.height * 0.5), -1.2, 1.2);
      yawT = nx * 0.5;
      pitchT = -ny * 0.3;
      ex = clamp(nx * 1.4, -1, 1);
      ey = clamp(ny * 1.3, -1, 1);
    } else {
      if (t > this.nextGlance) {
        // natural "looking around": pick a new point of interest; eyes jump first, head follows
        const big = Math.random() < 0.35;
        this.glance.yaw = rand(-1, 1) * (big ? 0.42 : 0.2);
        this.glance.pitch = rand(-0.12, 0.1) + (Math.random() < 0.2 ? -0.12 : 0);
        this.glance.ex = clamp(this.glance.yaw * 2.2 + rand(-0.15, 0.15), -0.9, 0.9);
        this.glance.ey = clamp(-this.glance.pitch * 2.6 + rand(-0.15, 0.15), -0.8, 0.8);
        this.nextGlance = t + rand(1.4, 3.8);
        if (big && Math.random() < 0.6) this.triggerBlink(0.05);
      }
      const n = Math.sin(t * 0.7) * 0.025 + Math.sin(t * 1.9 + 1.1) * 0.012;
      yawT = this.glance.yaw + n;
      pitchT = this.glance.pitch + Math.sin(t * 0.55 + 0.4) * 0.02;
      ex = this.glance.ex + Math.sin(t * 2.7) * 0.04;
      ey = this.glance.ey + Math.cos(t * 2.3) * 0.03;
    }
    // eye micro-saccades
    if (Math.random() < dt * 1.6) { this.eyeX.x += rand(-0.06, 0.06); this.eyeY.x += rand(-0.04, 0.04); }

    if (this.debug.has('lookx')) { ex = +this.debug.get('lookx'); ey = +(this.debug.get('looky') || 0); yawT = pitchT = 0; }
    this.yaw.target = yawT;
    this.pitch.target = pitchT;
    this.roll.target = -yawT * 0.18 + Math.sin(t * 0.4) * 0.015;
    this.eyeX.target = ex;
    this.eyeY.target = ey;
  }

  triggerBlink(delay = 0) {
    if (this.blink.t >= 0) return;
    this.blink.t = -delay - 1e-4;
    this.blink.pending = true;
  }

  updateBlink(dt) {
    const b = this.blink;
    if (this.debug.has('blink')) return +this.debug.get('blink');
    if (b.pending) {
      b.t += dt;
      if (b.t < 0) return 0;
      b.pending = false; b.t = 0;
    }
    if (b.t < 0) {
      b.next -= dt;
      if (b.next <= 0) { b.t = 0; b.double = Math.random() < 0.18; b.next = rand(2.2, 5.6); }
      return 0;
    }
    b.t += dt;
    const close = 0.075, hold = 0.035, open = 0.14, total = close + hold + open;
    let v;
    if (b.t < close) v = b.t / close;
    else if (b.t < close + hold) v = 1;
    else if (b.t < total) v = 1 - (b.t - close - hold) / open;
    else {
      v = 0;
      if (b.double) { b.double = false; b.t = -0.09; b.pending = true; }
      else b.t = -1;
    }
    v = clamp(v, 0, 1);
    return v * v * (3 - 2 * v);
  }

  tick() {
    const dt = Math.min(this.clock.getDelta(), 1 / 20);
    this.time += dt;
    if (!this.visible) return;
    this.updateTargets(dt);
    const k = this.reduced ? 0.25 : 1;
    const yaw = this.yaw.step(dt) * k, pitch = this.pitch.step(dt) * k, roll = this.roll.step(dt) * k;
    const ex = this.eyeX.step(dt), ey = this.eyeY.step(dt);
    const blink = this.reduced ? 0 : this.updateBlink(dt);
    // eyes rotate with the head, so the texture warp only carries the residual gaze
    this.uniforms.uHead.value.set(pitch, yaw, roll);
    this.uniforms.uLook.value.set(clamp(ex - yaw * 0.9, -1, 1), clamp(ey + pitch * 0.9, -1, 1));
    this.uniforms.uBlink.value = blink;

    // body follows slightly + breathing + intro rise
    this.intro = Math.min(1, this.intro + dt / 1.6);
    const ease = 1 - Math.pow(1 - this.intro, 3);
    const breathe = Math.sin(this.time * 1.4) * 0.5 + 0.5;
    this.root.rotation.y = yaw * 0.16;
    this.root.position.y = (1 - ease) * -0.08 + breathe * 0.004;
    this.root.scale.setScalar(0.96 + ease * 0.04 + breathe * 0.002);

    const tracking = this.mode === 'tracking';
    this.cursorLight.intensity += ((tracking ? 1.2 : 0) - this.cursorLight.intensity) * Math.min(1, dt * 3);
    if (tracking) {
      const r = this.container.getBoundingClientRect();
      const nx = (this.pointer.x - r.left) / r.width * 2 - 1, ny = -((this.pointer.y - r.top) / r.height * 2 - 1);
      this.cursorLight.position.x += (nx * 0.9 - this.cursorLight.position.x) * Math.min(1, dt * 4);
      this.cursorLight.position.y += (this.baseCam.lookY + ny * 0.5 - this.cursorLight.position.y) * Math.min(1, dt * 4);
    }

    this.renderer.render(this.scene, this.camera);

    // expose head screen position for UI rings
    const p = RIG.headCenter.clone().applyMatrix4(this.root.matrixWorld).project(this.camera);
    this.headScreen.set(p.x * 0.5 + 0.5, -p.y * 0.5 + 0.5);
    this.onState?.({
      mode: this.mode, yaw, pitch, blink, eyeX: ex, eyeY: ey, head: this.headScreen, intro: ease,
    });
  }
}
