# SafeRide organization — status and owner checklist

**Confirmed by project lead's screenshots, 13 Oct 2026:** three organization teams exist; the [SafeRide MVP Development board](https://github.com/orgs/saferide-l2e/projects/1/views/1) has 45 existing issues and Frontend, Backend, Database views; the three team labels were created and all 35 team issues were labeled.

## Still check and complete as owner
- [ ] Everyone invited has ACCEPTED their organization invitation.
- [ ] Add each accepted person to their selected team: [Teams](https://github.com/orgs/saferide-l2e/teams) → team → Members → Add member. **There is no automatic team-join link.** The team URL opens the page; it does not add a person by itself.
- [ ] Give each team **Write** permission on the [SafeRide repository](https://github.com/saferide-l2e/saferide/settings/access) (exact settings UI label may differ). Avoid Admin for most members.
- [ ] The board is marked **private** (lock icon). In Board `...` → Settings → Manage access, allow teammates to open board and change status. Test with a non-owner.
- [ ] Save the Frontend/Backend/Database view filters. Verify issue counts: **13, 14, 8**. Use labels `team:frontend`, `team:backend`, `team:database`, or title terms `FE-`, `BE-`, `DB-`.
- [ ] Assign one named GitHub owner to each task being started; select tasks by current skill and dependencies. Shared issues are for coordination/testing/pitch.
- [ ] Check **main** branch protection/rulesets if the organization plan permits it. Use a voluntary one-review rule regardless; document if private-org GitHub Free cannot enforce it.
- [ ] Check latest CI run before claiming green. Green foundation tests do not mean the SafeRide features are finished.

[Beginner Team Hub](TEAM_HUB.md) · [Board steps](PROJECT_BOARD_GUIDE.md) · [Meeting guide](TEAM_MEETING_GUIDE.md).
