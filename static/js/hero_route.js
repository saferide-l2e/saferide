/* Public road-route illustration. No live vehicle telemetry. */
(() => {
  "use strict";
  const root = document.querySelector("[data-route-hero]");
  if (!root) return;
  const mapNode = root.querySelector("#hero-route-map");
  const message = root.querySelector("[data-map-distance]");
  const motion = root.querySelector("[data-map-motion]");
  const from = root.querySelector("[data-map-origin]");
  const to = root.querySelector("[data-map-destination]");
  const directions = root.querySelector("[data-map-directions]");
  const reduceMotion = matchMedia("(prefers-reduced-motion: reduce)");
  const stops = {
    "Jibowu": [3.36779, 6.52104], "Mile 2": [3.31175, 6.45998],
    "Yaba": [3.3792, 6.5098], "Oshodi": [3.3437, 6.5557],
    "Ikeja": [3.3482, 6.6018], "Agege": [3.3244, 6.6184],
    "Surulere": [3.3561, 6.4999], "CMS": [3.3922, 6.4482],
    "Victoria Island": [3.4217, 6.4281], "Lekki Phase 1": [3.4723, 6.4415],
    "Maryland": [3.3719, 6.5692], "Berger": [3.3701, 6.6465],
    "Ojota": [3.3811, 6.5841], "Iyana Ipaja": [3.2823, 6.6036]
  };
  const loaders = new Map();
  let googleReady = null;
  let active = null;
  let generation = 0;
  const live = session => active === session && !session.controller.signal.aborted;
  const coordinate = p => [p.lng, p.lat];
  const latlng = p => ({lng: p[0], lat: p[1]});
  const valid = path => Array.isArray(path) && path.length > 1 && path.length < 15000 &&
    path.every(p => Number.isFinite(p.lat) && Number.isFinite(p.lng) &&
      p.lat > 5 && p.lat < 7 && p.lng > 2 && p.lng < 5);

  function bounded(promise, signal, timeout = 16000) {
    return new Promise((resolve, reject) => {
      const abort = () => { clearTimeout(timer); reject(new Error("Route cancelled")); };
      const timer = setTimeout(() => {
        signal?.removeEventListener("abort", abort);
        reject(new Error("Route request timed out"));
      }, timeout);
      if (signal?.aborted) { abort(); return; }
      signal?.addEventListener("abort", abort, {once: true});
      promise.then(value => {
        clearTimeout(timer); signal?.removeEventListener("abort", abort); resolve(value);
      }, error => {
        clearTimeout(timer); signal?.removeEventListener("abort", abort); reject(error);
      });
    });
  }
  function script(name, src) {
    if (loaders.has(name)) return loaders.get(name);
    const pending = new Promise((resolve, reject) => {
      const tag = document.createElement("script");
      const timer = setTimeout(() => { tag.remove(); reject(new Error("Map script timed out")); }, 16000);
      tag.src = src; tag.async = true;
      tag.onload = () => { clearTimeout(timer); resolve(); };
      tag.onerror = () => { clearTimeout(timer); tag.remove(); reject(new Error("Map script unavailable")); };
      document.head.append(tag);
    }).catch(error => { loaders.delete(name); throw error; });
    loaders.set(name, pending);
    return pending;
  }
  function syncLabels() {
    root.querySelector("[data-origin-label]").textContent = from.value;
    root.querySelector("[data-destination-label]").textContent = to.value;
    directions.href = "https://www.google.com/maps/dir/?api=1&origin=" +
      encodeURIComponent(from.value + ", Lagos, Nigeria") + "&destination=" +
      encodeURIComponent(to.value + ", Lagos, Nigeria") + "&travelmode=driving";
    mapNode.setAttribute("aria-label", `Lagos road map from ${from.value} to ${to.value}`);
    const searchFrom = document.querySelector("#site-from"), searchTo = document.querySelector("#site-to");
    if (searchFrom) searchFrom.value = from.value;
    if (searchTo) searchTo.value = to.value;
  }
  function motionState(state) {
    root.dataset.motion = state;
    motion.textContent = state === "playing" ? "Pause" : state === "arrived" ? "Replay" : "Play";
    motion.setAttribute("aria-label", state === "playing" ? "Pause bus animation" :
      state === "arrived" ? "Replay bus animation" : "Play bus animation");
    motion.setAttribute("aria-pressed", String(state !== "playing"));
  }
  function vehicle() {
    // The library owns the outer transform; only our inner sprite rotates.
    const element = document.createElement("div");
    element.className = "danfo-marker";
    element.setAttribute("aria-hidden", "true");
    const image = document.createElement("img");
    image.className = "danfo-vehicle";
    image.src = root.dataset.danfoIcon;
    image.alt = ""; image.draggable = false;
    image.width = 80; image.height = 44;
    element.append(image);
    return {element, image};
  }
  function orient(image, heading) {
    image.style.transform = `rotate(${heading}deg)`;
    image.dataset.heading = heading.toFixed(2);
  }
  function stopElement(name, end) {
    const pin = document.createElement("span");
    pin.className = "site-map-stop" + (end ? " site-map-stop--end" : "");
    pin.textContent = end ? "B" : "A";
    pin.title = name;
    pin.setAttribute("aria-label", name);
    return pin;
  }
  function startAnimation(session, adapter, path) {
    if (!live(session)) return;
    session.animation = SafeRideMotion.createAnimator({
      path, marker: adapter.vehicle(path[0]), project: p => adapter.project(p), onState: motionState
    });
    adapter.onMove(() => session.animation?.refresh());
    root.dataset.mapState = "ready";
    mapNode.setAttribute("aria-busy", "false");
    motion.disabled = false;
    motionState("paused");
    if (!reduceMotion.matches) session.animation.play();
  }
  function distanceLabel(value) {
    return Number.isFinite(value) && value > 0 ? `Approx. ${(value / 1000).toFixed(1)} km by road` : "Road route ready";
  }
  function watchSize(callback) {
    let previous = mapNode.getBoundingClientRect();
    const observer = new ResizeObserver(() => {
      const size = mapNode.getBoundingClientRect();
      if (Math.abs(size.width - previous.width) > 1 || Math.abs(size.height - previous.height) > 1) {
        previous = size; callback();
      }
    });
    observer.observe(mapNode);
    return () => observer.disconnect();
  }

  async function freeMap(session, start, end) {
    await bounded(window.maplibregl ? Promise.resolve() :
      script("maplibre", "https://unpkg.com/maplibre-gl@5.6.0/dist/maplibre-gl.js"), session.controller.signal);
    if (!live(session)) return;
    mapNode.replaceChildren();
    const map = new maplibregl.Map({
      container: mapNode, style: "https://tiles.openfreemap.org/styles/liberty",
      center: start, zoom: 11, attributionControl: true, dragRotate: false, pitchWithRotate: false
    });
    const markers = [];
    let unwatch = () => {};
    session.cleanup = () => { unwatch(); markers.forEach(m => m.remove()); map.remove(); };
    map.scrollZoom.disable(); map.touchZoomRotate.disableRotation();
    map.addControl(new maplibregl.NavigationControl({showCompass: false}), "top-left");
    await bounded(new Promise((resolve, reject) => {
      map.once("load", resolve);
      map.on("error", e => { if (!map.isStyleLoaded()) reject(e.error || new Error("Map unavailable")); });
    }), session.controller.signal);
    if (!live(session)) return;
    const fit = points => {
      const bounds = points.reduce((box, p) => box.extend(p), new maplibregl.LngLatBounds(points[0], points[0]));
      map.fitBounds(bounds, {padding: {top: 45, bottom: 78, left: 36, right: 36}, maxZoom: 14, duration: 0});
    };
    fit([start, end]);
    const url = "https://router.project-osrm.org/route/v1/driving/" +
      start.join(",") + ";" + end.join(",") + "?overview=full&geometries=geojson";
    const request = new AbortController();
    const cancel = () => request.abort();
    session.controller.signal.addEventListener("abort", cancel, {once: true});
    const timeout = setTimeout(cancel, 16000);
    let road;
    try {
      const response = await fetch(url, {signal: request.signal});
      if (!response.ok) throw new Error("Road directions unavailable");
      road = (await response.json()).routes?.[0];
    } finally {
      clearTimeout(timeout); session.controller.signal.removeEventListener("abort", cancel);
    }
    if (!live(session)) return;
    const path = road?.geometry?.coordinates?.map(latlng);
    if (!valid(path)) throw new Error("No suitable road route");
    const positions = path.map(coordinate);
    map.addSource("journey", {type: "geojson", data: {
      type: "Feature", properties: {}, geometry: {type: "LineString", coordinates: positions}
    }});
    for (const [id, color, width] of [["journey-halo", "#d6f86c", 9], ["journey-line", "#087657", 4]]) {
      map.addLayer({id, type: "line", source: "journey", layout: {"line-join": "round", "line-cap": "round"},
        paint: {"line-color": color, "line-width": width}});
    }
    fit(positions);
    for (const [p, name, endStop] of [[positions[0], from.value, false], [positions.at(-1), to.value, true]]) {
      markers.push(new maplibregl.Marker({element: stopElement(name, endStop)}).setLngLat(p).addTo(map));
    }
    startAnimation(session, {
      project: p => map.project(coordinate(p)),
      onMove: callback => map.on("move", callback),
      vehicle(p) {
        const {element, image} = vehicle();
        const marker = new maplibregl.Marker({element, anchor: "center", rotationAlignment: "viewport",
          pitchAlignment: "viewport", subpixelPositioning: true}).setLngLat(coordinate(p)).addTo(map);
        markers.push(marker);
        return {update(position, angle) { marker.setLngLat(coordinate(position)); orient(image, angle); },
          remove: () => marker.remove()};
      }
    }, path);
    unwatch = watchSize(() => { map.resize(); fit(positions); });
    message.textContent = distanceLabel(road.distance);
  }

  async function googleMap(session, start, end) {
    if (!window.google?.maps?.importLibrary && !googleReady) {
      // loading=async may fire script.onload before the Maps bootstrap is ready.
      // Its documented callback is the readiness contract, not the script event.
      googleReady = new Promise((resolve, reject) => {
        window.safeRideMapsReady = () => { delete window.safeRideMapsReady; resolve(); };
        script("google", "https://maps.googleapis.com/maps/api/js?key=" +
          encodeURIComponent(root.dataset.googleKey) +
          "&v=weekly&loading=async&callback=safeRideMapsReady").catch(reject);
      });
    }
    await bounded(window.google?.maps?.importLibrary ? Promise.resolve() : googleReady, session.controller.signal);
    const [{Map}, {Route}] = await bounded(Promise.all([
      google.maps.importLibrary("maps"), google.maps.importLibrary("routes")
    ]), session.controller.signal);
    const result = await bounded(Route.computeRoutes({origin: latlng(start), destination: latlng(end),
      travelMode: "DRIVING", fields: ["path", "distanceMeters"]}), session.controller.signal);
    if (!live(session)) return;
    const road = result.routes?.[0];
    const path = road?.path?.map(p => ({lat: typeof p.lat === "function" ? p.lat() : p.lat,
      lng: typeof p.lng === "function" ? p.lng() : p.lng}));
    if (!valid(path)) throw new Error("No suitable road route");
    mapNode.replaceChildren();
    const map = new Map(mapNode, {center: path[0], zoom: 11, tilt: 0, gestureHandling: "cooperative",
      mapTypeControl: false, streetViewControl: false, fullscreenControl: false});
    const overlays = [];
    let unwatch = () => {};
    // OverlayView is a supported DOM marker without an AdvancedMarker map-ID requirement.
    class DomMarker extends google.maps.OverlayView {
      constructor(element, position) {
        super(); this.element = element; this.position = position;
        this.ready = new Promise(resolve => { this.resolveReady = resolve; });
        this.setMap(map);
      }
      onAdd() { this.getPanes().overlayMouseTarget.append(this.element); }
      draw() {
        const p = this.getProjection()?.fromLatLngToDivPixel(new google.maps.LatLng(this.position));
        if (p) {
          this.element.style.left = p.x + "px"; this.element.style.top = p.y + "px";
          this.resolveReady?.(); this.resolveReady = null;
        }
      }
      onRemove() { this.element.remove(); }
    }
    const line = new google.maps.Polyline({map, path, strokeColor: "#087657", strokeWeight: 5, strokeOpacity: .95});
    session.cleanup = () => {
      unwatch(); line.setMap(null); overlays.forEach(item => item.setMap(null));
      google.maps.event.clearInstanceListeners(map);
    };
    const bounds = new google.maps.LatLngBounds();
    path.forEach(p => bounds.extend(p));
    const fit = () => map.fitBounds(bounds, {top: 45, bottom: 60, left: 36, right: 36});
    fit();
    for (const [p, name, last] of [[path[0], from.value, false], [path.at(-1), to.value, true]]) {
      const element = document.createElement("div");
      element.className = "danfo-overlay-stop"; element.append(stopElement(name, last));
      overlays.push(new DomMarker(element, p));
    }
    const probe = new DomMarker(document.createElement("span"), path[0]);
    overlays.push(probe);
    // idle can precede an overlay's first draw. Wait for its usable projection.
    await bounded(probe.ready, session.controller.signal);
    if (!live(session)) return;
    startAnimation(session, {
      project: p => probe.getProjection().fromLatLngToDivPixel(new google.maps.LatLng(p)),
      onMove: callback => google.maps.event.addListener(map, "bounds_changed", callback),
      vehicle(p) {
        const {element, image} = vehicle(); element.classList.add("danfo-google-marker");
        const marker = new DomMarker(element, p); overlays.push(marker);
        return {update(position, angle) { marker.position = position; marker.draw(); orient(image, angle); },
          remove: () => marker.setMap(null)};
      }
    }, path);
    unwatch = watchSize(fit);
    message.textContent = distanceLabel(road.distanceMeters);
  }

  function fallback(session) {
    if (!live(session)) return;
    session.cleanup?.(); session.cleanup = null;
    session.animation?.destroy(); session.animation = null;
    root.dataset.mapState = "unavailable";
    mapNode.setAttribute("aria-busy", "false");
    const panel = document.createElement("div"); panel.className = "site-map-loading";
    const text = document.createElement("strong"); text.textContent = "Your route, one tap away";
    const link = document.createElement("a");
    link.href = directions.href; link.target = "_blank"; link.rel = "noopener noreferrer";
    link.textContent = "View directions ↗"; panel.append(text, link);
    mapNode.replaceChildren(panel);
    message.textContent = "Road preview unavailable. View directions to plan your journey.";
  }
  async function show() {
    if (active) {
      active.controller.abort(); active.animation?.destroy(); active.cleanup?.();
    }
    const session = {id: ++generation, controller: new AbortController()};
    active = session;
    motion.disabled = true; motionState("paused"); syncLabels();
    root.dataset.mapState = "loading"; mapNode.setAttribute("aria-busy", "true");
    const loading = document.createElement("div"); loading.className = "site-map-loading";
    loading.textContent = "Finding your road route…"; mapNode.replaceChildren(loading);
    message.textContent = "Connecting your stops…";
    if (!stops[from.value] || !stops[to.value] || from.value === to.value) {
      fallback(session); message.textContent = "Choose two different Lagos stops."; return;
    }
    const start = stops[from.value], end = stops[to.value];
    if (root.dataset.googleKey) {
      try { await googleMap(session, start, end); return; }
      catch (_) { if (!live(session)) return; session.cleanup?.(); session.cleanup = null; }
    }
    try { await freeMap(session, start, end); }
    catch (_) { fallback(session); }
  }
  motion.addEventListener("click", () => {
    if (root.dataset.motion === "playing") active?.animation?.pause();
    else active?.animation?.play();
  });
  reduceMotion.addEventListener("change", event => { if (event.matches) active?.animation?.pause(); });
  from.addEventListener("change", show); to.addEventListener("change", show);
  window.addEventListener("pagehide", () => {
    active?.controller.abort(); active?.animation?.destroy(); active?.cleanup?.(); active = null;
  });
  show();
})();
