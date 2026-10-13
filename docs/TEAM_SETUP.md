# Organization tasks owners must finish manually
The connected GitHub app can create repository files and issues but **cannot configure GitHub Teams, GitHub Projects boards, new issue labels, member invitations, branch protections or organization permissions** using available actions. These must be done by an organization owner:
1. Teams: https://github.com/orgs/saferide-l2e/teams -> create visible `frontend`, `backend`, `database`; add verified member GitHub usernames after invitations are accepted; give each Write access to `saferide` (do not grant Admin).
2. People: https://github.com/orgs/saferide-l2e/people -> invite seven known team members by GitHub handle. Do not guess handles from their names.
3. Board: https://github.com/orgs/saferide-l2e/projects -> New project, name `SafeRide MVP Development`, status options `Backlog`, `In Progress`, `In Review`, `Done`; add every repo issue to board. Keep scope to all created issue cards.
4. Labels: https://github.com/saferide-l2e/saferide/labels -> create `team:frontend`, `team:backend`, `team:database`, `priority:p0`, `priority:p1`, `type:test`, `type:docs`, `blocked`. Then tag issues by title prefix.
5. Protect main if plan supports it: https://github.com/saferide-l2e/saferide/settings/branches -> require PR, 1 review, CI checks. Confirm protection **actually works**; private org Free plans may not enforce it. Team policy must still require reviewed PRs.
6. Set access requests/repository visibility according to least privilege. Never add unknown agents as Owners.
7. Teams/board are not created until the owner checks the GitHub UI and verifies their URLs. Track setup tasks on issues instead of calling them done.
