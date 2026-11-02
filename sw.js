// OraNW Service Worker v7 — نسخة دون اتصال للصفحات فقط
var CACHE = 'oranw-v7.0';
var ASSETS = ['/', '/index.html', '/manifest.json', '/icon.svg', '/icon.png'];

self.addEventListener('install', function (e) {
  e.waitUntil(caches.open(CACHE).then(function (c) { return c.addAll(ASSETS); }));
  self.skipWaiting();
});

self.addEventListener('activate', function (e) {
  e.waitUntil(caches.keys().then(function (keys) {
    return Promise.all(keys.filter(function (k) { return k !== CACHE; }).map(function (k) { return caches.delete(k); }));
  }));
  self.clients.claim();
});

self.addEventListener('fetch', function (e) {
  if (e.request.method !== 'GET') return;
  var url = new URL(e.request.url);
  if (url.origin !== self.location.origin) return;           // لا نمس الطلبات الخارجية
  if (url.pathname.indexOf('/api/') === 0) return;           // أدوات الفحص والسرعة: دائمًا من الشبكة
  if (url.pathname.indexOf('/cdn-cgi/') === 0) return;
  if (/\.json$/.test(url.pathname) && url.pathname !== '/manifest.json') {
    // البيانات (مثل archive.json): الشبكة أولاً، والنسخة المحفوظة فقط عند انقطاع الاتصال
    e.respondWith(fetch(e.request).then(function (res) {
      if (res && res.ok) { var cl = res.clone(); caches.open(CACHE).then(function (c) { c.put(e.request, cl); }); }
      return res;
    }).catch(function () { return caches.match(e.request); }));
    return;
  }
  e.respondWith(
    caches.match(e.request).then(function (cached) {
      var fetched = fetch(e.request).then(function (res) {
        if (res && res.ok) { var clone = res.clone(); caches.open(CACHE).then(function (c) { c.put(e.request, clone); }); }
        return res;
      }).catch(function () { return cached; });
      return cached || fetched;
    })
  );
});
