/* Geometry and screen-space animation, shared by the two map adapters. */
((scope) => {
  "use strict";
  const radians = Math.PI / 180;
  const clamp = (n, low, high) => Math.max(low, Math.min(high, n));
  function meters(a, b) {
    const y = Math.sin((b.lat - a.lat) * radians / 2);
    const x = Math.sin((b.lng - a.lng) * radians / 2);
    return 12742000 * Math.asin(Math.min(1, Math.sqrt(y * y +
      Math.cos(a.lat * radians) * Math.cos(b.lat * radians) * x * x)));
  }
  function createRoute(points) {
    const path = [points[0]], cumulative = [0];
    for (const p of points.slice(1)) {
      const span = meters(path[path.length - 1], p);
      if (span > .01) { path.push(p); cumulative.push(cumulative.at(-1) + span); }
    }
    const length = cumulative.at(-1);
    if (!(length > 0)) throw new Error("Route has no length");
    const at = distance => {
      const goal = clamp(distance, 0, length);
      let low = 1, high = path.length - 1;
      while (low < high) {
        const mid = (low + high) >> 1;
        if (cumulative[mid] < goal) low = mid + 1;
        else high = mid;
      }
      const a = path[low - 1], b = path[low];
      const t = (goal - cumulative[low - 1]) / (cumulative[low] - cumulative[low - 1]);
      return {lat: a.lat + (b.lat - a.lat) * t, lng: a.lng + (b.lng - a.lng) * t};
    };
    return {at, length};
  }
  const angleDelta = (from, to) => ((to - from + 540) % 360 + 360) % 360 - 180;
  function screenTangent(route, distance, project) {
    // First estimate local pixels/metre, then average a small visible road span.
    const scale = span => {
      const lo = Math.max(0, distance - span), hi = Math.min(route.length, distance + span);
      const a = project(route.at(lo)), b = project(route.at(hi));
      if (!a || !b || hi <= lo) return null;
      const dx = b.x - a.x, dy = b.y - a.y;
      // Arc length, rather than the turn's shorter chord, keeps corner speed steady.
      let pixels = 0, previous = a;
      for (let i = 1; i <= 4; i++) {
        const p = i === 4 ? b : project(route.at(lo + (hi - lo) * i / 4));
        pixels += Math.hypot(p.x - previous.x, p.y - previous.y); previous = p;
      }
      const ppm = pixels / (hi - lo);
      return ppm > 1e-8 ? {angle: Math.atan2(dy, dx) / radians, ppm} : null;
    };
    const local = scale(10);
    return local ? (scale(clamp(2 / local.ppm, 2, route.length / 40)) || local) : null;
  }
  function createAnimator({path, marker, project, onState, speed = 30}) {
    const route = createRoute(path);
    let distance = 0, heading = null, running = false, destroyed = false;
    let raf = null, lastTime = null;
    function render(dt = 0) {
      const tangent = screenTangent(route, distance, project);
      if (tangent) {
        heading = heading === null || dt === 0 ? tangent.angle :
          heading + angleDelta(heading, tangent.angle) * (1 - Math.exp(-dt / .055));
      }
      marker.update(route.at(distance), heading || 0);
    }
    function frame(now) {
      if (!running || destroyed) return;
      const dt = document.hidden || lastTime === null ? 0 : clamp((now - lastTime) / 1000, 0, .064);
      lastTime = document.hidden ? null : now;
      const tangent = screenTangent(route, distance, project);
      if (dt && tangent) distance = Math.min(route.length, distance + speed * dt / tangent.ppm);
      render(dt);
      if (distance >= route.length) { pause(); onState("arrived"); }
      else raf = requestAnimationFrame(frame);
    }
    function pause() {
      running = false; lastTime = null;
      if (raf !== null) cancelAnimationFrame(raf);
      raf = null;
      if (!destroyed) onState(distance >= route.length ? "arrived" : "paused");
    }
    function play() {
      if (destroyed || running) return;
      if (distance >= route.length) { distance = 0; heading = null; render(); }
      running = true; lastTime = null; onState("playing");
      raf = requestAnimationFrame(frame);
    }
    const visibility = () => { lastTime = null; };
    document.addEventListener("visibilitychange", visibility);
    render();
    return {
      play, pause, refresh: () => { if (!destroyed) render(); },
      destroy() {
        destroyed = true; pause(); marker.remove();
        document.removeEventListener("visibilitychange", visibility);
      }
    };
  }
  const api = {meters, createRoute, angleDelta, screenTangent, createAnimator};
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else scope.SafeRideMotion = api;
})(typeof window !== "undefined" ? window : globalThis);
