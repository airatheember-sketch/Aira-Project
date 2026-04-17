// AIRA Service Worker — Phase 6
const CACHE = 'aira-v1';
const SHELL = ['/', '/manifest.json'];

// ── Install: cache the app shell ──
self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting())
  );
});

// ── Activate: wipe old caches ──
self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

// ── Fetch strategy ──
// API calls (auth, chat, tts, ws) → always network, never cache
// App shell (/, /manifest.json) → cache-first with network fallback
self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);

  // Never intercept WebSocket upgrades
  if (e.request.headers.get('upgrade') === 'websocket') return;

  // Never cache API routes
  const apiPrefixes = ['/auth/', '/chat/', '/tts/', '/ws/', '/health'];
  if (apiPrefixes.some(p => url.pathname.startsWith(p))) {
    e.respondWith(fetch(e.request));
    return;
  }

  // App shell — cache-first
  e.respondWith(
    caches.match(e.request).then(cached => {
      if (cached) return cached;
      return fetch(e.request).then(res => {
        // Only cache same-origin GET responses
        if (
          res.ok &&
          e.request.method === 'GET' &&
          url.origin === self.location.origin
        ) {
          const clone = res.clone();
          caches.open(CACHE).then(c => c.put(e.request, clone));
        }
        return res;
      });
    }).catch(() => {
      // Offline fallback — return cached root
      if (e.request.destination === 'document') {
        return caches.match('/');
      }
    })
  );
});