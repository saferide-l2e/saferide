# Bookings module

`Booking.Status` is the stable lifecycle enum for backend integrations. The
database permits one active (`HELD` or `BOARDED`) booking per passenger and
departure, while preserving historical completed records.

Boarding codes are issued by `apps.bookings.services.issue_boarding_credential`
and verified with `verify_boarding_code`. Only the salted digest is persisted;
the returned raw code is available once to the caller and must not be logged or
rendered from a digest field.

`WaitlistEntry.objects.fifo()` orders equal join times by UUID for deterministic
queue order. `offer_next_waitlist_entry` should run inside the departure
inventory transaction after a seat is released. Count unexpired `OFFERED`
entries with `allocated_offer_count()` as occupied seats; do not expose them as
free inventory. Offers default to a 120-second expiry.
