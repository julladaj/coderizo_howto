import './style.css';
import { initSteps } from './steps.js';
import { initMarquees } from './marquee.js';

const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
const $ = (s, r = document) => r.querySelector(s);

/* ---------------- hero ---------------- */
async function initHero() {
  const stage = $('#stage');
  const hero = $('#hero');
  const loader = $('#loader');
  const pct = $('#loaderPct');
  const ring = loader.querySelector('.p');
  const hud = { mode: $('#hudMode'), yaw: $('#hudYaw'), pitch: $('#hudPitch'), optic: $('#hudOptic') };
  const fmt = (r) => { const d = (r * 180) / Math.PI; return `${d >= 0 ? '+' : '-'}${Math.abs(d).toFixed(1).padStart(4, '0')}°`; };

  let lastMode = '';
  let frame = 0;
  const { HedgehogStage } = await import('./hero/hedgehog.js');
  const app = new HedgehogStage({
    canvas: $('#hedgehog'),
    container: stage,
    onProgress: (p) => {
      pct.textContent = `${Math.round(p * 100)}%`;
      ring.style.strokeDashoffset = `${276.5 * (1 - p)}`;
    },
    onState: (s) => {
      hero.style.setProperty('--hx', `${(s.head.x * 100).toFixed(2)}%`);
      hero.style.setProperty('--hy', `${(s.head.y * 100).toFixed(2)}%`);
      hero.style.setProperty('--ex', s.eyeX.toFixed(3));
      hero.style.setProperty('--ey', s.eyeY.toFixed(3));
      if (s.mode !== lastMode) {
        lastMode = s.mode;
        hero.dataset.mode = s.mode;
        hud.mode.textContent = s.mode === 'tracking' ? 'LOCKED / TRACKING' : 'IDLE / SCANNING';
      }
      if (++frame % 4 === 0) {
        hud.yaw.textContent = fmt(s.yaw);
        hud.pitch.textContent = fmt(-s.pitch);
        hud.optic.textContent = `${Math.round((1 - s.blink) * 100)}%`;
      }
    },
  });
  try {
    await app.load('/models/hedgehog.glb');
    hero.classList.add('is-ready');
    window.__ready = true;
  } catch (err) {
    console.error(err);
    loader.querySelector('em').textContent = 'Model unavailable';
    hero.classList.add('is-ready', 'no-model');
  }
}

/* ---------------- hero parallax on scroll ---------------- */
function initScrollFx() {
  const hero = $('#hero');
  const fill = $('#railFill');
  const list = $('.steps-list');
  let ticking = false;
  const update = () => {
    ticking = false;
    const h = hero.offsetHeight;
    const p = Math.min(1, Math.max(0, window.scrollY / h));
    hero.style.setProperty('--sp', p.toFixed(3));
    const r = list.getBoundingClientRect();
    const prog = Math.min(1, Math.max(0, (innerHeight * 0.55 - r.top) / r.height));
    fill.style.transform = `scaleY(${prog})`;
    document.querySelector('.nav').classList.toggle('scrolled', window.scrollY > 24);
  };
  addEventListener('scroll', () => { if (!ticking) { ticking = true; requestAnimationFrame(update); } }, { passive: true });
  update();
}

/* ---------------- reveal + tilt ---------------- */
function initReveal() {
  const io = new IntersectionObserver((entries) => {
    for (const e of entries) if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
  }, { threshold: 0.18, rootMargin: '0px 0px -6% 0px' });
  document.querySelectorAll('.reveal').forEach((el) => io.observe(el));

  if (reduced || matchMedia('(hover: none)').matches) return;
  document.querySelectorAll('[data-tilt]').forEach((el) => {
    const win = el.firstElementChild;
    el.addEventListener('pointermove', (e) => {
      const r = el.getBoundingClientRect();
      const x = (e.clientX - r.left) / r.width - 0.5, y = (e.clientY - r.top) / r.height - 0.5;
      win.style.transform = `perspective(1200px) rotateY(${x * 6}deg) rotateX(${-y * 6}deg)`;
      el.style.setProperty('--gx', `${(x + 0.5) * 100}%`);
      el.style.setProperty('--gy', `${(y + 0.5) * 100}%`);
    });
    el.addEventListener('pointerleave', () => { win.style.transform = ''; });
  });
}

/* ---------------- bento ---------------- */
function initBento() {
  const featured = [
    { name: 'Extensions Manager', price: '€0.00', tag: 'Free' },
    { name: 'Advanced Live Search', price: '€0.00', tag: 'Free' },
    { name: 'Smart One Page Checkout', price: '€0.99', tag: '/ month' },
    { name: 'SEO Redirect Manager Pro', price: '€0.99', tag: '/ month' },
  ];
  let i = 0;
  const card = $('.b-feature-card');
  const set = (d) => {
    i = (i + d + featured.length) % featured.length;
    card.classList.remove('swap-l', 'swap-r');
    void card.offsetWidth;
    card.classList.add(d > 0 ? 'swap-l' : 'swap-r');
    setTimeout(() => {
      $('#ftName').textContent = featured[i].name;
      $('#ftPrice').textContent = featured[i].price;
      $('#ftTag').textContent = featured[i].tag;
    }, 180);
  };
  $('.b-slider .prev').addEventListener('click', () => set(-1));
  $('.b-slider .next').addEventListener('click', () => set(1));
  let sx = null;
  card.addEventListener('pointerdown', (e) => { sx = e.clientX; });
  card.addEventListener('pointerup', (e) => { if (sx !== null && Math.abs(e.clientX - sx) > 30) set(e.clientX < sx ? 1 : -1); sx = null; });

  document.querySelectorAll('.cats button').forEach((b, _, all) => b.addEventListener('click', () => {
    all.forEach((x) => { x.classList.toggle('on', x === b); x.setAttribute('aria-selected', x === b); });
  }));

  document.querySelectorAll('.b-card').forEach((c) => c.addEventListener('pointermove', (e) => {
    const r = c.getBoundingClientRect();
    c.style.setProperty('--mx', `${e.clientX - r.left}px`);
    c.style.setProperty('--my', `${e.clientY - r.top}px`);
  }));
}

/* ---------------- mobile nav ---------------- */
function initNav() {
  const btn = $('.burger');
  btn.addEventListener('click', () => {
    const open = document.body.classList.toggle('nav-open');
    btn.setAttribute('aria-expanded', open);
  });
  document.querySelectorAll('.nav-pills a').forEach((a) => a.addEventListener('click', () => document.body.classList.remove('nav-open')));
}

(document.fonts?.ready ?? Promise.resolve()).then(() => requestAnimationFrame(() => $('#hero').classList.add('booted')));
setTimeout(() => $('#hero').classList.add('booted'), 1500);

initNav();
initScrollFx();
initReveal();
initMarquees();
initSteps(reduced);
initBento();
initHero();
