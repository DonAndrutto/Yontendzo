/* Yontendzo service worker.
 *
 * Two jobs: make the app installable (browsers require a fetch handler
 * before they will offer "add to home screen"), and let it open without a
 * connection, which matters for a text people read in retreat and on the
 * road.
 *
 * The page is a single self-contained HTML file that is edited in place, so
 * navigations go to the network first and fall back to the cache only when
 * the network fails. A reader with a connection therefore always gets the
 * current text; a reader without one gets the last version they loaded.
 *
 * Bump CACHE_VERSION whenever the cached asset list changes; old caches are
 * dropped on activation.
 */

const CACHE_VERSION = 'v1';
const APP_CACHE = `ydz-app-${CACHE_VERSION}`;
const FONT_CACHE = `ydz-fonts-${CACHE_VERSION}`;
const CURRENT_CACHES = [APP_CACHE, FONT_CACHE];

// The page itself. Everything else is either inlined in it or optional.
const ESSENTIAL = ['./'];

const OPTIONAL = [
  './manifest.webmanifest',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/apple-touch-icon.png',
  './icons/favicon-32.png',
  './icons/favicon-96.png',
];

const FONT_HOSTS = ['fonts.googleapis.com', 'fonts.gstatic.com'];

self.addEventListener('install', event => {
  event.waitUntil((async () => {
    const cache = await caches.open(APP_CACHE);
    await cache.addAll(ESSENTIAL);
    // A missing or slow icon must not fail the whole installation.
    await Promise.allSettled(OPTIONAL.map(url => cache.add(url)));
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    const names = await caches.keys();
    await Promise.all(names
      .filter(name => name.startsWith('ydz-') && !CURRENT_CACHES.includes(name))
      .map(name => caches.delete(name)));
    await self.clients.claim();
  })());
});

async function networkFirst(request) {
  const cache = await caches.open(APP_CACHE);
  try {
    const response = await fetch(request);
    if (response && response.ok) cache.put(request, response.clone());
    return response;
  } catch (err) {
    // Offline: serve this page from the cache, falling back to the app root
    // for deep links that were never visited online.
    const cached = await cache.match(request, { ignoreSearch: true })
      || await cache.match('./');
    if (cached) return cached;
    throw err;
  }
}

async function staleWhileRevalidate(request, cacheName) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(request);
  const network = fetch(request).then(response => {
    // Opaque responses (cross-origin fonts) report status 0 but are still
    // usable from the cache, so they are kept too.
    if (response && (response.ok || response.type === 'opaque')) {
      cache.put(request, response.clone());
    }
    return response;
  }).catch(() => null);
  return cached || network.then(response => {
    if (response) return response;
    throw new Error('offline and not cached');
  });
}

self.addEventListener('fetch', event => {
  const { request } = event;
  if (request.method !== 'GET') return;
  if (request.headers.has('range')) return;

  const url = new URL(request.url);

  if (request.mode === 'navigate') {
    event.respondWith(networkFirst(request));
    return;
  }

  if (url.origin === self.location.origin
      && url.pathname.startsWith(new URL('./', self.location.href).pathname)) {
    event.respondWith(staleWhileRevalidate(request, APP_CACHE));
    return;
  }

  if (FONT_HOSTS.includes(url.hostname)) {
    event.respondWith(staleWhileRevalidate(request, FONT_CACHE));
  }
});
