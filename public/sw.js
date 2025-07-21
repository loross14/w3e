self.addEventListener("install", () => {
  console.log("Service Worker installed");
});

self.addEventListener("fetch", (event) => {
  event.respondWith(
    caches.match(event.request).then((response) => {
      if (response) {
        return response;
      }
      return fetch(event.request);
    }),
  );
});

self.addEventListener("activate", () => {
  caches.keys().then((keys) => {
    return Promise.all(
      keys
        .filter((key) => key !== "crypto-portfolio-cache")
        .map((key) => caches.delete(key)),
    );
  });
});
