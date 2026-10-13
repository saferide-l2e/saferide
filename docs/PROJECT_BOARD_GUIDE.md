# How to make the SafeRide Project board (team lead)

**This is a guide. The board is NOT created yet.** Only the repository and 45 issues are in place. The team lead or organization owner must do these steps in GitHub.

## A Project board is our task chart
Imagine four boxes. Each card is one GitHub Issue. You move the card as you work:

| Backlog | In Progress | In Review | Done |
|---|---|---|---|
| Not started | Someone is building it | A PR is being checked | Merged and tested |

**Never move an issue to Done only because its owner says “I finished.”** It needs a reviewed, merged PR and working tests.

## Create the board (organization owner)
1. Open **https://github.com/orgs/saferide-l2e/projects**.
2. Click **New project** (sometimes called **New project** then **Board** or **Board layout**).
3. Name it exactly: **SafeRide MVP Development**.
4. Set the **Status** choices to: **Backlog**, **In Progress**, **In Review**, **Done**. If GitHub starts with *Todo*, rename it to *Backlog*. Add *In Review* if missing. Find the status setting in the board field menu.
5. Add the existing repository issues as project items. Use **+ Add item** to search for an issue from `saferide-l2e/saferide` or paste its issue URL. Repeat or use multi-select if the UI offers it. There are **45** existing issues; do not create duplicates.
6. Keep all new issue cards in **Backlog** first. Claiming or starting a task moves it to **In Progress**. PR opened moves to **In Review**. Merged+tested moves to **Done**.
7. Copy the **real Project URL** and send it to the group. Check that all organization members with project access can open it.

## Make teams and give access
1. Open **https://github.com/orgs/saferide-l2e/teams** and create **frontend**, **backend**, **database** if missing.
2. Open **https://github.com/orgs/saferide-l2e/people** and invite members using their **actual GitHub usernames**. Only invite known teammates.
3. Give all three teams **Write** access to `saferide`. Keep owner/admin rights for trusted leads only.
4. Assign a specific teammate to each active issue in its **Assignees** field. Don't assign everyone to every issue. One main owner and optional helper is enough.

## Better team filtering (optional but useful)
1. Open **https://github.com/saferide-l2e/saferide/labels**.
2. Create three labels: `team:frontend`, `team:backend`, `team:database`.
3. Add a label to each existing issue by its title: `[FE-]` = Frontend, `[BE-]` = Backend, `[DB-]` = Database. Shared issues `[QA-]` and `[OPS-]` stay shared.
4. In the board, you can filter or make a saved view for each label, if that option is available.
5. **No labels have been added yet.** Until they are, use the linked team task lists. Each team already has exact issue URLs.

## Daily check-in
Start each day by opening the board. Ask each owner what is done, next, and blocked. If someone is stuck, arrange a pair-programming session. This is a learning project, not a blame board.

**If a button is missing in GitHub**, ask an owner to check their permissions. GitHub's interface and available project settings can change. Don't claim a board/team was created until you can open the real URL.

[Return to Start Here](TEAM_HUB.md)
