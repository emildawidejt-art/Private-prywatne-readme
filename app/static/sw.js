'use strict';
const CACHE = 'lowca-shell-v1';
const ASSETS = ['/static/style.css','/static/archive.js','/static/app.js','/static/icon-192.png','/static/icon-512.png','/static/manifest.webmanifest'];
self.addEventListener('install', e => { e.waitUntil(caches.open(CACHE).then(c=>c.addAll(ASSETS))); self.skipWaiting(); });
self.addEventListener('activate', e => { e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k.startsWith('lowca-shell-')&&k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())); });
self.addEventListener('fetch', e => {
  if(e.request.method!=='GET'||new URL(e.request.url).origin!==self.location.origin)return;
  if(e.request.mode==='navigate') {
    e.respondWith(fetch(e.request).catch(()=>new Response('<!doctype html><html lang="pl"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Łowca Maszyn — brak połączenia</title><body><h1>Brak połączenia z internetem</h1><p>Łowca Maszyn potrzebuje internetu, aby sprawdzać prawdziwe ogłoszenia. Włącz Wi-Fi lub dane komórkowe i otwórz aplikację ponownie.</p><a href="/">Spróbuj ponownie</a></body></html>',{headers:{'Content-Type':'text/html; charset=utf-8'},status:503})));
  } else if(ASSETS.includes(new URL(e.request.url).pathname)) {
    e.respondWith(fetch(e.request).catch(()=>caches.match(e.request)));
  }
  // Search results, favorites and authenticated API responses are never cached here.
});
