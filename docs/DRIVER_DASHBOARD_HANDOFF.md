# FE-05 — driver dashboard and departure publishing

## UI delivered
- driver/dashboard.html: server-provided upcoming trips, approved vehicle and boarded counts, driver-only actions/links.
- driver/publish_departure.html: real bound Django form (approved vehicle, route, boarding point, scheduled departure time as provided by BE-03), server error display and CSRF.
- driver/departure_detail.html: DRAFT/BOARDING_OPEN/BOARDING_CLOSED/EN_ROUTE/ARRIVED/CANCELLED display, and state-gated **POST** actions for close, start, arrive, cancel.
- Mobile-first CSS + template/HTML escaping/CSRF smoke tests.

## Backend contract
BE-03/BE-09 must provide driver-only auth/ownership checks. Context for dashboard: can_publish, publish_url, upcoming_count, approved_vehicle_count, boarded_today_count, departures (route_label, scheduled_departure_at, plate_display, capacity, status/status_label, detail_url). No other drivers' trips or private rider records.
Publishing context: can_publish, form (approved vehicle selection, route, boarding point, scheduled departure_at), form_action, time_zone_label defaulting to Africa/Lagos WAT. Require >=10 minutes until departure at server clock **after** timezone conversion, not HTML-only validation. Validate approved bus and staff/driver role.
Departure context: departure.status/status_label/route_label/scheduled_departure_at/plate_display/capacity/boarded_count/held_count; can_close/can_start/can_arrive/can_cancel and action URLs, search/roster links. Only permitted buttons render and all POST with CSRF. Backend must reject wrong-driver access and state changes even if user forges the URL. Driver arrival must not mark the passenger arrived.

## Still to do
BE-03/09 URLs and permissions are not merged. No live publishing or status transitions here. End-to-end PostgreSQL transitions, admin approval, wrong-role requests, invalid time (9 minutes), keyboard at 360px and 200%-zoom tests pending. Keep FE-05 open.
