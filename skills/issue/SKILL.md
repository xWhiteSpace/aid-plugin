---
name: issue
description: A.I.D asks the person and the Engineer AI Agents the same five questions, then files one parent issue. Agent-invoked from /issue.
user-invocable: false
---

# /issue

The person talks to **A.I.D**. A.I.D talks to the Engineer AI Agents. The Issue Manager does not answer the person.

Ask the person, in order, and keep their words. Each answer is 1–3 lines. If an answer is empty, longer than three lines, or When is not one of the ten process ids, ask that question again. Do not rewrite it.

1. What — the change, or the behavior that is wrong
2. Why — the person and the moment
3. When — one of SYS.2, SYS.3, SWE.1, SWE.2, SWE.3, SWE.4, SWE.5, SWE.6, SYS.4, SYS.5
4. Criteria — a pass or fail check
5. How — a few sentences of approach

Then ask each Engineer AI Agent those same five questions. Their answers are 1–3 lines from the repo, posted as a signed note on the parent. Their When is the process the repo has already reached.

Only after both sets, propose Kind and the processes still ahead, and wait for a yes.

- Requirement files as SYS.1. Then run `aid-usr-flow` and publish a USR for the processes still ahead.
- Fix files as SUP.9. Name the process list and stop before minting a USR.

The degree is the gap between the person's When and the engineers' When. Lanes: tiny is SWE.3 and SWE.4; small adds SWE.1 and SWE.6; standard is SWE.1 through SWE.6; large is all ten.

On confirm, file the parent with `gh issue create`. Title is the first line of What. Body is Kind plus the five headings, in the same shape as the GitHub form. Reply with the issue number and URL. Tell the Issue Manager the kind and the list. Do not open sub-issues. Do not move Workflow Status.

`/issue 123` continues a parent filed from the form. Confirm the kind with the person before the Issue Manager opens sub-issues. If When names a process that is not on the list, the Issue Manager refuses to open sub-issues and A.I.D tells the person the gap. The person's words stay as filed.

After confirm, the gate comments are:

- `/gate-Parent-accept` on the parent. This does not empty Backlog.
- `/gate-Parent-breakdown` on the parent, with the process list. This is what moves the parent and the next sub-issue to Ready.
