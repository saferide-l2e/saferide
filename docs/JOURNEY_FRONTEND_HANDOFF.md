# FE-11 — Journey progress, arrival and history UI

Passenger trip page shows independent states (seat held, boarded, en route, DRIVER MARKED ARRIVAL, PASSENGER CONFIRMED), driven by the server. Confirmation button renders only if booking_status=BOARDED, driver_arrived_at set, passenger confirmation not yet recorded and can_confirm=true. Confirm is a POST with CSRF and trusted confirm_action. The backend must check booking ownership and rule enforcement again even if HTML hides an action.

Passenger history lists only request.user's trips with privacy-safe status, overdue passenger confirmation, disputed marker and optional detail_url. Driver history lists only driver's own operated departures; **no passenger manifest** in history.

BE-09 backend contract: trip includes route_label, plate_display, booking_status, display_status, booking_held_at, boarded_at, en_route_at, driver_arrived_at, passenger_confirmed_at. Arrival timestamps must be separately stored. URL/view ownership and arrival state transitions enforced by server. The frontend doesn't create fake confirmation by client JS.

Required future checks: full PostgreSQL journey, cross-user forbidden access, arrival before boarding reject, cancelled trip, 360px, keyboard, zoom and realistic stale state. Keep issue #37 open until wired and tested.
