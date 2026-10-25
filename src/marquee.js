// Plugin names taken from the coderizo Shopware 6 Extension Marketplace.
const FREE = [
  ['Advanced Live Search', 'Coderizo', 'search'],
  ['Extensions Manager', 'Coderizo', 'grid'],
  ['PayPal for Shopware 6', 'Shopware', 'card'],
  ['Migration Assistant', 'Shopware', 'swap'],
  ['Security Plugin', 'Shopware', 'shield'],
  ['Tools', 'FriendsOfShopware', 'wrench'],
  ['Mail Archive', 'FriendsOfShopware', 'mail'],
  ['Language Pack', 'Shopware', 'globe'],
  ['Thumbnail Processor', 'FriendsOfShopware', 'image'],
  ['Altcha Captcha', 'FriendsOfShopware', 'lock'],
  ['Product Compare', 'FriendsOfShopware', 'layers'],
  ['Mollie Payments', 'Mollie', 'card'],
  ['Flow Builder Insights', 'FriendsOfShopware', 'chart'],
  ['Agentic Commerce', 'Shopware', 'spark'],
];
const POPULAR = [
  ['Two-Factor Authentication', 'Storefront & Admin', 'shield'],
  ['Extended Sitemap', 'SEO', 'layers'],
  ['Smart One Page Checkout', 'Checkout', 'card'],
  ['SEO Redirect Manager Pro', 'SEO', 'swap'],
  ['Cross-Selling Suggestions', 'Marketing', 'spark'],
  ['Google Tag Manager', 'Analytics', 'chart'],
  ['Hero Slider Pro', 'Shopping Experiences', 'image'],
  ['Feedback Xpert', 'Reviews', 'star'],
  ['FAQ Fox', 'SEO', 'search'],
  ['Commercial Customers Only', 'B2B', 'lock'],
  ['Elite Blog Pro', 'Content', 'doc'],
  ['BundleSpot Hotspots', 'Shopping Experiences', 'grid'],
  ['Bulk Order Processing', 'Admin', 'wrench'],
  ['Price on Request', 'B2B', 'mail'],
];

const ICONS = {
  search: '<circle cx="11" cy="11" r="6"/><path d="m20 20-4.5-4.5"/>',
  grid: '<rect x="4" y="4" width="7" height="7" rx="1.5"/><rect x="4" y="13" width="7" height="7" rx="1.5"/><rect x="13" y="13" width="7" height="7" rx="1.5"/><path d="m16.5 3 4 4-4 4-4-4z"/>',
  card: '<rect x="3" y="6" width="18" height="12" rx="2"/><path d="M3 10h18M7 15h4"/>',
  swap: '<path d="M4 8h13l-3-3M20 16H7l3 3"/>',
  shield: '<path d="M12 3 5 6v6c0 4 3 7.5 7 9 4-1.5 7-5 7-9V6z"/><path d="m9 12 2 2 4-4"/>',
  wrench: '<path d="M14.5 5.5a4 4 0 0 0 4.9 4.9L11 18.8a2 2 0 1 1-2.8-2.8l8.4-8.4"/>',
  mail: '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/>',
  globe: '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c3 3 3 15 0 18M12 3c-3 3-3 15 0 18"/>',
  image: '<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="10" r="2"/><path d="m21 16-5-5-9 9"/>',
  lock: '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>',
  layers: '<path d="m12 3 9 5-9 5-9-5z"/><path d="m3 13 9 5 9-5"/>',
  chart: '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
  spark: '<path d="M12 3v4M12 17v4M3 12h4M17 12h4M6 6l2.5 2.5M15.5 15.5 18 18M6 18l2.5-2.5M15.5 8.5 18 6"/>',
  star: '<path d="m12 3 2.7 5.6 6.1.8-4.5 4.2 1.1 6L12 16.7 6.6 19.6l1.1-6L3.2 9.4l6.1-.8z"/>',
  doc: '<path d="M6 3h9l4 4v14H6z"/><path d="M9 12h7M9 16h5"/>',
};

const HUES = [['#1aab73', '#0e7f8c'], ['#2b7bff', '#5a3bff'], ['#16c1c8', '#1a6dff'], ['#8b5cf6', '#2b7bff'], ['#22c58b', '#16c1c8']];
// staggered spacing pattern (repeats identically in both copies, so the -50% loop stays seamless)
const GAPS = [28, 52, 36, 64, 30, 46];

function build(track, list, free) {
  const html = list.map(([name, by, icon], i) => {
    const [a, b] = HUES[i % HUES.length];
    return `<div class="mq-item" style="--gap:${GAPS[i % GAPS.length]}px;--a:${a};--b:${b}">
      <span class="mq-logo"><svg viewBox="0 0 24 24">${ICONS[icon]}</svg></span>
      <span class="mq-txt"><b>${name}</b><small>${by}</small></span>
      ${free ? '<em class="mq-free">FREE</em>' : '<em class="mq-hot">★ TOP</em>'}
    </div>`;
  }).join('');
  track.innerHTML = `<div class="mq-set">${html}</div><div class="mq-set" aria-hidden="true">${html}</div>`;
}

export function initMarquees() {
  build(document.getElementById('mqFree'), FREE, true);
  build(document.getElementById('mqPopular'), POPULAR, false);
}
