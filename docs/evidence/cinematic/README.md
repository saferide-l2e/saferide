# Chromium evidence — cinematic landing

Actual local Chromium captures from the focused feature branch, 15 October 2026.

- `hero-{320,390,768,1024,1440}.webp`: responsive first viewport.
- `home-1440.webp`: complete homepage.
- `home-dark-390.webp`: complete dark theme phone page.
- `how-it-works-light-390.webp`, `for-drivers-light-390.webp`,
  `safety-support-light-390.webp`: connected public pages.
- `landing-results.json`: widths, layout shifts, links, queries, preference/media
  lifecycle tests and 28 axe audits.
- `product-theme-results.json`: 22 authenticated page/theme audits.
- `workflow-results.json`: isolated PostgreSQL registration/booking/check-in run.

The hero is an original **static** composition. Video lifecycle tests use silent
synthetic colour bars injected by the local test harness. These captures do not
show or prove realistic moving danfos, passenger boarding animation, a seamless
cinematic video loop, or a deployed release. See the handoff for outstanding media.

`interface-walkthrough.mp4` is a native Chromium/CDP interface recording (92
captured frames, about 7.1 seconds): hero, smooth section navigation, actual
keyless MapLibre road preview/stop selection and theme switching. It is **not**
cinematic traffic/boarding footage. `interface-recording.json` records timing.
`production-smoke.json` records the separate DEBUG=false local static-page check.

`native-media-results.json` is the follow-up complete landing/media run using the
actual Django hero template, WebM + MP4 fixtures, and both mobile and desktop
playback controls. Its axe array is empty because that follow-up run did not
repeat axe; the separate 28-audit evidence remains in landing-results.json.
