"use strict";
(function () {
  document.querySelectorAll("[data-boarding-submit]").forEach(function (form) {
    form.addEventListener("submit", function (event) {
      if (form.dataset.submitting === "true") {
        event.preventDefault();
        return;
      }
      form.dataset.submitting = "true";
      const button = form.querySelector('button[type="submit"]');
      if (button) button.disabled = true;
    });
    window.addEventListener("pageshow", function () {
      form.dataset.submitting = "false";
      const button = form.querySelector('button[type="submit"]');
      if (button) button.disabled = false;
    });
  });

  const board = document.querySelector("[data-roster-status-url]");
  if (!board) return;
  const message = document.querySelector("[data-roster-message]");
  const warning = document.querySelector("[data-roster-offline]");
  const boardedCount = board.querySelector("[data-boarded-count]");
  const heldCount = board.querySelector("[data-held-count]");
  let endpoint;
  try {
    const parsed = new URL(board.dataset.rosterStatusUrl || "", window.location.href);
    if (parsed.origin === window.location.origin) endpoint = parsed.href;
  } catch (_error) {
    endpoint = undefined;
  }
  let pending = false;
  async function poll() {
    if (!endpoint || pending || document.hidden || !navigator.onLine) return;
    pending = true;
    try {
      const response = await fetch(endpoint, {
        credentials: "same-origin", cache: "no-store",
        headers: { Accept: "application/json" },
      });
      if (!response.ok) throw new Error("Roster unavailable");
      const data = await response.json();
      if (Number.isInteger(data.boarded_count) && data.boarded_count >= 0 && boardedCount) {
        boardedCount.textContent = String(data.boarded_count);
      }
      if (Number.isInteger(data.held_count) && data.held_count >= 0 && heldCount) {
        heldCount.textContent = String(data.held_count);
      }
      if (message) message.textContent = "Latest counts received. Refresh to see updated passenger rows.";
    } catch (_error) {
      if (message) message.textContent = "Could not refresh boarding counts. Check your connection and reload.";
    } finally {
      pending = false;
    }
  }
  function networkStatus() {
    if (warning) warning.hidden = navigator.onLine;
    if (navigator.onLine) void poll();
  }
  window.addEventListener("online", networkStatus);
  window.addEventListener("offline", networkStatus);
  networkStatus();
  if (endpoint) window.setInterval(function () { void poll(); }, 15000);
})();
