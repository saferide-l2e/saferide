/* Route-first Lagos map. Real road geometry; no fictional vehicle animation. */
(() => {
  "use strict";
  const root = document.querySelector("[data-route-hero]");
  if (!root) return;

  const mapNode = root.querySelector("#hero-route-map");
  const origin = root.querySelector("[data-map-origin]");
  const destination = root.querySelector("[data-map-destination]");
  const distanceLabel = root.querySelector("[data-map-distance]");
  const directions = root.querySelector("[data-map-directions]");
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
  let googleBoot = null;
  let googleUnavailable = false;
  let current = null;
  let sequence = 0;

  const valid = points => Array.isArray(points) && points.length > 1 &&
    points.length < 15000 && points.every(p => Number.isFinite(p.lat) &&
      Number.isFinite(p.lng) && p.lat > 5 && p.lat < 7 && p.lng > 2 && p.lng < 5);
  const coordinate = p => [p.lng, p.lat];
  const location = p => ({lng: p[0], lat: p[1]});
  const isCurrent = session => current === session && !session.abort.signal.aborted;
  const label = name => encodeURIComponent(name + ", Lagos, Nigeria");

  function syncSelections() {
    root.querySelector("[data-origin-label]").textContent = origin.value;
    root.querySelector("[data-destination-label]").textContent = destination.value;
    directions.href = "https://www.google.com/maps/dir/?api=1&origin=" +
      label(origin.value) + "&destination=" + label(destination.value) +
      "&travelmode=driving";
    mapNode.setAttribute("aria-label", "Map of the road between " + origin.value + " and " + destination.value);
    const searchOrigin = document.getElementById("site-from");
    const searchDestination = document.getElementById("site-to");
    if (searchOrigin) searchOrigin.value = origin.value;
    if (searchDestination) searchDestination.value = destination.value;
  }

  function loadScript(name, url) {
    if (loaders.has(name)) return loaders.get(name);
    const promise = new Promise((resolve, reject) => {
      const element = document.createElement("script");
      element.src = url;
      element.async = true;
      const timeout = setTimeout(() => {
        element.remove(); reject(new Error("Road map loading timed out"));
      }, 14000);
      element.onload = () => { clearTimeout(timeout); resolve(); };
      element.onerror = () => { clearTimeout(timeout); reject(new Error("Unable to load road map")); };
      document.head.append(element);
    }).catch(error => {loaders.delete(name); throw error;});
    loaders.set(name, promise);
    return promise;
  }

  function loadVectorStyle() {
    if (loaders.has("vector-style")) return loaders.get("vector-style");
    const promise = new Promise((resolve, reject) => {
      const link = document.createElement("link");
      link.rel = "stylesheet";
      link.href = "https://unpkg.com/maplibre-gl@5.6.0/dist/maplibre-gl.css";
      const timeout = setTimeout(() => {
        link.remove(); reject(new Error("Map styling timed out"));
      }, 14000);
      link.onload = () => { clearTimeout(timeout); resolve(); };
      link.onerror = () => { clearTimeout(timeout); reject(new Error("Map styling unavailable")); };
      document.head.append(link);
    }).catch(error => { loaders.delete("vector-style"); throw error; });
    loaders.set("vector-style", promise);
    return promise;
  }

  function showLoading(text) {
    const panel = document.createElement("div");
    panel.className = "site-map-loading";
    const title = document.createElement("strong");
    title.textContent = text;
    panel.append(title);
    mapNode.replaceChildren(panel);
    distanceLabel.textContent = "Finding the best available road route…";
  }

  function markReady(session, meters) {
    if (!isCurrent(session)) return;
    root.dataset.mapState = "ready";
    mapNode.setAttribute("aria-busy", "false");
    distanceLabel.textContent = Number.isFinite(meters) && meters > 0
      ? "Approx. " + (meters / 1000).toFixed(1) + " km by road"
      : "Road route ready";
  }

  function stopPin(last, name) {
    const marker = document.createElement("span");
    marker.className = "site-map-stop" + (last ? " site-map-stop--end" : "");
    marker.textContent = last ? "B" : "A";
    marker.title = name;
    marker.setAttribute("aria-label", name);
    return marker;
  }

  function noRoute(session, text) {
    if (!isCurrent(session)) return;
    session.cleanup?.(); session.cleanup = null;
    root.dataset.mapState = "unavailable";
    mapNode.setAttribute("aria-busy", "false");
    const panel = document.createElement("div");
    panel.className = "site-map-loading site-map-fallback";
    const heading = document.createElement("strong");
    heading.textContent = "You can still plan this journey";
    const link = document.createElement("a");
    link.href = directions.href;
    link.rel = "noopener noreferrer"; link.target = "_blank";
    link.textContent = "View directions ↗";
    panel.append(heading, link);
    mapNode.replaceChildren(panel);
    distanceLabel.textContent = text;
  }

  async function vectorMap(session, start, end) {
    await Promise.all([
      loadVectorStyle(),
      window.maplibregl ? Promise.resolve() : loadScript("vector", "https://unpkg.com/maplibre-gl@5.6.0/dist/maplibre-gl.js")
    ]);
    if (!isCurrent(session)) return;
    mapNode.replaceChildren();
    const map = new maplibregl.Map({
      container: mapNode, style: "https://tiles.openfreemap.org/styles/liberty",
      center: start, zoom: 11, attributionControl: true,
      dragRotate: false, pitchWithRotate: false
    });
    const markers = [];
    let observer;
    session.cleanup = () => {
      observer?.disconnect();
      markers.forEach(marker => marker.remove());
      map.remove();
    };
    map.scrollZoom.disable();
    map.touchZoomRotate.disableRotation();
    map.addControl(new maplibregl.NavigationControl({showCompass: false}), "top-left");

    await new Promise((resolve, reject) => {
      const timeout = setTimeout(() => reject(new Error("Map timeout")), 14000);
      map.once("load", () => {clearTimeout(timeout); resolve();});
      map.on("error", event => {
        if (!map.isStyleLoaded()) {
          clearTimeout(timeout);
          reject(event.error || new Error("Map could not load"));
        }
      });
      session.abort.signal.addEventListener("abort", () => {
        clearTimeout(timeout); reject(new Error("Cancelled"));
      }, {once: true});
    });
    if (!isCurrent(session)) return;

    const fit = coords => {
      const bounds = coords.reduce((box, p) => box.extend(p),
        new maplibregl.LngLatBounds(coords[0], coords[0]));
      map.fitBounds(bounds, {padding: 45, maxZoom: 13, duration: 0});
    };
    fit([start, end]);

    for (const [p, name, last] of [[start, origin.value, false], [end, destination.value, true]]) {
      markers.push(new maplibregl.Marker({element: stopPin(last, name)})
        .setLngLat(p).addTo(map));
    }

    const controller = new AbortController();
    const onAbort = () => controller.abort();
    session.abort.signal.addEventListener("abort", onAbort, {once: true});
    const timer = setTimeout(() => controller.abort(), 11500);
    try {
      const url = "https://router.project-osrm.org/route/v1/driving/" +
        start.join(",") + ";" + end.join(",") +
        "?overview=full&geometries=geojson";
      const response = await fetch(url, {signal: controller.signal});
      if (!response.ok) throw new Error("Road service unavailable");
      const road = (await response.json()).routes?.[0];
      const path = road?.geometry?.coordinates?.map(location);
      if (!valid(path)) throw new Error("Route geometry unavailable");
      if (!isCurrent(session)) return;
      const coordinates = path.map(coordinate);
      map.addSource("saferide-route", {type: "geojson", data: {
        type: "Feature", properties: {},
        geometry: {type: "LineString", coordinates}
      }});
      for (const [id, color, width] of [
        ["saferide-route-outline", "#dbff67", 9],
        ["saferide-route-line", "#0b7458", 5]
      ]) {
        map.addLayer({id, type: "line", source: "saferide-route",
          layout: {"line-join": "round", "line-cap": "round"},
          paint: {"line-color": color, "line-width": width}});
      }
      fit(coordinates);
      observer = new ResizeObserver(() => map.resize());
      observer.observe(mapNode);
      markReady(session, road.distance);
    } catch (error) {
      if (isCurrent(session)) {
        root.dataset.mapState = "stops-only";
        mapNode.setAttribute("aria-busy", "false");
        distanceLabel.textContent = "Road route unavailable. View directions to continue.";
        observer = new ResizeObserver(() => map.resize());
        observer.observe(mapNode);
      }
    } finally {
      clearTimeout(timer);
      session.abort.signal.removeEventListener("abort", onAbort);
    }
  }

  function wait(promise, session, milliseconds = 16000) {
    return Promise.race([
      promise,
      new Promise((_, reject) => {
        const timer = setTimeout(() => reject(new Error("Map request timed out")), milliseconds);
        session.abort.signal.addEventListener("abort", () => {
          clearTimeout(timer); reject(new Error("Cancelled"));
        }, {once: true});
        promise.finally(() => clearTimeout(timer)).catch(() => {});
      })
    ]);
  }

  async function googleMap(session, start, end) {
    if (!window.google?.maps?.importLibrary) {
      if (!googleBoot) {
        googleBoot = new Promise((resolve, reject) => {
          window.safeRideMapsReady = resolve;
          loadScript("google", "https://maps.googleapis.com/maps/api/js?key=" +
            encodeURIComponent(root.dataset.googleKey) +
            "&v=weekly&loading=async&callback=safeRideMapsReady").catch(reject);
        });
      }
      await wait(googleBoot, session);
    }
    const [{Map}, {Route}] = await wait(Promise.all([
      google.maps.importLibrary("maps"), google.maps.importLibrary("routes")
    ]), session);
    const response = await wait(Route.computeRoutes({
      origin: location(start), destination: location(end),
      travelMode: "DRIVING", fields: ["path", "distanceMeters"]
    }), session);
    if (!isCurrent(session)) return;
    const road = response.routes?.[0];
    const path = road?.path?.map(p => ({
      lat: typeof p.lat === "function" ? p.lat() : p.lat,
      lng: typeof p.lng === "function" ? p.lng() : p.lng
    }));
    if (!valid(path)) throw new Error("No suitable road geometry");
    mapNode.replaceChildren();
    const map = new Map(mapNode, {
      center: path[0], zoom: 11, tilt: 0, gestureHandling: "cooperative",
      mapTypeControl: false, streetViewControl: false, fullscreenControl: false
    });
    const line = new google.maps.Polyline({
      map, path, strokeColor: "#087657", strokeOpacity: .96, strokeWeight: 6
    });
    const markers = [
      new google.maps.Marker({map, position: path[0], label: "A", title: origin.value}),
      new google.maps.Marker({map, position: path.at(-1), label: "B", title: destination.value})
    ];
    const bounds = new google.maps.LatLngBounds();
    path.forEach(p => bounds.extend(p));
    const fit = () => map.fitBounds(bounds, {top: 45, bottom: 45, left: 40, right: 40});
    fit();
    const observer = new ResizeObserver(fit);
    observer.observe(mapNode);
    session.cleanup = () => {
      observer.disconnect();
      markers.forEach(marker => marker.setMap(null));
      line.setMap(null);
      google.maps.event.clearInstanceListeners(map);
    };
    markReady(session, road.distanceMeters);
  }

  async function showRoute() {
    current?.abort.abort();
    current?.cleanup?.();
    const session = {id: ++sequence, abort: new AbortController(), cleanup: null};
    current = session;
    syncSelections();
    root.dataset.mapState = "loading";
    mapNode.setAttribute("aria-busy", "true");
    showLoading("Finding your route…");
    if (!stops[origin.value] || !stops[destination.value] || origin.value === destination.value) {
      noRoute(session, "Choose two different Lagos stops.");
      return;
    }
    const start = stops[origin.value], end = stops[destination.value];
    if (root.dataset.googleKey && !googleUnavailable) {
      try {await googleMap(session, start, end); return;}
      catch (error) {
        if (!isCurrent(session)) return;
        // Keep subsequent stop changes usable after a provider failure instead
        // of repeating the same SDK/API timeout for every selected journey.
        googleUnavailable = true;
        session.cleanup?.(); session.cleanup = null;
        console.info("Using an alternate route preview.", error.message);
      }
    }
    try {await vectorMap(session, start, end);}
    catch (error) {
      if (isCurrent(session)) noRoute(session, "Map preview unavailable. View directions to continue.");
    }
  }

  let visibilityObserver;
  function selectRoute() {
    visibilityObserver?.disconnect();
    showRoute();
  }
  origin.addEventListener("change", selectRoute);
  destination.addEventListener("change", selectRoute);
  window.addEventListener("pagehide", () => {
    current?.abort.abort();
    current?.cleanup?.();
    current = null;
  });
  window.addEventListener("pageshow", event => {
    if (event.persisted && root.dataset.mapState) selectRoute();
  });
  // The road preview is secondary to the hero and search. Defer provider SDKs
  // and routing requests until it approaches the viewport or a stop is changed.
  if ("IntersectionObserver" in window) {
    visibilityObserver = new IntersectionObserver(entries => {
      if (entries.some(entry => entry.isIntersecting)) selectRoute();
    }, {rootMargin: "200px"});
    visibilityObserver.observe(root);
  } else selectRoute();
})();
