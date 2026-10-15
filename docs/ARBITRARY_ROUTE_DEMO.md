## Arbitrary location demo-search behavior

SafeRide’s public route search accepts any pair of place labels (up to 80 printable characters each). Search remains **read-only**.

- If SafeRide has a published, not-yet-departed departure matching the names, show **real database-backed SafeRide demo inventory**, even to unverified users. Verification is still enforced by booking services and driver permissions.
- Normalize whitespace when matching place names, so `Mile2` finds `Mile 2`.
- If no published departure matches, generate **four fictional example buses** using a reproducible SHA-256-derived pseudorandom seed for the entered route and UTC calendar day. Show sample departure times, illustrated vehicles and example seat counts. These do not assert that routes/operators/seats exist.
- Example cards are clearly marked **Fictional example / Not a live bus / Not bookable**. They have expandable descriptions, but no reservation URL, ID or database row. Refreshing the same search does not invent new inventory in PostgreSQL.
- For arbitrary locations, display the *entered route names* and an external Google Maps directions link. **Do not draw the unrelated Jibowu–Mile 2 illustration** as though it mapped the user’s query.
- If a verified passenger chooses an existing published departure, existing 600-second holds, single-use boarding codes, capacities and staff-reviewed verification remain enforced unchanged.
- No live GPS, real transport providers, route geocoding or confirmed bus availability is implied.

**Demo instructions:** Try `/departures/search/?origin=Agege&destination=Lekki` for four non-bookable examples. Try `Jibowu` → `Mile2` to locate available **published** sample departures (if still scheduled). To make a demo booking, sign in with a staff-approved fictional passenger and select one of those published departures.

This feature deliberately does not auto-create routes, vehicles, drivers, verification approvals or departure inventory from unauthenticated search requests.
