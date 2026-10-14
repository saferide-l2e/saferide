# FE-03 — Simulated bilateral verification and public profile UI

Figma: https://www.figma.com/design/ztF1QqN7Npu55gnJwZVrG7

## Delivered
- User's own verification status: NOT_SUBMITTED, PENDING, VERIFIED, REJECTED, SUSPENDED with distinct help text and actions.
- An optional POST declaration form with Django Form fields, CSRF, validation and backend-controlled can_submit boolean.
- Driver and passenger public profile pages with a strict whitelist: public_display_name, initials and is_approved only.
- Visible disclosure: all checks are simulated. Do not upload real documents or pretend that governmental/licence checks are performed.
- Responsive CSS and rendering/privacy smoke tests.

## BE-02 integration contract
- Render templates/accounts/verification.html only after authentication and object-level ownership checks. Provide status string, optional rejection_reason, info_message, error_message, support_url and server validated form, can_submit, submit_action.
- The form must be a fictional declaration plus required consent; reject all real ID numbers, image uploads and personal licence documents. Only authorised admin can change verification status to VERIFIED or SUSPENDED. In particular can_submit must be false for PENDING, VERIFIED and SUSPENDED. Server enforce this; HTML cannot.
- Render the counterparty profile template from a public-only safe dictionary. Never pass a full raw User/DriverProfile model instance with extra personal attributes into the context.
- The badge describes **simulated** approval. Do not imply a police/criminal/background/physical licence registry check.
- Role permissions and booking/publishing eligibility must be enforced by BE-02 and subsequent backend views.

Still required: actual forms and routes from BE-02, independent approval workflow, forbidden-role tests, browser 360px/keyboard/zoom reviews. Keep FE-03 open until end-to-end.
