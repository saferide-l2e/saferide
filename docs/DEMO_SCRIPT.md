# Friday 16 October — 6–8 minute live demo
**Demo uses fictional people, fictional vehicle plate and simulated identity reviews.** Put a visible "DEMO DATA" label on screens.
1. 30 sec: problem, both sides deserve accountability and privacy.
2. 45 sec: staff has already approved demo driver, passenger and vehicle; show limited badges, not documents.
3. 60 sec: driver publishes Jibowu -> Mile 2 departure (future enough to honor hold).
4. 60 sec: passenger searches and reserves a seat; show countdown and driver roster.
5. 60 sec: second passenger sees full bus and joins waitlist; cancel/expire first hold, show 120-second offer, accept it. Use deterministic test clock/helper for demo, not a 10-minute live wait; do not weaken production rule.
6. 60 sec: driver checks in via one-time code, departs/arrives; passenger confirms arrival.
7. 45 sec: completed passenger rates and files a private complaint; verified user submits traffic report; admin moderates.
8. 45 sec: show tests (especially concurrency and unauthorized access), one merged PR and lessons.
**Fallback:** local PostgreSQL app with prerecorded walk-through if live hosting fails. Never fake test results.
