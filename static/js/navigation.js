"use strict";
(function () {
  document.documentElement.classList.add("has-js");
  const header = document.querySelector("[data-site-header]");
  const toggle = document.querySelector("[data-nav-toggle]");
  const nav = document.querySelector("[data-primary-nav]");
  if (!header || !toggle || !nav) return;

  function update(open) {
    header.classList.toggle("nav-open", open);
    toggle.setAttribute("aria-expanded", String(open));
    toggle.setAttribute("aria-label", open ? "Close navigation" : "Open navigation");
  }

  toggle.addEventListener("click", function () {
    update(toggle.getAttribute("aria-expanded") !== "true");
  });
  nav.querySelectorAll("[data-nav-link]").forEach(function (link) {
    link.addEventListener("click", function () { update(false); });
  });
  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && header.classList.contains("nav-open")) {
      update(false);
      toggle.focus();
    }
  });
  document.addEventListener("click", function (event) {
    if (header.classList.contains("nav-open") && !header.contains(event.target)) update(false);
  });
  const wide = window.matchMedia("(min-width: 800px)");
  if (wide.addEventListener) wide.addEventListener("change", function (event) {
    if (event.matches) update(false);
  });
})();
