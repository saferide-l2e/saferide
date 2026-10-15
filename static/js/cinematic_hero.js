/* Optional licensed/pre-rendered footage. No source is requested in poster mode. */
(() => {
  "use strict";
  const hero = document.querySelector("[data-cinematic-hero]");
  // Scope smooth scrolling to explicit section links. Global smooth scrolling
  // also animates browser/keyboard form scrolling and can leave controls moving.
  hero?.querySelectorAll('a[href^="#"]').forEach(link => {
    link.addEventListener("click", event => {
      if (event.button || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      const target = document.getElementById(link.hash.slice(1));
      if (!target) return;
      event.preventDefault();
      history.pushState(null, "", link.hash);
      target.scrollIntoView({behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "instant" : "smooth"});
      target.setAttribute("tabindex", "-1");
      target.focus({preventScroll: true});
    });
  });
  const video = hero?.querySelector("[data-hero-video]");
  if (!video) return;
  const control = hero.querySelector("[data-video-toggle]");
  const reduced = matchMedia("(prefers-reduced-motion: reduce)");
  const mobile = matchMedia("(max-width: 700px)");
  const connection = navigator.connection;
  let visible = false, pausedByUser = false, failed = false, generation = 0;
  const allowed = () => !reduced.matches && !connection?.saveData && !/^(slow-)?2g$/.test(connection?.effectiveType || "");
  const displayControl = () => {
    control.hidden = !allowed() || failed || !video.currentSrc;
    control.textContent = video.paused ? "Play scene" : "Pause scene";
    control.setAttribute("aria-label", control.textContent);
    control.setAttribute("aria-pressed", String(!video.paused));
  };
  const sync = () => {
    if (!allowed() || document.hidden || !visible || pausedByUser || failed) {
      video.pause();
      if (!allowed() && video.querySelector("source")) {
        video.replaceChildren(); video.removeAttribute("src"); video.load();
      }
      if (!allowed() || failed) hero.classList.remove("is-playing");
      displayControl(); return;
    }
    if (!video.querySelector("source")) {
      const prefix = mobile.matches ? "mobile" : "desktop";
      let failures = 0;
      for (const type of ["webm", "mp4"]) {
        const sourceURL = video.dataset[prefix + (type === "webm" ? "Webm" : "Mp4")];
        if (!sourceURL) continue;
        const source = document.createElement("source");
        source.src = sourceURL; source.type = `video/${type}`; video.append(source);
        source.addEventListener("error", () => {
          failures++;
          if (failures === video.querySelectorAll("source").length) { failed = true; sync(); }
        });
      }
      video.load();
    }
    const ticket = ++generation;
    video.play().then(() => {
      // A preference/visibility change may arrive while autoplay is pending.
      if (ticket !== generation || !allowed() || document.hidden || !visible || pausedByUser) { video.pause(); return; }
      hero.classList.add("is-playing"); displayControl();
    }).catch(() => { hero.classList.remove("is-playing"); displayControl(); });
  };
  control.addEventListener("click", () => { pausedByUser = !video.paused; generation++; sync(); });
  video.addEventListener("error", () => { failed = true; sync(); });
  video.addEventListener("pause", displayControl);
  video.addEventListener("playing", displayControl);
  document.addEventListener("visibilitychange", () => { generation++; sync(); });
  reduced.addEventListener("change", () => { generation++; sync(); });
  connection?.addEventListener("change", () => { generation++; sync(); });
  if ("IntersectionObserver" in window) new IntersectionObserver(entries => {
    visible = entries[0].isIntersecting; generation++; sync();
  }, { threshold: 0.15 }).observe(hero);
  else { visible = true; sync(); }
})();
