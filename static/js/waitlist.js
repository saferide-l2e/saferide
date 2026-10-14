"use strict";
/* Queue order and offer allocation are exclusively decided by the server. */
(function () {
  const oneTimeForms = document.querySelectorAll("[data-one-time-submit]");
  oneTimeForms.forEach(function (form) {
    form.addEventListener("submit", function (event) {
      if (form.dataset.submitting === "true") {
        event.preventDefault();
        return;
      }
      form.dataset.submitting = "true";
      const button = form.querySelector('button[type="submit"]');
      if (button) button.disabled = true;
    });
  });
  window.addEventListener("pageshow", function () {
    oneTimeForms.forEach(function (form) {
      form.dataset.submitting = "false";
      const button = form.querySelector('button[type="submit"]');
      if (button) button.disabled = false;
    });
  });

  const offer = document.querySelector("[data-offer-clock]");
  const queue = document.querySelector("[data-waitlist-status]");
  const offlineWarnings = document.querySelectorAll("[data-queue-offline]");
  const root = offer || queue;
  if (!root) return;

  const originalServer = Date.parse(offer ? offer.dataset.serverNow || "" : "");
  let baseServer = originalServer;
  let monotonicStart = performance.now();
  let expiresAt = Date.parse(offer ? offer.dataset.offerExpires || "" : "");
  let status = offer ? offer.dataset.offerStatus : "WAITING";
  let announced = "";
  const readout = offer && offer.querySelector("[data-offer-readout]");
  const message = offer ? offer.querySelector("[data-offer-message]") : queue.querySelector("[data-queue-message]");
  const position = queue && queue.querySelector("[data-queue-position]");
  const progress = offer && offer.querySelector("[data-offer-progress]");

  function tell(text) {
    if (message && announced !== text) {
      message.textContent = text;
      announced = text;
    }
  }

  function updateTime() {
    if (!offer || status !== "OFFERED" || !readout) return;
    if (!Number.isFinite(baseServer) || !Number.isFinite(expiresAt)) {
      readout.textContent = "--:--";
      tell("Refresh to obtain the offer deadline from the server.");
      return;
    }
    const remaining = Math.max(0, Math.ceil((expiresAt - baseServer - (performance.now() - monotonicStart)) / 1000));
    readout.textContent = String(Math.floor(remaining / 60)).padStart(2, "0") + ":" + String(remaining % 60).padStart(2, "0");
    if (progress) progress.style.width = Math.min(100, remaining / 120 * 100) + "%";
    if (remaining === 0) tell("The displayed offer time has run out. Refresh to confirm your actual status before acting.");
    else if (remaining <= 30) tell("Less than thirty seconds remain. Accept or decline before the deadline.");
    else if (remaining <= 60) tell("Less than a minute remains for this offer.");
    else tell("Your offer is held for two minutes. Only the server can confirm acceptance.");
  }

  let endpoint;
  try {
    if (root.dataset.statusUrl) {
      const parsed = new URL(root.dataset.statusUrl, window.location.href);
      if (parsed.origin === window.location.origin) endpoint = parsed.href;
    }
  } catch (_error) {
    endpoint = undefined;
  }
  let pending = false;
  async function poll() {
    if (!endpoint || pending || !navigator.onLine || document.hidden) return;
    pending = true;
    try {
      const response = await fetch(endpoint, {
        method: "GET", credentials: "same-origin", cache: "no-store",
        headers: { Accept: "application/json" },
      });
      if (!response.ok) throw new Error("Queue status unavailable");
      const data = await response.json();
      if (typeof data.status !== "string") throw new Error("Invalid queue response");
      status = data.status;
      if (queue && position && Number.isInteger(data.queue_position) && data.queue_position > 0) {
        position.textContent = "#" + data.queue_position;
      }
      if (offer) {
        const actualNow = Date.parse(data.server_now || "");
        const actualExpiry = Date.parse(data.offer_expires_at || "");
        if (Number.isFinite(actualNow)) {
          baseServer = actualNow;
          monotonicStart = performance.now();
        }
        if (Number.isFinite(actualExpiry)) expiresAt = actualExpiry;
        if (status !== "OFFERED") {
          if (readout) readout.textContent = "--:--";
          tell("The offer is now " + status.toLowerCase().replaceAll("_", " ") + ". Refresh for the next step.");
        }
      } else if (status !== "WAITING") {
        tell("Your queue status has changed to " + status.toLowerCase().replaceAll("_", " ") + ". Refresh to see the next step.");
      } else {
        tell("Your position was updated from SafeRide.");
      }
    } catch (_error) {
      tell("Couldn't refresh queue status. Reconnect and refresh to confirm.");
    } finally {
      pending = false;
    }
  }
  function checkConnection() {
    offlineWarnings.forEach(function (e) { e.hidden = navigator.onLine; });
    if (navigator.onLine) void poll();
  }
  window.addEventListener("online", checkConnection);
  window.addEventListener("offline", checkConnection);
  checkConnection();
  updateTime();
  if (offer) window.setInterval(updateTime, 1000);
  if (endpoint) window.setInterval(function () { void poll(); }, 15000);
})();
