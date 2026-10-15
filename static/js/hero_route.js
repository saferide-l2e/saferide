/* SafeRide Lagos public stop-to-stop road preview. No GPS or live bus telemetry. */
(() => {
  "use strict";
  const root = document.querySelector("[data-route-hero]");
  if (!root) return;
  const mapNode = root.querySelector("#hero-route-map");
  const provider = root.querySelector("[data-map-provider]");
  const message = root.querySelector("[data-map-distance]");
  const motion = root.querySelector("[data-map-motion]");
  const from = root.querySelector("[data-map-origin]");
  const to = root.querySelector("[data-map-destination]");
  const originLabel = root.querySelector("[data-origin-label]");
  const destinationLabel = root.querySelector("[data-destination-label]");
  const directions = root.querySelector("[data-map-directions]");
  const busImage = root.dataset.danfoIcon;
  const googleKey = root.dataset.googleKey;
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  const stops = {
    "Jibowu": [3.36779, 6.52104], "Mile 2": [3.31175, 6.45998],
    "Yaba": [3.3792, 6.5098], "Oshodi": [3.3437, 6.5557],
    "Ikeja": [3.3482, 6.6018], "Agege": [3.3244, 6.6184],
    "Surulere": [3.3561, 6.4999], "CMS": [3.3922, 6.4482],
    "Victoria Island": [3.4217, 6.4281], "Lekki Phase 1": [3.4723, 6.4415],
    "Maryland": [3.3719, 6.5692], "Berger": [3.3701, 6.6465],
    "Ojota": [3.3811, 6.5841], "Iyana Ipaja": [3.2823, 6.6036]
  };
  let activeMap = null;
  let activeMarker = null;
  let activeBus = null;
  let currentRoute = [];
  let cumulative = [];
  let distance = 0;
  let raf = null;
  let lastFrame = null;
  let elapsed = 0;
  let moving = false;
  let generation = 0;
  let abortController = null;
  const duration = 24000;

  const point = name => ({ lng: stops[name][0], lat: stops[name][1] });
  const setMessage = value => { message.textContent = value; };
  const googleLink = () =>
    "https://www.google.com/maps/dir/?api=1&origin=" +
    encodeURIComponent(from.value + ", Lagos, Nigeria") + "&destination=" +
    encodeURIComponent(to.value + ", Lagos, Nigeria") + "&travelmode=driving";

  function syncLabels() {
    if (originLabel) originLabel.textContent = from.value;
    if (destinationLabel) destinationLabel.textContent = to.value;
    if (directions) directions.href = googleLink();
    mapNode.setAttribute("aria-label", "Road map from " + from.value + " to " + to.value + " in Lagos");
  }

  function script(src) {
    return new Promise((resolve, reject) => {
      const item = document.createElement("script");
      item.src = src; item.async = true;
      item.onload = resolve;
      item.onerror = () => reject(new Error("Map script could not load"));
      document.head.append(item);
    });
  }

  function valid(path) {
    return Array.isArray(path) && path.length > 1 && path.length < 15000 &&
      path.every(p => Number.isFinite(p.lat) && Number.isFinite(p.lng) &&
        p.lat > 5 && p.lat < 7 && p.lng > 2 && p.lng < 5);
  }
  function meters(a, b) {
    const r = Math.PI / 180;
    const y = Math.sin((b.lat - a.lat) * r / 2);
    const x = Math.sin((b.lng - a.lng) * r / 2);
    return 12742000 * Math.asin(Math.min(1, Math.sqrt(
      y * y + Math.cos(a.lat * r) * Math.cos(b.lat * r) * x * x
    )));
  }
  function atProgress(progress) {
    const goal = Math.min(1, Math.max(0, progress)) * distance;
    let low = 1, high = cumulative.length - 1;
    while (low < high) {
      const mid = (low + high) >> 1;
      if (cumulative[mid] < goal) low = mid + 1;
      else high = mid;
    }
    const i = Math.max(1, low);
    const left = currentRoute[i - 1], right = currentRoute[i];
    const span = cumulative[i] - cumulative[i - 1];
    const portion = span ? (goal - cumulative[i - 1]) / span : 0;
    return { lat: left.lat + (right.lat - left.lat) * portion,
      lng: left.lng + (right.lng - left.lng) * portion };
  }
  function bearing(a, b) {
    const rad = Math.PI / 180;
    const dy = (b.lng - a.lng) * Math.cos((a.lat + b.lat) * rad / 2);
    const dx = b.lat - a.lat;
    return Math.atan2(dy, dx) * 180 / Math.PI;
  }
  function pause() {
    moving = false;
    if (raf !== null) cancelAnimationFrame(raf);
    raf = null; lastFrame = null;
    motion.textContent = "Play bus animation ▶";
    motion.setAttribute("aria-pressed", "true");
  }
  function play() {
    if (moving || !activeMarker || !currentRoute.length) return;
    moving = true; lastFrame = null;
    motion.textContent = "Pause bus animation Ⅱ";
    motion.setAttribute("aria-pressed", "false");
    const frame = now => {
      if (!moving) return;
      if (!document.hidden && lastFrame !== null) elapsed = (elapsed +
        Math.min(80, Math.max(0, now - lastFrame))) % duration;
      lastFrame = now;
      const progress = elapsed / duration, p = atProgress(progress);
      const next = atProgress(Math.min(.9999, progress + .001));
      activeMarker(p, bearing(p, next));
      raf = requestAnimationFrame(frame);
    };
    raf = requestAnimationFrame(frame);
  }
  motion.addEventListener("click", () => moving ? pause() : play());
  reduceMotion.addEventListener?.("change", event => { if (event.matches) pause(); });
  document.addEventListener("visibilitychange", () => { lastFrame = null; });

  function animate(path, update) {
    pause(); currentRoute = path; activeMarker = update;
    cumulative = [0];
    for (let i = 1; i < path.length; i++) {
      cumulative.push(cumulative[i - 1] + meters(path[i - 1], path[i]));
    }
    distance = cumulative[cumulative.length - 1];
    elapsed = 0;
    if (distance > 0) {
      motion.disabled = false;
      update(path[0], bearing(path[0], path[1]));
      if (!reduceMotion.matches) play();
    }
  }
  function icon() {
    const image = document.createElement("img");
    image.src = busImage;
    image.alt = "";
    image.setAttribute("aria-hidden", "true");
    image.className = "site-map-google-bus";
    image.style.width = "54px";
    image.style.maxWidth = "54px";
    image.style.filter = "drop-shadow(0 4px 4px #0b241d70)";
    return image;
  }

  async function openFreeMap(id, start, end) {
    if (!window.maplibregl) {
      await script("https://unpkg.com/maplibre-gl@5.6.0/dist/maplibre-gl.js");
    }
    if (id !== generation) return;
    mapNode.replaceChildren();
    const map = new maplibregl.Map({
      container: mapNode, style: "https://tiles.openfreemap.org/styles/liberty",
      center: start, zoom: 10.4, attributionControl: true,
      dragRotate: false, pitchWithRotate: false
    });
    activeMap = map;
    map.scrollZoom.disable();
    map.touchZoomRotate.disableRotation();
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-left");
    await new Promise((resolve, reject) => {
      const timer = setTimeout(() => reject(new Error("Map tiles timed out")), 16000);
      map.once("load", () => { clearTimeout(timer); resolve(); });
      map.on("error", event => {
        if (!map.isStyleLoaded()) { clearTimeout(timer); reject(event.error || new Error("Tiles unavailable")); }
      });
    });
    if (id !== generation) return;
    provider.textContent = "OpenFreeMap";
    for (const [coordinate, label, last] of [[start, "A", false], [end, "B", true]]) {
      const pin = document.createElement("span");
      pin.className = "site-map-stop" + (last ? " site-map-stop--end" : "");
      pin.textContent = label;
      pin.setAttribute("aria-hidden", "true");
      new maplibregl.Marker({ element: pin }).setLngLat(coordinate).addTo(map);
    }
    const fit = points => {
      const bounds = points.reduce((box, value) => box.extend(value),
        new maplibregl.LngLatBounds(points[0], points[0]));
      map.fitBounds(bounds, { padding: 48, maxZoom: 13, duration: 0 });
    };
    fit([start, end]);
    setMessage("Finding a road route between your stops…");
    abortController = new AbortController();
    const timer = setTimeout(() => abortController.abort(), 12000);
    try {
      const url = "https://router.project-osrm.org/route/v1/driving/" +
        start.join(",") + ";" + end.join(",") + "?overview=full&geometries=geojson";
      const response = await fetch(url, { signal: abortController.signal });
      if (!response.ok) throw new Error("Road routing unavailable");
      const body = await response.json();
      const road = body.routes?.[0];
      const path = road?.geometry?.coordinates?.map(([lng, lat]) => ({ lng, lat }));
      if (!valid(path)) throw new Error("Invalid mapped road route");
      if (id !== generation) return;
      const positions = path.map(p => [p.lng, p.lat]);
      map.addSource("journey", {
        type: "geojson", data: {
          type: "Feature", properties: {}, geometry: { type: "LineString", coordinates: positions }
        }
      });
      map.addLayer({
        id: "journey-glow", type: "line", source: "journey",
        layout: { "line-join": "round", "line-cap": "round" },
        paint: { "line-color": "#cfff47", "line-width": 9 }
      });
      map.addLayer({
        id: "journey-line", type: "line", source: "journey",
        layout: { "line-join": "round", "line-cap": "round" },
        paint: { "line-color": "#03795b", "line-width": 4 }
      });
      fit(positions);
      const bus = icon();
      activeBus = new maplibregl.Marker({ element: bus, anchor: "center",
        rotationAlignment: "viewport" }).setLngLat(positions[0]).addTo(map);
      animate(path, (position, direction) => {
        activeBus.setLngLat([position.lng, position.lat]);
        // Slight course correction keeps the illustrative danfo upright and small.
        bus.style.rotate = Math.max(-18, Math.min(18, direction - 90)) + "deg";
      });
      setMessage("Approx. " + (road.distance / 1000).toFixed(1) + " km by road · Bus follows the mapped route");
    } catch (error) {
      if (id === generation) setMessage("Road directions temporarily unavailable. Open in Google Maps for directions.");
      console.warn("SafeRide route preview:", error.message);
    } finally {
      clearTimeout(timer);
      if (id === generation) setTimeout(() => map.resize(), 100);
    }
  }

  async function googleRoute(id, start, end) {
    if (!googleKey) throw new Error("No Google key");
    if (!window.google?.maps?.importLibrary) {
      await script("https://maps.googleapis.com/maps/api/js?key=" +
        encodeURIComponent(googleKey) + "&v=weekly&loading=async");
    }
    if (id !== generation) return;
    const [{ Map }, { Route }] = await Promise.all([
      google.maps.importLibrary("maps"), google.maps.importLibrary("routes")
    ]);
    const result = await Route.computeRoutes({
      origin: { lat: start[1], lng: start[0] },
      destination: { lat: end[1], lng: end[0] },
      travelMode: "DRIVING", fields: ["path", "distanceMeters"]
    });
    const road = result.routes?.[0];
    const path = road?.path?.map(p => ({
      lat: typeof p.lat === "function" ? p.lat() : p.lat,
      lng: typeof p.lng === "function" ? p.lng() : p.lng
    }));
    if (!valid(path)) throw new Error("Google route has no valid geometry");
    if (id !== generation) return;
    mapNode.replaceChildren();
    const map = new Map(mapNode, {
      center: { lat: start[1], lng: start[0] }, zoom: 11,
      gestureHandling: "cooperative", mapTypeControl: false,
      streetViewControl: false, fullscreenControl: false
    });
    new google.maps.Polyline({
      map, path, strokeColor: "#087657", strokeWeight: 7, strokeOpacity: .95
    });
    const bounds = new google.maps.LatLngBounds();
    path.forEach(p => bounds.extend(p)); map.fitBounds(bounds, 50);
    for (const [position, label] of [[start, "A"], [end, "B"]]) {
      new google.maps.Marker({ map, label, position: { lat: position[1], lng: position[0] } });
    }
    const danfo = new google.maps.Marker({
      map, position: path[0], title: "Illustrative SafeRide danfo",
      icon: { url: busImage, scaledSize: new google.maps.Size(54, 39),
        anchor: new google.maps.Point(27, 25) }
    });
    activeBus = danfo;
    provider.textContent = "Google Maps";
    animate(path, p => danfo.setPosition(p));
    setMessage("Approx. " + ((road.distanceMeters || distance) / 1000).toFixed(1) +
      " km by road · Bus follows the mapped route");
  }

  async function show() {
    const id = ++generation;
    pause(); motion.disabled = true;
    currentRoute = []; activeMarker = null; activeBus = null;
    if (abortController) abortController.abort();
    if (activeMap) { activeMap.remove(); activeMap = null; }
    syncLabels();
    mapNode.replaceChildren();
    if (!stops[from.value] || !stops[to.value] || from.value === to.value) {
      provider.textContent = "Select a route";
      setMessage("Choose two different Lagos bus stops.");
      return;
    }
    const start = stops[from.value], end = stops[to.value];
    provider.textContent = "Loading route…";
    setMessage("Connecting " + from.value + " to " + to.value + "…");
    if (googleKey) {
      try { await googleRoute(id, start, end); return; }
      catch (error) { console.warn("Google route unavailable; trying OpenFreeMap", error.message); }
    }
    try { await openFreeMap(id, start, end); }
    catch (error) {
      if (id !== generation) return;
      provider.textContent = "Map unavailable";
      const link = document.createElement("a");
      link.href = googleLink(); link.rel = "noopener noreferrer";
      link.target = "_blank"; link.textContent = "Open road directions in Google Maps ↗";
      mapNode.replaceChildren(link);
      setMessage("Map provider is temporarily unavailable.");
    }
  }
  from.addEventListener("change", show);
  to.addEventListener("change", show);
  show();
})();