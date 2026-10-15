(() => {
  'use strict';
  const notice = document.querySelector('[data-review-progress]');
  if (!notice) return;
  const endpoint = new URL(notice.dataset.reviewUrl, location.href);
  if (endpoint.origin !== location.origin) return;
  let timer, stopped = false, attempts = 0;
  const controller = new AbortController();
  function schedule() {
    if (!stopped && !document.hidden) timer = setTimeout(check, 500);
  }
  async function check() {
    if (stopped || document.hidden) return;
    if (++attempts > 60) {
      stopped = true;
      notice.textContent = 'Approval is taking longer than expected. Refresh this page to check your status or contact support.';
      return;
    }
    try {
      const response = await fetch(endpoint, {credentials: 'same-origin', cache: 'no-store', signal: controller.signal});
      if (response.redirected || response.status === 401 || response.status === 403) {
        stopped = true;
        notice.textContent = 'Please refresh this page and sign in again to check your status.';
        return;
      }
      if (response.ok) {
        const status = await response.json();
        if (typeof status.version === 'string' && status.version !== notice.dataset.reviewVersion) {
          stopped = true;
          location.reload();
          return;
        }
      }
    } catch (error) {
      if (error.name === 'AbortError') return;
    }
    schedule();
  }
  document.addEventListener('visibilitychange', () => { clearTimeout(timer); schedule(); });
  window.addEventListener('pagehide', () => { stopped = true; clearTimeout(timer); controller.abort(); });
  // A restored back/forward-cache page must show the current server status.
  window.addEventListener('pageshow', event => { if (event.persisted) location.reload(); });
  schedule();
})();
