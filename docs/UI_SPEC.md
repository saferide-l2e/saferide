# SafeRide responsive frontend — FE-01

## Design and scope

Our design: https://www.figma.com/design/ztF1QqN7Npu55gnJwZVrG7

Team concept art: https://www.figma.com/design/hOvnMbooxS9EW7t2mjxYmU

Technology: Django templates + HTML + CSS + vanilla JS (no React). This is the first shared frontend PR, not completed reservations or real background screening.

Style tokens: forest #064F40, green #087D5B, lime #D6F86C, off-white #F8FAF5, ink #102F2C, muted #526B63.

Breakpoints: mobile first (320–649px, targeted minimum 360px), small tablet (650–799px), desktop navigation (800px+), large layout (950px+). Shared content max-width 1220px.

## Implemented

- / — semantic landing and the three anchored sections: Discover, Journey, Safety.
- Accessible header, navigation, mobile menu, site messages and footer.
- Shared Django includes for action links, feature cards, status badges, messages, form errors, and synthetic-data disclosures.
- Illustration of a Jibowu–Mile 2 route; not a live map. Motion respects reduced-motion settings.
- Role-aware account label for authenticated users. No fictitious login or booking success buttons.
- Browser JS closes the mobile menu after navigation, Escape or outside click. Without JS, links remain visible.
- Test file: apps/core/test_frontend.py. CI needs to execute this test and the project's other checks before completion is claimed.

## Upcoming issues and real Django backend contracts

| Issue | Screen | Needed server contract |
| --- | --- | --- |
| FE-02 #28 | Signup, login, logout | URL names, Django form names, roles, CSRF |
| FE-03 #29 | Profile and approval | Staff-managed state; private/public fields |
| FE-04 #30 | Vehicle registration | Driver ownership and APPROVED status |
| FE-05 #31 | Driver dashboard | Departures, capacity, POST and permissions |
| FE-06 #32 | Passenger search | Search parameters, results, stop data |
| FE-07 #33 | Bus detail | Eligible departure, public vehicle/driver info |
| FE-08 #34 | Hold and cancel | Server 600s expiry; CSRF POST and 409/403 states |
| FE-09 #35 | FIFO waitlist | Queue position; 120s offer and accept URLs |
| FE-10 #36 | Driver check-in | Assigned driver-only access and one-time code |
| FE-11 #37 | Trip and history | Driver ARRIVED separate from passenger confirmation |
| FE-12 #38 | Review, private report, route updates | Moderation and ownership contracts |
| FE-13 #39 | Accessibility and cross-browser polish | Real 360px, 200% zoom, keyboard, throttling evidence |

Re-use the data disclosure include on any booking, identity or reporting screens with fictional records. Never present unimplemented live GPS, registry verification, emergency dispatch or inventory changes as functional.

## Accessibility QA

- [x] Semantic landmarks, bypass/skip link, explicit link names, readable color+text states.
- [x] Menu button aria-expanded and Escape behaviour implemented.
- [x] Reduced-motion styles and no third-party font dependency.
- [ ] Manual keyboard-only pass in a browser.
- [ ] At 360px width, 200% zoom and low bandwidth, inspect overflow and headings.
- [ ] Test complete booking journeys after backend integration.
- [ ] Capture browser screenshots and request teammate review.

FE-01 should not be marked Done without real browser and CI evidence.
