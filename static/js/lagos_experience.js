/* User-controlled theme and linked search-stop selectors. No tracking or network calls. */
(() => {
  "use strict";
  const key = "saferide-color-theme";
  const root = document.documentElement;
  const toggle = document.querySelector("[data-theme-toggle]");
  let theme = root.dataset.theme || "light";
  const apply = mode => {
    root.dataset.theme = mode;
    if (toggle) {
      toggle.hidden = false;
      toggle.textContent = mode === "dark" ? "☀" : "☾";
      toggle.setAttribute("aria-label", mode === "dark" ? "Switch to light mode" : "Switch to dark mode");
      toggle.setAttribute("aria-pressed", String(mode === "dark"));
    }
  };
  apply(theme);
  toggle?.addEventListener("click", () => {
    theme = root.dataset.theme === "dark" ? "light" : "dark";
    apply(theme);
    try { localStorage.setItem(key, theme); } catch (error) { /* Session theme only. */ }
  });
  const systemTheme = matchMedia("(prefers-color-scheme: dark)");
  systemTheme.addEventListener("change", event => {
    let saved;
    try { saved = localStorage.getItem(key); } catch (_) { /* Use system preference. */ }
    if (!saved) apply(event.matches ? "dark" : "light");
  });
  window.addEventListener("storage", event => {
    if (event.key === key) apply(event.newValue === "dark" ? "dark" : event.newValue === "light" ? "light" : systemTheme.matches ? "dark" : "light");
  });
  const from = document.querySelector("[data-map-origin]");
  const to = document.querySelector("[data-map-destination]");
  const searchFrom = document.querySelector("#site-from");
  const searchTo = document.querySelector("#site-to");
  if (from && to && searchFrom && searchTo) {
    from.addEventListener("change", () => { searchFrom.value = from.value; });
    to.addEventListener("change", () => { searchTo.value = to.value; });
    const form = searchFrom.closest("form");
    form?.addEventListener("submit", () => {
      searchFrom.value = searchFrom.value.trim();
      searchTo.value = searchTo.value.trim();
    });
  }
})();
