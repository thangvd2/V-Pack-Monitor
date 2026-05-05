# Project Memory — Learned Lessons

> **Episodic + Procedural memory shared across OpenCode and Antigravity.**
> This file captures lessons learned during development to prevent repeating mistakes.
> Both platforms READ this file to benefit from past experiences.

---

## Critical Lessons

### 1. Release Process: ALWAYS use --merge for dev → master
- **What happened**: Used `--squash` for release PR (dev → master). This created a new commit on master that dev doesn't share, breaking shared history.
- **Impact**: Every subsequent release PR had 12+ file conflicts.
- **Fix**: `gh pr merge <N> --merge` (merge commit, NOT squash). This creates a commit with 2 parents, so git knows dev ≤ master.
- **Rule**: Feature PR → dev: `--squash`. Release PR → master: `--merge`. NO EXCEPTIONS.

### 2. GitHub API Propagation Delay
- **What happened**: After PATCHing `required_approving_review_count` to 0 via GitHub API, immediately tried to merge PR. Still got "required reviews" error.
- **Root cause**: GitHub API has propagation delay (30+ seconds) for branch protection changes.
- **Fix**: `sleep 30` after PATCH, or DELETE protection entirely + restore after merge.
- **Rule**: Always wait 30s after API changes to branch protection before merging.

### 3. Never Trust Root Cause Without Evidence
- **What happened**: Agent stated "strict: true caused the conflict" but the actual cause was API propagation delay.
- **Impact**: Wasted time debugging wrong root cause.
- **Rule**: Always VERIFY root cause with evidence (logs, API responses, git state) before proposing fixes. State assumptions explicitly.

### 4. Pre-commit Hooks Must Be Idempotent
- **What happened**: Pre-push branch protection hook blocked a push even though the branch was correct.
- **Root cause**: Hook script had edge case with branch naming.
- **Rule**: Pre-commit hooks must handle edge cases gracefully and provide clear error messages.

### 5. AI False Positives in Code Review
- **What happened**: AI flagged 5 "REAL" issues. After deep investigation, 3 were FALSE POSITIVE (already mitigated elsewhere).
- **Impact**: Wasted time investigating non-issues.
- **Rule**: ALWAYS check for existing mitigations BEFORE flagging issues. Provide FOR and AGAINST evidence. Issue without against-evidence = incomplete review.

### 6. Indentation/Formatting Issues Should Be Caught by Tooling
- **What happened**: Prettier not configured, so indentation issues slipped through to PR.
- **Fix**: Setup Prettier + eslint-config-prettier + pre-commit hook.
- **Rule**: Formatting issues should NEVER reach code review. Automated tooling catches them.

### 7. Release Conflict Root Cause: dev Not Synced from master After Release
- **What happened**: v3.2.0 release PR conflicted on VERSION/vpack/app.py/RELEASE_NOTES when merging master into release branch (Step 4).
- **Root cause**: After v3.1.1 release (merge to master), dev was never synced back from master. Dev stayed at VERSION v3.1.0 while master had v3.1.1. Next release branch (from dev) conflicted when merged with master's newer VERSION.
- **Fix**: Added Step 7 to release workflow — after tag+release creation, merge master back into dev (`git merge origin/master --no-edit`). This ensures dev ≤ master at all times.
- **Prevention**: ALWAYS sync dev from master after every release. Never skip this step.

---

## Project-Specific Gotchas

### V-Pack Monitor Architecture
- `vpack/app.py` is the FastAPI app entry point — DO NOT add routes here. Use `routes_*.py` which export `register_routes(app)`.
- `vpack/video_worker.py` uses bounded queue (max 10). Don't add unbounded queues — OOM risk with large video files.
- `vpack/database.py` uses Fernet encryption for sensitive fields (Telegram bot token, cloud credentials). Key is persisted in DB by `vpack/auth.py`.
- SSE events in backend MUST have corresponding frontend handler in the SAME commit.
- FFmpeg processes must be cleaned up on shutdown — check `vpack/recorder.py` cleanup paths.

### Testing Patterns
- Tests use `tmp_path` fixture for isolation — no shared state between tests, no temp file leaks.
- Spy pattern: Use `mocker.patch()` not `@patch` decorator for test isolation.
- Thread safety tests: Always verify cleanup (cancel timers, join threads, close connections).

### Frontend Patterns
- React stale closures: useEffect deps array must include all referenced variables.
- WebRTC player: Sub-stream only (H.264), main-stream is for recording (HEVC).
- Prettier config: single quotes, trailing commas, 120 char width.

---

## Procedural Memory — Workflows That Work

### Effective PR Review Flow
1. Fire 2-3 parallel review agents (backend, frontend, tests)
2. Collect ALL flagged issues (don't filter)
3. For each issue, verify with full dependency chain
4. Classify: REAL / SPECULATIVE / FALSE POSITIVE
5. Report only REAL issues to user

### Effective Release Flow
1. Update VERSION + vpack/app.py header + RELEASE_NOTES.md on dev
2. Create release branch from dev
3. Push + create PR to master
4. Wait CI pass (if "not up to date", merge master into release branch)
5. Merge with `--merge` (NOT --squash)
6. Create git tag + GitHub release
7. Sync dev from master (CRITICAL — prevents next release conflict)
8. Verify dev ≤ master

### Thread Safety Debugging
1. Map all lock acquisitions (file:line)
2. Check lock ordering across ALL code paths
3. Verify cleanup paths (error, shutdown, cancellation)
4. Look for stale references in closures/callbacks
5. Test with concurrent access patterns
