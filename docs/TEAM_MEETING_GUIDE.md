# SafeRide
**Tuesday 13 October 2026 · Friday demo 16 October 2026**


**Welcome**

“Hello, everyone! Thank you for joining SafeRide. Today I want to show you what we are building, how we will work, where your tasks are, and how we will get ready for Friday.

SafeRide is a bus-booking demo. A passenger can search for a bus from **Jibowu to Mile 2**, see a small approved driver profile, and hold one seat for **10 minutes**. If the seat is not used, the system can offer it to the next person waiting. A driver can check a passenger in with a one-time code. After the ride, the passenger can confirm arrival, give a rating or send a private report.

Both drivers and passengers need approval in the app. For Friday, these checks are **pretend demo checks with fictional people**. We are NOT checking real IDs or criminal records, and we must not claim the app guarantees safety.

**What is ready?**

We have created our [GitHub organization](https://github.com/saferide-l2e), [code repository](https://github.com/saferide-l2e/saferide), three development teams, [Project board](https://github.com/orgs/saferide-l2e/projects/1/views/1), starter Django project, tests and detailed issues. The starter checks have passed before, but most app features are **not built yet**.

We have **45 tasks** on GitHub. They are called **Issues**. Every issue says what to build, what code to touch, how to test it and when the work is done. You do not need to guess.

**Who builds what?**

- **Frontend — 13 issues:** You build what people see: signup, bus search, driver page, 10-minute timer, waitlist and mobile pages.
- **Backend — 14 issues:** You make the features work: signup/login, demo approval rules, finding buses, booking without double-booking, boarding codes, arrival, reviews and reports.
- **Database — 8 issues:** You decide how we save accounts, drivers, buses, trips, bookings, waitlist, reviews and demo data in PostgreSQL.
- **10 shared issues:** These cover GitHub setup, putting everyone's work together, testing, launch, and the Friday pitch. All teams help.

The three groups need each other. When a passenger taps Reserve, Frontend shows the button, Backend checks the booking rules, and Database saves the seat.

**How to find your work**

Go to [Everyone Start Here](TEAM_HUB.md) or your team view on the board. Click a task. Read it all. Ask the leader to assign you **one first task** using your GitHub username. Some tasks must wait for another task. Do not take many issues at once.

**How we track progress**

Our GitHub Project board has four columns: **Backlog** means not started. **In Progress** means you are building it. **In Review** means you have sent code for another person to check. **Done** means the code was reviewed, added to the main project, and tested.

**How to work and learn**

Each person should make their changes on a **branch** (a safe copy of the code), test them, and open a **Pull Request** (ask the team to review the code). Do not push straight to `main`.

You can use YouTube lessons, Django documentation, teammates and AI tools. Ask AI to explain a small idea, practise it yourself, and check that you understand the code. If you are stuck, tell the group what you tried and what help you need.

**Everyone helps with the pitch**

Every person should practise a **30–60-second talk** about their own work: What did you build? How does it work? What did you learn? Please volunteer if you would like to pitch, click through the live demo or answer questions. We will practise as a group. You do not have to be an expert speaker. Thank you — let's build and learn together!”

---

## 2. Show these screenshots/screens in this order (about 5 minutes)

| Show | What to open | What to point at / say |
|---|---|---|
| **1. Whole board** | [Board All Tasks](https://github.com/orgs/saferide-l2e/projects/1/views/1) | “All 45 jobs are here. The four columns tell us what is happening.” Clear any team filter and show the total. |
| **2. Team views** | [Same board](https://github.com/orgs/saferide-l2e/projects/1/views/1) | Click **Frontend**, **Backend**, **Database** tabs. “You only need to look at your own team's tasks.” Confirm 13 / 14 / 8 items. |
| **3. Labels** | [Repository labels](https://github.com/saferide-l2e/saferide/labels) | Show `team:frontend`, `team:backend`, `team:database`.  “These labels help us find tasks fast.” |
| **4. One issue** | [Issue #17 — Reserve a Seat](https://github.com/saferide-l2e/saferide/issues/17) | Scroll to instructions, acceptance tests and coding-agent prompt. one issue is one clear job. |
| **5. Code repository** | [SafeRide Code](https://github.com/saferide-l2e/saferide) | Show `templates/`, `static/`, `apps/`, `tests/` and `docs/`. Explain what each team edits. |
| **6. GitHub Teams** | [Teams](https://github.com/orgs/saferide-l2e/teams) | Show Frontend/Backend/Database. Tell members to accept the organization invite. The leader adds them to their team. |
| **7. Pull Requests** | [PR page](https://github.com/saferide-l2e/saferide/pulls) | “When you finish some code, you ask someone else to check it here.” Empty is normal at the start. |
| **8. Tests** | [GitHub Actions](https://github.com/saferide-l2e/saferide/actions) |  “GitHub can test our code automatically. A green foundation test does not mean the whole app is ready.” |


## 3.

| Word | Meaning |
|---|---|
| **GitHub** | The website where our team keeps code and tasks. |
| **Organization** | Our main SafeRide group on GitHub. |
| **Team** | A smaller group: Frontend, Backend or Database. |
| **Repository (repo)** | Our shared project code folder. |
| **Issue** | One job with written instructions. |
| **Assignee** | The person who owns that job. |
| **Branch** | Your own safe place to work on code. |
| **Commit** | Saving a set of changes to Git. |
| **Pull Request (PR)** | Asking the team to review your code before adding it. |
| **Project board** | A chart that shows not started, working, checking, and finished. |
| **P0** | First priority. |
| **P1** | Do this after the most important parts work. |
| **Test** | A way to check that code works and catches mistakes. |


 
