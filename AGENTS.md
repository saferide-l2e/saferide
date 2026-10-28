# SafeRide — instructions for Codex / coding agents
**Updated 28 October 2026.** Read [docs/CODEX_UI_HANDOFF.md](docs/CODEX_UI_HANDOFF.md) and [docs/WORKFLOWS.md](docs/WORKFLOWS.md) **before editing**.

1. Use branch `codex/ui-browser-review-2026-10-28` (based on `main` at `0255ced56595`). The old `codex/ui-visual-polish-handoff` branch and October 15 branch instructions are obsolete.
2. Inspect the actual website **graphically** at https://saferide-friday-web.onrender.com/ first. Use Codex's browser or `python scripts/codex_public_ui_capture.py` with Chromium and inspect the resulting screenshots. Do not claim an inspection if the browser was unavailable.
3. Current UI: cinematic Lagos hero with original generated imagery, search and a separate real-road map preview; not the old all-screen gallery and not necessarily a moving danfo. Inspect code and screenshots rather than old assumptions.
4. Fixed stack: Django 5.2 LTS, templates/HTML/CSS/vanilla JS, PostgreSQL. Preserve service-level 600s holds, 120s offers, server permissions and private reporting.
5. Work on this safe branch; review a PR into `main` when tests/screenshots are complete. Render deploys a different branch `deploy/render-demo-2026-10-16`; never update Render or `main` directly without explicit team review.
6. Browser QA: widths 320/390/768/1024/1440, dark/light, keyboard/200% zoom, reduced-motion, route fallback and public page errors. Use a separate LOCAL PostgreSQL DB for live form/E2E testing; the browser capture is deliberately GET-only on production.
7. Never expose credentials or the previously pasted Google Maps key; rotate/restrict the browser key in Google Cloud. Do not overwrite the original teammate Figma file.
8. Keep it professional, responsive and authentic: no fictional live GPS, official KYC, payment, insurance, emergency dispatch or fake successful bookings.
