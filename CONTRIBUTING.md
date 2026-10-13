# Contributing to SafeRide
1. Read [MVP_SCOPE](docs/MVP_SCOPE.md) and your assigned issue from start to finish.
2. Clone: `git clone https://github.com/saferide-l2e/saferide.git`
3. Create a branch from updated main: `git switch -c feat/issue-N-short-name`.
4. Work ONLY on the files and responsibilities in your issue; ask before changing database model contracts or another team's templates.
5. Run `ruff check .`, `python manage.py check`, and `pytest -q`; show results honestly. PostgreSQL is required for booking-concurrency tests.
6. Push your branch and open a PR. Put `Closes #N` in its description.
7. Request one teammate's review, address comments, and merge only after checks pass.
8. If stuck, post a short comment on your issue: what you tried, exact error (without secrets), and what help you need.

## Team ownership
Frontend: Django templates + static assets. Backend: views/forms/services/permissions. Database: models, migrations, constraints, fixtures. Review is cross-team. No one should assume issue assignment means exclusive file permission.

## Safety
Synthetic-only KYC and bus profiles for Friday. Driver sees only approved display name, booking status and boarding code result — never raw IDs, licences, private complaints, or contact details. No one may mark themselves VERIFIED or ADMIN.

## Definition of done
Feature works from the UI; backend enforces rules; database records are correct; relevant success/failure/security tests exist; CI passes; PR reviewed; issue linked. A screenshot alone is not done.
