# SafeRide — Frontend integration handoff (14 Oct 2026)

**Design:** https://www.figma.com/design/ztF1QqN7Npu55gnJwZVrG7
**Integration PR:** https://github.com/saferide-l2e/saferide/pull/63
**Full combined CI:** https://github.com/saferide-l2e/saferide/actions/runs/38635052690 (passed)

The frontend is implemented as Django templates, static CSS and vanilla JS. The main branch still needs reviewed merges, approved Django views, PostgreSQL workflow integration and deployment.

| FE issue | Code PR | Current state | Backend needed |
|---|---|---|---|
| FE-01 #27 | #51 | Responsive homepage and reusable shell, CI passed | auth/search route wiring later |
| FE-02 #28 | #52 | Sign-up/sign-in/CSRF logout templates, CI passed | BE-01 |
| FE-03 #29 | #58 | Simulated verification and public profiles, CI passed | BE-02 |
| FE-04 #30 | #59 | Vehicle form and approval states, CI passed | BE-03 |
| FE-05 #31 | #60 | Driver dashboard and departure transitions, CI passed | BE-03/09 |
| FE-06 #32 | #53 | Search and bus result templates, CI passed | BE-04 |
| FE-07 #33 | #54 | Bus detail/profile and booking intent POST, CI passed | BE-04/05/07 |
| FE-08 #34 | #55 | Server-clock 600s hold display, cancel, CI passed | BE-05/06/14 |
| FE-09 #35 | #56 | FIFO queue and 120s offers, CI passed | BE-07/14 |
| FE-10 #36 | #57 | Driver-only roster/code check-in, CI passed | BE-08/09 |
| FE-11 #37 | #61 | Journey state, arrival and history, CI passed | BE-09 |
| FE-12 #38 | #62 | Ratings, private reports, moderated notices, CI passed | BE-10/11 |
| FE-13 #39 | #64 | A11y/contrast/error announcement audit, CI passed | real browser/device QA |

**Important:** Individual frontend PRs and combined PR #63 have been checked, but they have not been merged into main. A successful template smoke test is NOT evidence of a functioning backend endpoint.

## Integration steps for the team

1. Review and merge FE-01 (#51) first. Retarget subsequent stacked feature PRs to main as applicable; review order matters because FE-07 depends on FE-06 and FE-13 is currently based on this integration branch.
2. Backend owners add Django URL names/views and safe context dictionaries described by each feature's docs/*_HANDOFF.md file.
3. Retest authenticated roles, admin approvals, privacy, one-time codes, capacity locks, duplicate bookings, exactly 600s holds and 120s offers on PostgreSQL, before declaring an end-to-end booking complete.
4. Run Ruff, Django check, pytest, then capture keyboard-only and 360px/768px/1440px / 200%-zoom browser tests. See docs/ACCESSIBILITY_CHECK.md on FE-13 PR #64.
5. Configure a secure Vercel project with DATABASE_URL, DJANGO_SECRET_KEY, ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS, collected static assets and deployment migrations only once deployment credentials and backend readiness are confirmed.

## Deployment status

The Vercel connection can list existing projects but returns **403 forbidden when accessing the selected workspace/team scope**. No SafeRide project or live deployment has been created. User needs to reauthenticate the Vercel connection to the workspace with suitable permissions. Never deploy a misleading fake booking endpoint or claim payment/identity/GPS dispatch capability.

## Design and copy safeguards

Maintain the original teammate's credited Figma asset work. Current code uses SVG illustrations; original photography/map assets are still a separate integration task. Simulated verification, synthetic pilot data and non-live maps should be disclosed where relevant. Do not replace verification with official registry claims, public blacklist, real-time seat success, or emergency responder dispatch.