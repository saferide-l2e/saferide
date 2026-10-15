# SafeRide — instructions for Codex and coding agents

## Read first
- Full context, URLs, browser workflow and priorities: [docs/CODEX_UI_HANDOFF.md](docs/CODEX_UI_HANDOFF.md)
- Map implementation: [docs/LAGOS_MAP_HERO.md](docs/LAGOS_MAP_HERO.md)
- Render deployment: [docs/RENDER_SHOWCASE_DEPLOY.md](docs/RENDER_SHOWCASE_DEPLOY.md)

## Working rules
1. This checkout uses the **codex/ui-visual-polish-handoff** working branch, based on the currently deployed Render branch. Keep `main` and `deploy/render-demo-2026-10-16` unchanged until the team reviews a PR.
2. **Inspect the actual UI using a graphical browser** (Codex browser or Playwright/Chromium) before and after changes. Live reference: https://saferide-friday-web.onrender.com/. Use local/staging browser preview to see changes not yet deployed.
3. Fixed stack: Django 5.2 LTS + Django templates + HTML/CSS/vanilla JS + PostgreSQL. Don't swap to React/Next.js or rewrite backend business logic for a UI task.
4. Keep responsive desktop/tablet/mobile layouts, keyboard accessibility, reduced-motion and real page navigation. Avoid decorative, fictional routes presented as real. A moving danfo on a Google/OSRM road line is **illustrative, not live tracking**.
5. The Google Maps key appeared in a chat; **never copy that key to code, docs, commits, or screenshots**. Ask operator to rotate/restrict it and set `GOOGLE_MAPS_BROWSER_KEY` as a Render environment variable.
6. Do not expose credentials, use the live PostgreSQL database for tests, overwrite original teammate Figma files, or merge into `main` automatically.
7. Test with `ruff check .`, `python manage.py check`, `pytest -q` with local PostgreSQL and real-browser screenshots at 320/390/768/1024/1440px. Report unverified tests honestly.
8. Work iteratively: baseline screenshots → priority bugs → local browser inspection → QA → PR to `deploy/render-demo-2026-10-16`.
