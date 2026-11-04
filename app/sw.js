/* FledgeView offline support. The app works offline after the first visit.
   When you publish a new version, change CACHE below (it follows the app's version number). */
const CACHE = 'fledgeview-0.9.40-beta';
const ASSETS = [
  "/app/",
  "/app/index.html",
  "/app/manifest.webmanifest",
  "/assets/exifr.umd.js",
  "/assets/jszip.min.js",
  "/assets/fonts/fonts.css",
  "/assets/fonts/barlow-latin-400-normal.woff2",
  "/assets/fonts/barlow-latin-500-normal.woff2",
  "/assets/fonts/barlow-latin-600-normal.woff2",
  "/assets/fonts/barlow-latin-700-normal.woff2",
  "/assets/fonts/barlow-condensed-latin-400-normal.woff2",
  "/assets/fonts/barlow-condensed-latin-500-normal.woff2",
  "/assets/fonts/barlow-condensed-latin-600-normal.woff2",
  "/assets/fonts/barlow-condensed-latin-700-normal.woff2",
  "/assets/icons/icon-192.png",
  "/assets/icons/icon-512.png",
  "/assets/icons/favicon-32.png",
  "/assets/icons/apple-touch-icon.png"
];
self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k.startsWith('fledgeview-') && k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET' || new URL(req.url).origin !== location.origin) return;
  if (req.mode === 'navigate') {
    /* the app page: try the network first so updates arrive, fall back to the saved copy offline */
    e.respondWith(fetch(req).then(r => { const c = r.clone(); caches.open(CACHE).then(x => x.put('/app/index.html', c)); return r; }).catch(() => caches.match('/app/index.html')));
    return;
  }
  e.respondWith(caches.match(req).then(hit => hit || fetch(req).then(r => { if (r.ok) { const c = r.clone(); caches.open(CACHE).then(x => x.put(req, c)); } return r; })));
});
