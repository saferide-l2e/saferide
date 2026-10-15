# Database model contract — Database team source of truth
Use UUID IDs for public records, UTC aware datetimes, PostgreSQL in the booking tests. Create migrations in dependent order and agree naming with backend first.

| Model | Essential fields and constraints |
|---|---|
| User | email unique, password hash, role PASSENGER/DRIVER (admin=staff), display_name, is_active; custom user from day one |
| Verification | user one-to-one, status NOT_SUBMITTED/PENDING/VERIFIED/REJECTED/SUSPENDED, reviewed_by/date; demo only, no real documents |
| DriverProfile | user one-to-one, approved display fields; licence review STATUS only |
| Vehicle | driver, plate_normalized unique for pilot, plate_display, vehicle_type, capacity > 0, approval_status |
| Route | origin_name, destination_name, boarding_point, destination_point |
| Departure | route, driver, vehicle, scheduled_departure_at, capacity_snapshot, walk_in_count >= 0, DRAFT/BOARDING_OPEN/BOARDING_CLOSED/EN_ROUTE/ARRIVED/CANCELLED |
| Booking | UUID; departure, passenger, HELD/BOARDED/COMPLETED/CANCELLED/EXPIRED/DISPUTED, created_at, expires_at, checked_in_at, driver_arrived_at, passenger_confirmed_at; partial unique (departure, passenger) while HELD/BOARDED |
| WaitlistEntry | UUID; departure, passenger, WAITING/OFFERED/ACCEPTED/EXPIRED/CANCELLED/INELIGIBLE, joined_at, offered_at, offer_expires_at, accepted_booking; FIFO order (joined_at,id); partial unique (departure,passenger) while WAITING/OFFERED |
| BoardingCredential | booking one-to-one, unique salted `code_digest` (never raw code), issued_at, consumed_at, revoked_at |
| Review | booking unique, author=passenger, stars 1–5, comment, created_at |
| IncidentReport | booking nullable for route reports, reporter, subject optional, category, description, PENDING/REVIEWED/RESOLVED/DISMISSED |
| RouteUpdate | route, reporter, type TRAFFIC/SAFETY, note, occurred_at, PENDING/APPROVED/REJECTED |
| AuditEvent | actor, action, object ref, created_at, redacted metadata |

Indexes: departure(route,status,scheduled_departure_at), booking(departure,status,expires_at), waitlist(departure,status,joined_at,id). Partial unique indexes for active booking statuses (HELD,BOARDED) and for WAITING/OFFERED waitlist per person+departure. CHECK stars 1..5; capacity>0; walk-ins >=0. Enforce aggregate inventory **in locked service**, not row CHECK.

Deletion policy: do not cascade-delete an existing booking or its incident evidence just because a user or bus profile is deactivated. Use privacy-sensitive retention/soft deactivation; real launch requires documented lawful basis and retention limits.
