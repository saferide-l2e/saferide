"use strict";
/* Internal review only: these forms do not submit or mutate bookings. */
document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll("main form").forEach(function (form) {
    form.addEventListener("submit", function (event) {
      event.preventDefault();
      let notice = document.getElementById("preview-action-notice");
      if (!notice) {
        notice = document.createElement("p");
        notice.id = "preview-action-notice";
        notice.setAttribute("role", "status");
        notice.className = "preview-action-notice";
        const main = document.querySelector("main");
        if (main) main.prepend(notice);
      }
      notice.textContent = "This is a page review. Account, booking and check-in actions are not connected yet.";
      notice.scrollIntoView({ behavior: "instant", block: "start" });
    });
  });
});
