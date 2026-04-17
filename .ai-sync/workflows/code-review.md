# Code Review Workflow

> **Agent-assisted code review procedure.**
> Use this workflow when reviewing PRs or preparing code for review.
> Shared between OpenCode and Antigravity.

---

## Phase 1: Context Gathering

Before reviewing any code:
1. **Read the PR description** — What problem does this solve? What approach? Known limitations?
2. **Check architecture decisions** — Does this relate to any existing ADR or constraint?
3. **Identify scope** — How many files changed? What subsystems affected?

## Phase 2: Security Review

### Mandatory Checks
- [ ] No hardcoded secrets
- [ ] No eval() or dynamic code execution
- [ ] No unsanitized user input
- [ ] No SQL string interpolation
- [ ] Auth checks on all protected routes
- [ ] Input validation present

## Phase 3: Code Quality Review

### Structure
- [ ] Files under 300 lines
- [ ] Functions under 50 lines
- [ ] Nesting under 3 levels
- [ ] Clear separation of concerns
- [ ] No circular dependencies

### Patterns
- [ ] Error handling is explicit (no bare catch)
- [ ] Types are complete (no `any`)
- [ ] Resources are properly closed
- [ ] Thread safety verified (if applicable)

## Phase 4: Test Coverage

### Required Tests
- [ ] Happy path covered
- [ ] Edge cases handled
- [ ] Error paths tested
- [ ] Integration points verified

## Phase 5: Review Summary

Generate structured review:
- 🟢 **Approved Items** — Good practices observed
- 🟡 **Suggestions** — Optional improvements (non-blocking)
- 🔴 **Required Changes** — Must fix before merge
- 📋 **Verification** — Tests pass, build succeeds, no new warnings

## Decision Matrix

| Finding | Severity | Action |
|---------|----------|--------|
| Security vulnerability | 🔴 Critical | Block merge, fix immediately |
| Missing tests | 🔴 High | Block merge |
| Type errors | 🔴 High | Block merge |
| Lint violations | 🟡 Medium | Fix or document exception |
| Style inconsistencies | 🟡 Medium | Suggest fix |
| Minor improvements | 🟢 Low | Optional |
