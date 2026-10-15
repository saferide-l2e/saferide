"use strict";
/* The backend is the only source of truth for expiry, inventory and check-in.
   This script displays time and polls the optional status endpoint; it never
   changes booking status or sends a reservation request. */
(function () {
  const root = document.querySelector("[data-hold-timer]");
  if (!root) return;
  const readout = root.querySelector("[data-time-display]");
  const message = root.querySelector("[data-hold-message]");
  const progress = root.querySelector("[data-hold-progress]");
  const code = document.querySelector("[data-boarding-code]");
  const offline = document.querySelector("[data-offline-warning]");
  const cancel = document.querySelector("[data-one-time-submit]");
  let status = root.dataset.bookingStatus;
  const initialServerTime = Date.parse(root.dataset.serverNow || "");
  let expiresAt = Date.parse(root.dataset.expiresAt || "");
  let serverBaseline = initialServerTime;
  let monotonicBaseline = performance.now();
  let lastNotice = "";
  let pending = false;

  if (cancel) {
    cancel.addEventListener("submit", function (event) {
      const button = cancel.querySelector('button[type="submit"]');
      if (cancel.dataset.submitting === "true") {
        event.preventDefault();
        return;
      }
      cancel.dataset.submitting = "true";
      if (button) button.disabled = true;
    });
    window.addEventListener("pageshow", function () {
      cancel.dataset.submitting = "false";
      const button = cancel.querySelector('button[type="submit"]');
      if (button) button.disabled = false;
    });
  }

  function tell(text) {
    if (message && lastNotice !== text) {
      message.textContent = text;
      lastNotice = text;
    }
  }

  function display() {
    if (!readout || status !== "HELD") return;
    if (!Number.isFinite(serverBaseline) || !Number.isFinite(expiresAt)) {
      readout.textContent = "--:--";
      tell("Refresh to retrieve the current server expiry time.");
      return;
    }
    const serverNow = serverBaseline + (performance.now() - monotonicBaseline);
    const left = Math.max(0, Math.ceil((expiresAt - serverNow) / 1000));
    const mins = String(Math.floor(left / 60)).padStart(2, "0");
    const secs = String(left % 60).padStart(2, "0");
    readout.textContent = mins + ":" + secs;
    if (progress) progress.style.width = Math.min(100, (left / 600) * 100) + "%";
    if (left === 0) {
      tell("The timer reached zero. Refresh to confirm the server's current booking status.");
      if (code) code.hidden = true;
    } else if (left <= 60) {
      tell("Less than one minute remains. Check in with your assigned driver now.");
    } else if (left <= 180) {
      tell("Less than three minutes remain to check in.");
    } else {
      tell("Your booking expires at the time shown above. Only the server can confirm your seat.");
    }
  }

  const rawUrl = root.dataset.statusUrl;
  let statusUrl;
  if (rawUrl) {
    try {
      const parsed = new URL(rawUrl, window.location.href);
      if (parsed.origin === window.location.origin) statusUrl = parsed.href;
    } catch (_error) {
      statusUrl = undefined;
    }
  }
  async function poll() {
    if (!statusUrl || pending || !navigator.onLine || document.hidden) return;
    pending = true;
    try {
      const response = await fetch(statusUrl, {
        method: "GET", credentials: "same-origin", cache: "no-store",
        headers: { Accept: "application/json" },
      });
      if (!response.ok) throw new Error("Status unavailable");
      const data = await response.json();
      if (typeof data.status !== "string") throw new Error("Invalid booking status");
      status = data.status;
      const current = Date.parse(data.server_now || "");
      const expiry = Date.parse(data.expires_at || "");
      if (Number.isFinite(current)) {
        serverBaseline = current;
        monotonicBaseline = performance.now();
      }
      if (Number.isFinite(expiry)) expiresAt = expiry;
      if (status !== "HELD") {
        if (code) code.hidden = true;
        if (progress) progress.style.width = "0%";
        if (readout) readout.textContent = "--:--";
        tell("Your booking status is now " + status.toLowerCase().replaceAll("_", " ") + ". Refresh the page for the latest actions.");
      } else display();
    } catch (_error) {
      tell("We couldn't refresh the booking status. Check your connection, then refresh the page.");
    } finally {
      pending = false;
    }
  }

  function connectionChanged() {
    if (offline) offline.hidden = navigator.onLine;
    if (navigator.onLine) void poll();
  }
  window.addEventListener("online", connectionChanged);
  window.addEventListener("offline", connectionChanged);
  connectionChanged();
  display();
  window.setInterval(display, 1000);
  if (statusUrl) window.setInterval(function () { void poll(); }, 15000);
})();
