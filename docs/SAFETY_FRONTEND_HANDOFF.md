# FE-12 — SafeRide ratings, private reports and moderated route updates

Django template screens: safety/review.html, safety/report.html, safety/route_feed.html, safety/route_update_form.html. All submit actions require real Django Forms and csrf_token, conditional permissions from backend, and server-rendered validation. Styling static/css/safety_ui.css follows our shared Figma design.

BE-10 owns ratings (stars 1..5, one rating per passenger-owned completed trip) and confidential incident reports (involved passenger or driver, private reviewer-only case status). Public profiles must NEVER render raw reports or unmoderated accusations.

BE-11 owns community updates; publish only APPROVED timestamped route notices from server-filtered queryset, without creator's personal details or risky driver blacklist/score data. This template defensively hides PENDING notices too. An eligible verified account submits PENDING notices using POST + CSRF, with staff moderation before public display.

Context: review — can_review, trip_is_completed, has_reviewed, form, review_action, report_url; report — can_report, form, report_action, report_submitted, case_reference; route_feed — updates with status/type_label/route_label/note/published_at, can_contribute/contribute_url; route_update_form — can_submit, form, form_action, submitted/feed_url. Optional error_message, success_message and action_message.

No live backend endpoints are included. BE-10/11 must add ownership checks, permissions, moderation/auditing, abuse tests and PostgreSQL integration. Manual 360px/200%-zoom/keyboard/low-bandwidth testing is outstanding. Do not close issue #38 yet.
