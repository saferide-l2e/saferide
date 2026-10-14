# Bookings module

`Booking.Status` is the stable lifecycle enum for backend integrations. The
database permits one active (`HELD` or `BOARDED`) booking per passenger and
departure, while preserving historical completed records.

Boarding codes are issued by `apps.bookings.services.issue_boarding_credential`
and verified with `verify_boarding_code`. Only the salted digest is persisted;
the returned raw code is available once to the caller and must not be logged or
rendered from a digest field.
