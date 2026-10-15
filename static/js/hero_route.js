/* SafeRide: route-following illustration; NOT GPS / live bus telemetry. */
(() => {
  "use strict";

  const root = document.querySelector("[data-route-hero]");
  if (!root) return;

  const element = root.querySelector("#hero-route-map");
  const message = root.querySelector("[data-map-distance]");
  const provider = root.querySelector("[data-map-provider]");
  const loading = root.querySelector("[data-map-loading]");
  const motion = root.querySelector("[data-map-motion]");
  const busImage = root.dataset.danfoIcon;
  const googleKey = root.dataset.googleKey;
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

  // Coordinates refer to public stop areas, not to an operator-approved bay.
  const JIBOWU = { lat: 6.52104, lng: 3.36779 };
  const MILE_TWO = { lat: 6.45998, lng: 3.31175 };
  const ROUTE_LINK = "https://www.google.com/maps/dir/?api=1" +
    "&origin=Jibowu%20Bus%20Stop%2C%20Lagos%2C%20Nigeria" +
    "&destination=Mile%202%20Bus%20Stop%2C%20Lagos%2C%20Nigeria" +
    "&travelmode=driving";

  let animationFrame = null;
  let travelling = false;
  let progressMs = 0;
  let previousFrame = null;
  let follow = null;
  let distanceTotal = 0;
  let cumulative = [];
  let routePoints = [];
  const loopMs = 22000;

  function showMessage(text) {
    message.textContent = text;
  }

  function hideLoading() {
    if (loading) loading.remove();
  }

  function loadScript(src) {
    return new Promise((resolve, reject) => {
      const tag = document.createElement("script");
      tag.src = src;
      tag.async = true;
      tag.onload = resolve;
      tag.onerror = () => reject(new Error("Map provider failed to load."));
      document.head.append(tag);
    });
  }

  function haversine(a, b) {
    const rad = Math.PI / 180;
    const dLat = (b.lat - a.lat) * rad;
    const dLng = (b.lng - a.lng) * rad;
    const p1 = a.lat * rad;
    const p2 = b.lat * rad;
    const sinLat = Math.sin(dLat / 2);
    const sinLng = Math.sin(dLng / 2);
    return 6371000 * 2 * Math.asin(Math.min(1, Math.sqrt(
      sinLat * sinLat + Math.cos(p1) * Math.cos(p2) * sinLng * sinLng
    )));
  }

  function prepareAnimation(path, moveBus) {
    if (!Array.isArray(path) || path.length < 2) return;
    routePoints = path;
    follow = moveBus;
    cumulative = [0];
    for (let i = 1; i < path.length; i += 1) {
      cumulative.push(cumulative[i - 1] + haversine(path[i - 1], path[i]));
    }
    distanceTotal = cumulative[cumulative.length - 1];
    if (!Number.isFinite(distanceTotal) || distanceTotal < 1) return;

    progressMs = 0;
    moveBus(path[0]);
    motion.disabled = false;
    motion.addEventListener("click", () => {
      if (travelling) {
        stopAnimation();
        showMessage("Route animation paused. Press Play to continue.");
      } else {
        startAnimation();
        showMessage("Illustrated danfo travelling along the mapped road.");
      }
    });
    if (reduceMotion.matches) {
      motion.innerHTML = 'Play animation <span aria-hidden="true">▶</span>';
      motion.setAttribute("aria-pressed", "true");
      showMessage("Road route ready · Animation paused (reduced motion)");
    } else {
      startAnimation();
    }
  }

  function locationAt(fraction) {
    const distance = Math.min(1, Math.max(0, fraction)) * distanceTotal;
    let lo = 0;
    let hi = cumulative.length - 1;
    while (lo < hi) {
      const mid = Math.floor((lo + hi) / 2);
      if (cumulative[mid] < distance) lo = mid + 1;
      else hi = mid;
    }
    const end = Math.max(1, lo);
    const beginning = end - 1;
    const width = cumulative[end] - cumulative[beginning];
    const t = width <= 0 ? 0 : (distance - cumulative[beginning]) / width;
    const a = routePoints[beginning];
    const b = routePoints[end];
    return { lat: a.lat + (b.lat - a.lat) * t, lng: a.lng + (b.lng - a.lng) * t };
  }

  function stopAnimation() {
    travelling = false;
    if (animationFrame !== null) cancelAnimationFrame(animationFrame);
    animationFrame = null;
    previousFrame = null;
    motion.innerHTML = 'Play animation <span aria-hidden="true">▶</span>';
    motion.setAttribute("aria-pressed", "true");
  }

  function startAnimation() {
    if (!follow || distanceTotal <= 0 || travelling) return;
    travelling = true;
    previousFrame = null;
    motion.innerHTML = 'Pause animation <span aria-hidden="true">Ⅱ</span>';
    motion.setAttribute("aria-pressed", "false");

    function frame(now) {
      if (!travelling) return;
      if (document.hidden) {
        previousFrame = now;
        animationFrame = requestAnimationFrame(frame);
        return;
      }
      if (previousFrame !== null) {
        progressMs = (progressMs + Math.min(80, now - previousFrame)) % loopMs;
      }
      previousFrame = now;
      follow(locationAt(progressMs / loopMs));
      animationFrame = requestAnimationFrame(frame);
    }

    animationFrame = requestAnimationFrame(frame);
  }

  document.addEventListener("visibilitychange", () => { previousFrame = null; });
  reduceMotion.addEventListener?.("change", event => {
    if (event.matches && travelling) stopAnimation();
  });

  function validRoadPath(points) {
    return Array.isArray(points) && points.length >= 2 && points.length < 15000 &&
      points.every(p => Number.isFinite(p.lat) && Number.isFinite(p.lng) &&
        p.lat > 5 && p.lat < 7 && p.lng > 2 && p.lng < 5);
  }

  async function showGoogle() {
    if (!googleKey) throw new Error("Google Maps key has not been configured.");

    await loadScript("https://maps.googleapis.com/maps/api/js?key=" +
      encodeURIComponent(googleKey) + "&v=weekly&loading=async");
    const [{ Map }, { Route }] = await Promise.all([
      google.maps.importLibrary("maps"),
      google.maps.importLibrary("routes")
    ]);
    const map = new Map(element, {
      center: JIBOWU,
      zoom: 12,
      mapId: "DEMO_MAP_ID",
      gestureHandling: "cooperative",
      mapTypeControl: false,
      fullscreenControl: false,
      streetViewControl: false
    });

    const response = await Route.computeRoutes({
      origin: "Jibowu Bus Stop, Yaba, Lagos, Nigeria",
      destination: "Mile 2 Bus Stop, Lagos, Nigeria",
      travelMode: "DRIVING",
      fields: ["path"]
    });
    const result = response.routes?.[0];
    if (!result?.path) throw new Error("Google Maps did not return a driving route.");
    const path = result.path.map(p => ({
      lat: typeof p.lat === "function" ? p.lat() : p.lat,
      lng: typeof p.lng === "function" ? p.lng() : p.lng
    }));
    if (!validRoadPath(path)) throw new Error("Invalid Google road route geometry.");
    const polyline = new google.maps.Polyline({
      map, path, strokeColor: "#0a825c", strokeOpacity: .95, strokeWeight: 7
    });
    const bounds = new google.maps.LatLngBounds();
    path.forEach(p => bounds.extend(p));
    map.fitBounds(bounds, 45);

    for (const [name, location, label] of [
      ["Jibowu", path[0], "J"],
      ["Mile 2", path[path.length - 1], "M"]
    ]) {
      new google.maps.Marker({ map, position: location, label, title: name });
    }

    const img = document.createElement("img");
    img.src = busImage;
    img.alt = "Animated yellow Lagos danfo (illustration)";
    img.className = "site-map-google-bus";
    img.style.width = "88px";

    let update;
    try {
      const { AdvancedMarkerElement } = await google.maps.importLibrary("marker");
      const danfo = new AdvancedMarkerElement({ map, position: path[0], content: img });
      update = position => { danfo.position = position; };
    } catch (error) {
      const danfo = new google.maps.Marker({
        map, position: path[0], title: "Animated SafeRide danfo",
        icon: {
          url: busImage,
          scaledSize: new google.maps.Size(88, 63),
          anchor: new google.maps.Point(44, 44)
        }
      });
      update = position => danfo.setPosition(position);
    }
    hideLoading();
    provider.textContent = "Google Maps";
    showMessage("Road route ready · Animated danfo follows Google's road path");
    prepareAnimation(path, update);
    return polyline;
  }

  async function showOpenFreeMap() {
    // OSM Foundation volunteer raster tiles can reject production requests (403).
    // OpenFreeMap explicitly permits public/commercial keyless vector-map usage.
    if (!window.maplibregl) {
      await loadScript("https://unpkg.com/maplibre-gl@5.6.0/dist/maplibre-gl.js");
    }
    element.replaceChildren();
    const map = new maplibregl.Map({
      container: element,
      style: "https://tiles.openfreemap.org/styles/liberty",
      center: [3.34, 6.49],
      zoom: 11,
      attributionControl: true,
      dragRotate: false,
      pitchWithRotate: false
    });
    map.scrollZoom.disable();
    map.touchZoomRotate.disableRotation();
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-left");

    // A basemap is only marked ready after the vector style has actually loaded.
    // A broken style must give visitors useful directions, not blank or 403 tiles.
    try {
      await new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
          reject(new Error("Map tiles timed out."));
        }, 15000);
        const onError = event => {
          if (!map.isStyleLoaded()) {
            clearTimeout(timeout);
            map.off("error", onError);
            reject(event.error || new Error("Map provider is unavailable."));
          }
        };
        map.on("error", onError);
        map.once("load", () => {
          clearTimeout(timeout);
          map.off("error", onError);
          resolve();
        });
      });
    } catch (error) {
      map.remove();
      throw error;
    }

    const marker = (label, location, isEnd) => {
      const wrapper = document.createElement("span");
      wrapper.className = "site-map-stop" + (isEnd ? " site-map-stop--end" : "");
      wrapper.textContent = label;
      wrapper.setAttribute("aria-hidden", "true");
      return new maplibregl.Marker({ element: wrapper })
        .setLngLat([location.lng, location.lat])
        .addTo(map);
    };
    marker("J", JIBOWU, false);
    marker("M", MILE_TWO, true);
    const area = [
      [Math.min(JIBOWU.lng, MILE_TWO.lng), Math.min(JIBOWU.lat, MILE_TWO.lat)],
      [Math.max(JIBOWU.lng, MILE_TWO.lng), Math.max(JIBOWU.lat, MILE_TWO.lat)]
    ];
    map.fitBounds(area, { padding: 35, maxZoom: 12, duration: 0 });
    hideLoading();
    provider.textContent = "OpenFreeMap";
    showMessage("Street map loaded · Finding driving route…");

    // OSRM is only a best-effort demo routing source; never substitute a
    // straight imaginary line if actual road geometry is unavailable.
    const abort = new AbortController();
    const timer = setTimeout(() => abort.abort(), 11000);
    try {
      const api = "https://router.project-osrm.org/route/v1/driving/" +
        JIBOWU.lng + "," + JIBOWU.lat + ";" + MILE_TWO.lng + "," + MILE_TWO.lat +
        "?overview=full&geometries=geojson";
      const response = await fetch(api, { signal: abort.signal });
      if (!response.ok) throw new Error("Demo routing service unavailable.");
      const body = await response.json();
      const road = body.routes?.[0];
      if (!road || !Array.isArray(road.geometry?.coordinates)) {
        throw new Error("No road geometry in routing response.");
      }
      const path = road.geometry.coordinates.map(([lng, lat]) => ({ lat, lng }));
      if (!validRoadPath(path)) throw new Error("Invalid Lagos road geometry.");
      const coords = path.map(p => [p.lng, p.lat]);
      map.addSource("saferide-road", {
        type: "geojson",
        data: {
          type: "Feature",
          properties: {},
          geometry: { type: "LineString", coordinates: coords }
        }
      });
      map.addLayer({
        id: "saferide-road-outline", type: "line", source: "saferide-road",
        paint: { "line-color": "#d6f86c", "line-width": 10, "line-opacity": 0.95 },
        layout: { "line-join": "round", "line-cap": "round" }
      });
      map.addLayer({
        id: "saferide-road-path", type: "line", source: "saferide-road",
        paint: { "line-color": "#067759", "line-width": 6 },
        layout: { "line-join": "round", "line-cap": "round" }
      });
      const bounds = coords.reduce((box, point) => box.extend(point),
        new maplibregl.LngLatBounds(coords[0], coords[0]));
      map.fitBounds(bounds, { padding: 35, maxZoom: 13, duration: 0 });

      const bus = document.createElement("img");
      bus.src = busImage;
      bus.alt = "";
      bus.className = "site-map-google-bus";
      bus.style.width = "88px";
      bus.style.filter = "drop-shadow(0 8px 7px #15241e63)";
      const movingMarker = new maplibregl.Marker({ element: bus, anchor: "center" })
        .setLngLat(coords[0]).addTo(map);
      showMessage("Approx. " + (road.distance / 1000).toFixed(1) +
        " km by road · Illustrated danfo follows the mapped route");
      prepareAnimation(path, position => movingMarker.setLngLat([position.lng, position.lat]));
    } catch (error) {
      console.warn("SafeRide demo road route unavailable:", error.message);
      showMessage("Street map loaded; road route is temporarily unavailable. Use Google Maps directions.");
    } finally {
      clearTimeout(timer);
      setTimeout(() => map.resize(), 120);
    }
  }

  async function init() {
    if (googleKey) {
      try {
        await showGoogle();
        return;
      } catch (error) {
        console.warn("SafeRide Google Maps route unavailable; switching to OpenFreeMap.", error.message);
      }
    }
    try {
      await showOpenFreeMap();
    } catch (error) {
      hideLoading();
      provider.textContent = "Google Maps directions";
      element.replaceChildren();
      const panel = document.createElement("div");
      panel.className = "site-map-loading";
      const link = document.createElement("a");
      link.href = ROUTE_LINK;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      link.textContent = "Open the real Jibowu → Mile 2 road route in Google Maps ↗";
      panel.append(link);
      element.append(panel);
      showMessage("Interactive map couldn't load. Google Maps directions are still available.");
    }
  }

  init();
})();
