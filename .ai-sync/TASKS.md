# Cross-Tool Task Tracking

> **Active tasks visible to BOTH OpenCode and Antigravity agents.**
> Written by either tool, read by both. Update when starting/ending a session.

---

## Active Tasks

<!-- Format: ### [STATUS] Task Name — Started: YYYY-MM-DD — Tool: OpenCode/Antigravity -->

_(No active tasks)_

---

## Completed Tasks (Last 5)

### [DONE] Setup Prettier + eslint-config-prettier — 2025-04-17 — Tool: OpenCode
- Added Prettier config, eslint-config-prettier, pre-commit hook
- PR #13 merged to dev

### [DONE] Fix 5 REAL code review issues from v3.1.0 — 2025-04-17 — Tool: OpenCode
- Download auth gap, test improvements, SetupModal cleanup
- PR #12 merged to dev

### [DONE] Release v3.1.1 — 2025-04-17 — Tool: OpenCode
- VERSION + vpack/app.py header + RELEASE_NOTES.md updated
- PR #14 merged to master (--merge)

### [DONE] Release process lessons documentation — 2025-04-17 — Tool: OpenCode
- CONTRIBUTING.md updated with sole-developer workaround, strict:false docs
- PR #15 merged to dev

### [DONE] Fix required_approving_review_count in CONTRIBUTING.md — 2025-04-17 — Tool: OpenCode
- PR #16 merged to dev

---

## Task Protocol

### Starting a Task
1. Add task to "Active Tasks" section above
2. Include: STATUS, task name, date started, tool (OpenCode/Antigravity)
3. Briefly describe what you're doing

### Completing a Task
1. Move from "Active Tasks" to "Completed Tasks"
2. Note: PR number or commit hash
3. Leave brief completion note

### Cross-Tool Handoff
- When ending a session with unfinished work → also update `HANDOFF.md`
- When starting a session → check this file + `HANDOFF.md` for context
- **NEVER** remove another tool's task entry — only mark as superseded if needed
