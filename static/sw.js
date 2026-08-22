/**
 * NEXA PRIME v2 — Production Service Worker
 * Suzanne Tenekecioğlu | Coldwell Banker VIP
 * Caching Strategies: Cache-First for Static, Network-First for Dynamic APIs, Offline Navigation Fallback
 */

const CACHE_VERSION = 'nexa-suzanne-v2.2.0';
const STATIC_CACHE = `static-${CACHE_VERSION}`;
const API_CACHE = `api-${CACHE_VERSION}`;
const OFFLINE_CACHE = `offline-${CACHE_VERSION}`;

const PRECACHE_STATIC_ASSETS = [
    '/site',
    '/manifest.json',
    '/favicon.ico',
    '/apple-touch-icon.png',
    '/static/img/suzanne_icon_circle_32.png',
    '/static/img/suzanne_icon_circle_64.png',
    '/static/img/suzanne_icon_circle_180.png',
    '/static/img/suzanne_icon_circle_192.png',
    '/static/img/suzanne_favicon_192.png',
    '/static/img/suzanne_favicon_512.png',
    '/static/img/suzanne_hero.jpeg',
    'https://fonts.googleapis.com/css2?family=Inter:wght@200;300;400;500;600;700&family=Outfit:wght@200;300;400;500;600;700&display=swap',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css',
    'https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js',
    'https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/ScrollTrigger.min.js'
];

const OFFLINE_FALLBACK_HTML = `<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Çevrimdışı Mod | Suzanne Tenekecioğlu VIP</title>
    <style>
        :root { --bg: #040408; --card: #0c0c14; --accent: #0071E3; --text: #FFFFFF; --text-muted: #8E8E93; }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { background: var(--bg); color: var(--text); font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; display: flex; align-items: center; justify-content: center; min-height: 100vh; padding: 24px; text-align: center; }
        .offline-card { background: var(--card); border: 1px solid rgba(255,255,255,0.1); border-radius: 24px; padding: 40px 28px; max-width: 440px; width: 100%; box-shadow: 0 20px 50px rgba(0,0,0,0.6); }
        .icon-wrap { width: 72px; height: 72px; background: rgba(0,113,227,0.15); border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; margin-bottom: 20px; color: var(--accent); font-size: 28px; }
        h1 { font-size: 22px; font-weight: 700; margin-bottom: 12px; letter-spacing: -0.02em; }
        p { font-size: 14px; color: var(--text-muted); line-height: 1.6; margin-bottom: 24px; }
        .btn { display: inline-flex; align-items: center; justify-content: center; gap: 8px; background: var(--accent); color: #fff; text-decoration: none; padding: 12px 24px; border-radius: 12px; font-size: 14px; font-weight: 600; border: none; cursor: pointer; transition: transform 0.2s, opacity 0.2s; width: 100%; }
        .btn:active { transform: scale(0.98); }
        .contact-box { margin-top: 20px; padding-top: 20px; border-top: 1px solid rgba(255,255,255,0.08); font-size: 13px; color: var(--text-muted); }
        .contact-box a { color: #25D366; text-decoration: none; font-weight: 600; }
    </style>
</head>
<body>
    <div class="offline-card">
        <div class="icon-wrap">⚡</div>
        <h1>Şu Anda Çevrimdışısınız</h1>
        <p>İnternet bağlantınızı kontrol edin. Daha önce görüntülediğiniz portföy verilerine önbellekten erişebilirsiniz.</p>
        <button class="btn" onclick="window.location.reload()">Yeniden Dene</button>
        <div class="contact-box">
            Doğrudan İletişim: <a href="tel:+905354895656">+90 535 489 56 56</a>
        </div>
    </div>
</body>
</html>`;

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(STATIC_CACHE).then(async (cache) => {
            await Promise.allSettled(
                PRECACHE_STATIC_ASSETS.map((url) =>
                    cache.add(new Request(url, { cache: 'reload' })).catch((err) => {
                        console.warn('[SW] Pre-caching asset failed (ignoring):', url, err);
                    })
                )
            );
            const offlineResp = new Response(OFFLINE_FALLBACK_HTML, {
                headers: { 'Content-Type': 'text/html; charset=utf-8' }
            });
            await cache.put('/offline-fallback.html', offlineResp);
        }).then(() => self.skipWaiting())
    );
});

self.addEventListener('activate', (event) => {
    const validCaches = [STATIC_CACHE, API_CACHE, OFFLINE_CACHE];
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((name) => {
                    if (!validCaches.includes(name)) {
                        console.log('[SW] Deleting legacy cache:', name);
                        return caches.delete(name);
                    }
                })
            );
        }).then(() => self.clients.claim())
    );
});

self.addEventListener('message', (event) => {
    if (event.data && event.data.action === 'skipWaiting') {
        self.skipWaiting();
    }
});

self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    if (request.method !== 'GET') {
        return;
    }

    if (
        request.headers.get('range') ||
        url.pathname.endsWith('.mp4') ||
        url.pathname.endsWith('.pdf') ||
        url.pathname.startsWith('/stream/') ||
        url.pathname.startsWith('/download/') ||
        url.pathname === '/1.mp4' ||
        url.pathname === '/video/1.mp4'
    ) {
        return;
    }

    if (url.pathname.startsWith('/api/')) {
        event.respondWith(
            fetch(request)
                .then((networkResponse) => {
                    if (networkResponse && networkResponse.status === 200) {
                        const cloned = networkResponse.clone();
                        caches.open(API_CACHE).then((cache) => cache.put(request, cloned));
                    }
                    return networkResponse;
                })
                .catch(async () => {
                    const cachedResponse = await caches.match(request);
                    if (cachedResponse) {
                        return cachedResponse;
                    }
                    return new Response(
                        JSON.stringify({
                            success: false,
                            offline: true,
                            message: 'Çevrimdışı moddasınız. Güncel veriler internet bağlantısı kurulduğunda yenilenecektir.'
                        }),
                        {
                            status: 503,
                            headers: { 'Content-Type': 'application/json; charset=utf-8' }
                        }
                    );
                })
        );
        return;
    }

    if (request.mode === 'navigate' || (request.headers.get('accept') && request.headers.get('accept').includes('text/html'))) {
        event.respondWith(
            fetch(request)
                .then((networkResponse) => {
                    if (networkResponse && networkResponse.status === 200) {
                        const cloned = networkResponse.clone();
                        caches.open(STATIC_CACHE).then((cache) => cache.put(request, cloned));
                    }
                    return networkResponse;
                })
                .catch(async () => {
                    const cachedSite = (await caches.match(request)) || (await caches.match('/site'));
                    if (cachedSite) return cachedSite;
                    const offlineFallback = await caches.match('/offline-fallback.html');
                    return offlineFallback || new Response(OFFLINE_FALLBACK_HTML, {
                        headers: { 'Content-Type': 'text/html; charset=utf-8' }
                    });
                })
        );
        return;
    }

    event.respondWith(
        caches.match(request).then((cachedResponse) => {
            if (cachedResponse) {
                fetch(request)
                    .then((networkResponse) => {
                        if (networkResponse && networkResponse.status === 200) {
                            caches.open(STATIC_CACHE).then((cache) => cache.put(request, networkResponse));
                        }
                    })
                    .catch(() => {});
                return cachedResponse;
            }

            return fetch(request)
                .then((networkResponse) => {
                    if (networkResponse && networkResponse.status === 200) {
                        const cloned = networkResponse.clone();
                        caches.open(STATIC_CACHE).then((cache) => cache.put(request, cloned));
                    }
                    return networkResponse;
                })
                .catch(() => {
                    if (request.destination === 'image' || url.pathname.match(/\.(png|jpg|jpeg|svg|webp|gif)$/i)) {
                        return new Response(
                            '<svg xmlns="http://www.w3.org/2000/svg" width="300" height="200" viewBox="0 0 300 200"><rect width="300" height="200" fill="#0c0c14"/><text x="50%" y="50%" fill="#8E8E93" dominant-baseline="middle" text-anchor="middle" font-family="sans-serif" font-size="14">Görsel Çevrimdışı</text></svg>',
                            { headers: { 'Content-Type': 'image/svg+xml' } }
                        );
                    }
                });
        })
    );
});