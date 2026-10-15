/* Apply the saved preference before CSS paints. Storage may be unavailable. */
(() => {
  // Hide the collapsible menu before first paint; no-JS navigation stays open.
  document.documentElement.classList.add("has-js");
  let saved;
  try { saved = localStorage.getItem("saferide-color-theme"); } catch (_) { /* Use system preference. */ }
  document.documentElement.dataset.theme = saved === "light" || saved === "dark"
    ? saved : (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
})();
