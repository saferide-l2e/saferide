# Departures module

Departures store UTC-aware scheduled times and a lifecycle from draft through
arrival or cancellation. The domain service snapshots vehicle capacity when a
draft is created, checks driver and vehicle ownership, and only opens boarding
for an approved vehicle. PostgreSQL guards preserve those ownership and
capacity-snapshot invariants against direct writes.

Seat inventory, booking holds, and boarding credentials belong to their
separate database and backend issues.
