# SafeRide FE-02 — registration, login and logout UI

Design file: https://www.figma.com/design/ztF1QqN7Npu55gnJwZVrG7

## What has been built

- Django templates: templates/accounts/register.html and templates/accounts/login.html.
- Common form renderer: templates/includes/form_fields.html. Real bound Django Form fields, field-level and non-field errors.
- Semantic POST forms with csrf_token. Password widgets and role/consent fields come from the backend form rather than hardcoded HTML.
- Responsive authentication styling and conditional role-aware login/logout navigation.
- Sign-out is always a POST form with CSRF, never a GET link.
- Automated rendering smoke tests in apps/core/test_auth_templates.py.

## BE-01 integration contract

**The BE-01 endpoints are not in main yet; these forms are not a working auth service until the backend adds the views.**

1. Render the registration template with context variable form and a bound Django Form on invalid POST.
2. Form should provide a valid role (PASSENGER or DRIVER), display_name, email, password1, password2 and privacy acknowledgement checkbox. Enforce account uniqueness, password validation, privacy consent and allowed roles on server, not just in HTML.
3. Render the login template with a form containing email and password, and support next safely. Authentication uses Django sessions.
4. Prefer URL route names register, login and logout for the global navigation. If namespaced, pass login_url / register_url into template context for inter-form links. The sign-out route must only accept POST.
5. The registration view must not mark a new account VERIFIED automatically. Verification and permission checks belong to backend services.
6. Do not echo passwords, store auth tokens in JavaScript localStorage, or log private data.

## Remaining work

- Wire the backend's actual URL names and form fields once BE-01 merges, adjust markup only if needed.
- Real browser test at 360px and 200% zoom; keyboard only and screen reader review.
- Integration tests: successful registration, duplicate email, incorrect password, suspended account, logout CSRF, rejected unsafe next URL.

This PR covers frontend form rendering and CSS, not backend authentication or verified functional login.