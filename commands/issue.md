---
name: issue
description: Talk to A.I.D. Ask What, Why, When, Criteria, and How, confirm requirement or fix, and file the parent issue.
---
Run the `issue` skill from the A.I.D plugin on the message that follows this command.

A.I.D asks the five questions, then asks the Engineer AI Agents the same five. It proposes Kind (Requirement is SYS.1, Fix is SUP.9) and the process list, and waits for a yes. It files the parent with `gh`. It does not open sub-issues or move Workflow Status. A requirement then runs `aid-usr-flow`. A fix stops before a USR. A.I.D tells the Issue Manager the kind and the list.

`/issue 123` continues a parent already filed from the GitHub form. There is no `/usr` command.
