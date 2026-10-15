# Account selection and copy correction

Original bug: the authentication text-field selector also matched radio inputs,
applying 100% width, 52px minimum height and text-field padding. The result was
oversized circles separated from their labels.

Registration now uses an accessible fieldset with compact native 18px radio
controls inside fully clickable Passenger/Driver cards. Text inputs explicitly
exclude radios. Keyboard focus has its own visible indicator; pointer selection
uses the green selected state. Native required-field behaviour, submitted role
values and account permission boundaries remain intact.

Customer copy was revised in account creation/review, eligibility errors, example
listings, route notices and administrative labels. Example listings remain
explicitly non-bookable; account review does not claim government identity or
licence checks. Legacy field names, internal modules and historical migrations
are retained for compatibility. Existing database records are not rewritten.
Migration 0003 changes only the displayed VERIFIED label to Account approved;
stored status codes and staff-only transitions are unchanged.

Actual local Chromium evidence, 15 October 2026:

- 320/390/768/1024/1440px, light and dark: no overflow, correct radio size.
- Ten axe WCAG A/AA checks: zero reported violations.
- Card clicks, keyboard arrows, driver preselection and selection retained after
  form-validation errors all pass. Native selection also works without JavaScript.
- Customer text scan passes on the checked public/auth/search/example pages.
- 46 focused account/review/discovery tests plus seven subtests passed. Full-suite
  and Chromium CI status for the latest commit is on PR #80.

Screenshots contain blank account fields, not the personal information from the
user's reference screenshot. The corrected interface is on the feature branch;
this evidence does not claim a production deployment.
