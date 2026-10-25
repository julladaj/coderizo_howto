const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

/** Small scripted "demo" runner: a fake cursor that moves, clicks and types inside an illustration window. */
class Demo {
  constructor(win) {
    this.win = win;
    this.cursor = win.querySelector('.cursor');
    this.visible = false;
    this.waiters = [];
    new IntersectionObserver(([e]) => {
      this.visible = e.isIntersecting;
      if (this.visible) { this.waiters.forEach((r) => r()); this.waiters = []; }
    }, { threshold: 0.35 }).observe(win);
  }
  el(name) { return this.win.querySelector(`[data-el="${name}"]`); }
  untilVisible() { return this.visible ? Promise.resolve() : new Promise((r) => this.waiters.push(r)); }
  async wait(ms) { await sleep(ms); await this.untilVisible(); }
  point(target, ox = 0.5, oy = 0.55) {
    const w = this.win.getBoundingClientRect(), t = target.getBoundingClientRect();
    const sx = this.win.offsetWidth / w.width || 1;
    return { x: (t.left - w.left + t.width * ox) * sx, y: (t.top - w.top + t.height * oy) * sx };
  }
  show(x, y) {
    this.cursor.style.transition = 'none';
    this.cursor.style.transform = `translate(${x}px, ${y}px)`;
    void this.cursor.offsetWidth;
    this.cursor.style.transition = '';
    this.cursor.classList.add('on');
  }
  hide() { this.cursor.classList.remove('on'); }
  async move(target, ms = 850, ox, oy) {
    const p = this.point(target, ox, oy);
    this.cursor.style.transitionDuration = `${ms}ms, ${ms}ms, 0.3s`;
    this.cursor.style.transform = `translate(${p.x}px, ${p.y}px)`;
    await this.wait(ms + 60);
    return p;
  }
  async click(target) {
    const p = this.point(target);
    this.cursor.classList.add('press');
    const ripple = document.createElement('span');
    ripple.className = 'ripple';
    ripple.style.left = `${p.x}px`; ripple.style.top = `${p.y}px`;
    this.win.appendChild(ripple);
    setTimeout(() => ripple.remove(), 700);
    await sleep(160);
    this.cursor.classList.remove('press');
  }
  async type(field, text, speed = 55) {
    const out = field.querySelector('.typed');
    field.classList.add('focus');
    for (const ch of text) { out.textContent += ch; await sleep(speed + Math.random() * 40); }
    field.classList.remove('focus');
  }
}

async function runCheckout(d) {
  const item = d.el('item'), check = d.el('check'), submit = d.el('submit'), toast = d.el('toast'), offer = d.el('offer');
  for (;;) {
    d.win.classList.remove('state-done');
    [check, submit, toast, item, offer].forEach((e) => e.classList.remove('on', 'loading', 'done', 'hover'));
    await d.untilVisible();
    d.show(d.win.offsetWidth * 0.18, d.win.offsetHeight * 0.95);
    await d.wait(400);
    offer.classList.add('on');
    await d.move(item, 900, 0.3, 0.45); item.classList.add('hover');
    await d.wait(700); item.classList.remove('hover');
    await d.move(check, 900, 0.03, 0.5); await d.click(check); check.classList.add('on');
    await d.wait(350);
    await d.move(submit, 800); await d.click(submit); submit.classList.add('loading');
    await d.wait(1100);
    submit.classList.remove('loading'); submit.classList.add('done'); d.win.classList.add('state-done');
    toast.classList.add('on');
    await d.wait(500); d.hide();
    await d.wait(2600);
  }
}

async function runLogin(d) {
  const nav = d.el('nav'), sub = d.el('sub'), card = d.el('card'), email = d.el('email'), pass = d.el('pass'), login = d.el('login');
  for (;;) {
    [nav, sub, card, login].forEach((e) => e.classList.remove('on', 'loading', 'ok'));
    d.win.classList.remove('expanded');
    email.querySelector('.typed').textContent = ''; pass.querySelector('.typed').textContent = '';
    await d.untilVisible();
    d.show(d.win.offsetWidth * 0.6, d.win.offsetHeight * 0.9);
    await d.wait(400);
    await d.move(nav, 900, 0.4); await d.click(nav); nav.classList.add('on'); d.win.classList.add('expanded');
    await d.wait(450);
    await d.move(sub, 600, 0.4); await d.click(sub); sub.classList.add('on'); card.classList.add('on');
    await d.wait(500);
    await d.move(email, 800, 0.2); await d.click(email);
    await d.type(email, 'you@yourshop.com');
    await d.move(pass, 500, 0.2); await d.click(pass);
    await d.type(pass, '••••••••••', 45);
    await d.move(login, 600); await d.click(login); login.classList.add('loading');
    await d.wait(1000);
    login.classList.remove('loading'); card.classList.add('ok');
    await d.wait(400); d.hide();
    await d.wait(2800);
  }
}

async function runDownloads(d) {
  const rows = [...d.win.querySelectorAll('[data-row]')];
  for (;;) {
    rows.forEach((r) => r.classList.remove('loading', 'done'));
    await d.untilVisible();
    d.show(d.win.offsetWidth * 0.4, d.win.offsetHeight * 0.98);
    await d.wait(400);
    for (const [i, row] of rows.entries()) {
      const btn = row.querySelector('.dl');
      await d.move(btn, i ? 550 : 900); await d.click(btn);
      row.classList.add('loading');
      setTimeout(() => { row.classList.remove('loading'); row.classList.add('done'); }, 1300);
      await d.wait(i === rows.length - 1 ? 1300 : 380);
    }
    await d.wait(400); d.hide();
    await d.wait(3000);
  }
}

export function initSteps(reduced) {
  const [a, b, c] = ['#art1', '#art2', '#art3'].map((s) => document.querySelector(s));
  if (reduced) {
    a.querySelector('[data-el="check"]').classList.add('on');
    a.querySelector('[data-el="submit"]').classList.add('done');
    a.querySelector('[data-el="toast"]').classList.add('on');
    b.classList.add('expanded');
    ['nav', 'sub'].forEach((n) => b.querySelector(`[data-el="${n}"]`).classList.add('on'));
    b.querySelector('[data-el="card"]').classList.add('on', 'ok');
    c.querySelectorAll('[data-row]').forEach((r) => r.classList.add('done'));
    return;
  }
  runCheckout(new Demo(a));
  runLogin(new Demo(b));
  runDownloads(new Demo(c));
}
