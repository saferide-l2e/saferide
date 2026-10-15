# Five-second approval policy

The product owner requested automatic approval five seconds after submission,
replacing the previous staff-only onboarding and publication policy. This change
is intentional. It grants application access, not identity or safety clearance.

## Scope

- Submitted account profiles: PENDING → VERIFIED (displayed as Account approved).
- Driver profiles: PENDING → APPROVED for active, approved driver accounts.
- Submitted vehicles: PENDING → APPROVED for active, approved drivers/profiles.
- Community route posts: PENDING → APPROVED for active approved accounts on active routes.

Only pending records are processed. Existing rejections and suspensions are not
reversed. Unsubmitted accounts are not approved. The existing explicit account
resubmission flow can create a new pending request after rejection; suspension
still prevents resubmission. Staff can reject or suspend as before. Role,
object-ownership, CSRF, departure timing, booking inventory and private boarding
code checks remain enforced. Safety incident reports stay private and require
follow-up; they are never automatically marked reviewed/resolved or published.

Public status wording describes automatic account/profile/listing access.
It does not imply official identity, licence, background or mechanical checks.
Community observations are labelled as not independently verified.

## Server implementation

`apps/core/automatic_reviews.py` checks server database timestamps. The fixed
minimum delay is five seconds, using submitted_at for accounts and created_at
for driver profiles, vehicles and route posts. No record is approved early.
The worker scans every 250 ms in bounded transactions and uses PostgreSQL row
locks with skip_locked to avoid duplicate decisions across multiple workers.
Status and the system audit event commit together. Automated audit records have
no staff actor, automatic=true and delay_seconds=5. Account notes state the
approval is automatic and does not perform screening.

`python manage.py process_reviews --watch` runs continuously; omitting --watch
processes currently due work once. Database timestamps survive restarts and tab
closure. Already overdue pending work is picked up on startup. Legacy pending
accounts without submitted_at do not have a valid deadline and need their data
corrected or an explicit new submission; the worker does not invent a timestamp.

Render's existing start command now supervises this worker and Gunicorn in the
same service. If either exits, its sibling is stopped and the service exits so
Render can restart it. Signal shutdown is forwarded to both children. No new
Render service, database, migration or secret is needed.

`SAFERIDE_AUTO_APPROVAL` defaults to true. Setting it to false and restarting
stops future automatic decisions and restores manual-review descriptions.
Disabling it does not undo approvals already committed; staff can manage those
records explicitly. Production startup still runs the established migrations
and optional existing seed command; neither is replaced.

## Browser behavior

Pending account, vehicle-list and route-feed screens load a small shared progress
component. It polls the authenticated, non-cacheable `/review-progress/` endpoint
every 500 ms and reloads when the current user's status changes. That endpoint is
read-only and never processes approvals or exposes other users' status. Hidden
tabs pause polling; pages restored from the browser back/forward cache refresh.
Network failures retry for 30 seconds before showing a truthful delay message.
Without JavaScript users can refresh the page to see the server decision.

Five seconds is the minimum processing delay, not a hard real-time SLA. Worker
scheduling, database load, restart/cold-start delay and browser refresh/network
latency can add time. A sleeping or stopped Render instance cannot process jobs;
its overdue queue catches up on restart. There is no browser-only fake success.

## Validation

Local PostgreSQL tests cover the boundary immediately before and at five seconds,
idempotence and audit provenance, concurrent workers, restart catch-up, disabled
policy, unsubmitted/inactive accounts, rejections, suspensions, driver/vehicle
eligibility, route posts versus private incident reports, and a private read-only
progress endpoint. Existing regression tests retain permission and booking checks.

Chromium evidence: `docs/evidence/automatic-approval/results.json` and WebP captures.
The measured account server decisions were at 5.106 and 5.126 seconds, the latter
with its browser context completely closed. Visible account, vehicle and route
transitions took 6.043, 5.817 and 5.771 seconds including navigation/poll/render.
Ten light/dark viewport combinations (320/390/768/1024/1440) had no horizontal
overflow or uncaught page errors. The supervisor test checks health, worker exit
handling, a subsequent startup and clean shutdown without orphan web processes.
CI launches the real worker and checks the account and vehicle transitions.

Production remains unverified until the reviewed release is deployed and its
live `/static/release.json` matches the release commit. Local timing evidence
must not be described as a measurement of production approval latency.

Final local release checks: Ruff clean; Django system check clean; migration
check reports no changes; pytest: 226 passed and 82 subtests passed. The local
startup instructions saved in the cloud configuration draft now include the
review worker; that draft save is separate from environment publication and
separate from the Render release.
