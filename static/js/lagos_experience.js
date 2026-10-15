/* User-controlled theme and linked search-stop selectors. No tracking or network calls. */
(() => {
  "use strict";
  const key = "saferide-color-theme";
  const root = document.documentElement;
  const toggle = document.querySelector("[data-theme-toggle]");
  let theme = "light";
  try { theme = localStorage.getItem(key) === "dark" ? "dark" : "light"; }
  catch (error) { theme = "light"; }
  const apply = mode => {
    root.dataset.theme = mode;
    if (toggle) {
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