# .ai-sync/ — Universal AI Tool Coordination Protocol

> **Single source of truth for coordinating OpenCode (GLM-5.1) and Antigravity (Gemini) on the same project.**

---

## Quick Start

```bash
# 1. Edit rules/context in .ai-sync/ files
vim .ai-sync/RULES.md
vim .ai-sync/CONTEXT.md

# 2. Sync to both platform configs
python .ai-sync/sync.py

# 3. Check if configs are up to date
python .ai-sync/sync.py --check

# 4. Preview changes without writing
python .ai-sync/sync.py --dry-run
```

## How It Works

```
.ai-sync/                          ← YOU EDIT HERE (single source of truth)
├── CONTEXT.md                     ← Project overview, tech stack, constraints
├── RULES.md                       ← Shared coding rules (both platforms)
├── MEMORY.md                      ← Learned lessons (episodic/procedural)
├── TASKS.md                       ← Cross-tool task tracking
├── HANDOFF.md                     ← Session handoff between tools
├── extensions/
│   ├── opencode.md                ← OpenCode-specific rules (→ AGENTS.md)
│   └── antigravity.md             ← Antigravity-specific rules (→ .agents/rules/)
└── workflows/                     ← Shared procedures (copied to both)
    ├── code-review.md
    └── release.md
        ↓ python .ai-sync/sync.py ↓
AGENTS.md                          ← AUTO-GENERATED for OpenCode
.agents/
├── rules/
│   ├── project-rules.md           ← AUTO-GENERATED shared rules for Antigravity
│   └── platform-antigravity.md    ← AUTO-GENERATED platform rules for Antigravity
├── workflows/                     ← COPIED from .ai-sync/workflows/
└── skills/                        ← Universal skills (managed separately)
```

### Sync Formula

```
AGENTS.md                              = CONTEXT.md + RULES.md + extensions/opencode.md
.agents/rules/project-rules.md         = CONTEXT.md + RULES.md + extensions/antigravity.md
.agents/rules/platform-antigravity.md  = extensions/antigravity.md (split when project-rules.md > 12,000 chars)
.agents/workflows/                     = Copied from .ai-sync/workflows/
```

### Architecture Notes

Per Antigravity official docs (`antigravity.google/docs/rules-workflows`):

**Directory Structure:**
- **Workspace Rules**: `.agents/rules/` — Markdown files, max 12,000 chars each
- **Workspace Workflows**: `.agents/workflows/` — Markdown files, max 12,000 chars each
- **Workspace Skills**: `.agents/skills/<skill-folder>/SKILL.md` — YAML frontmatter + instructions
- **Global Rules**: `~/.gemini/GEMINI.md` — applied across all workspaces
- **Global Skills**: `~/.gemini/antigravity/skills/<skill-folder>/SKILL.md` — all workspaces
- **Backward support**: Antigravity also reads `.agent/rules/` and `.agent/skills/` (legacy)

**Rule Activation Modes (Antigravity only):**
- **Always On**: Always applied (sync.py generates rules with this mode)
- **Manual**: Activated via `@rule-name` mention in Agent input
- **Model Decision**: Agent decides based on rule description
- **Glob**: Applied to files matching a glob pattern (e.g., `*.py`)

**@ Mentions:** Rules can reference files via `@filename` (relative to rule file, or absolute)

**Skills:** Open standard — each skill is a folder with `SKILL.md` containing YAML frontmatter:
```yaml
---
name: my-skill
description: What this skill does and when to use it.
---
# My Skill
Instructions for the agent...
```

**Workflows:** Invoked via `/workflow-name` slash command. Can chain workflows. Agent can auto-generate workflows from conversation history.

**sync.py validates** 12,000 char limit on generated `.agents/rules/project-rules.md` and all workflow files.

### Platform Feature Matrix

Features verified against official documentation:

| Feature | OpenCode (GLM-5.1) | Antigravity (Gemini) | Claude Code |
|---------|:-------------------:|:--------------------:|:-----------:|
| Auto-loaded project rules | `AGENTS.md` | `.agents/rules/*.md` | `CLAUDE.md` |
| Char limit per rule file | None known | 12,000 chars | None known |
| Rule activation modes | — | ✅ (4 modes) | ✅ (globs) |
| `@path/to/import` in rules | ❌ Not supported | ❌ Not supported | ✅ Supported |
| Symlink-based rule sharing | ✅ (via sync.py) | ✅ (via sync.py) | ✅ (native) |
| `@ Mentions` for rules | — | ✅ `@filename` | ✅ `@path` |
| SKILL.md format | — | ✅ YAML frontmatter | ✅ |
| Workflow slash commands | — | ✅ `/workflow-name` | — |

> **Note**: Z.AI docs (`docs.z.ai/devpack/resources/`) describe generic best practices for coding agents and use **Claude Code as a reference example**. Features like `@path/to/import` and `.claude/rules/` are Claude Code-specific, NOT OpenCode/GLM-5.1 features.

## Best Practices Framework

Based on Z.AI's *Best Practices for Coding Agents* (`docs.z.ai/devpack/resources/best-practice`). These 10 principles are **generic patterns applicable to all coding agents** — both OpenCode (GLM-5.1) and Antigravity (Gemini) benefit from them. The `.ai-sync/` protocol implements each principle to varying degrees.

> **Key insight from Z.AI**: *"The value of a coding agent does not come from model capability alone. It comes from the combination of model capability and the development workflow around it."*

### Implementation Status

| # | Principle | Description | `.ai-sync/` Implementation | Status |
|---|-----------|-------------|---------------------------|--------|
| 1 | **Collaborator, not Q&A** | Agent is a configurable collaborator refined over time via guidance files, tool integrations, reusable skills | RULES.md + MEMORY.md + workflows/ shape agent behavior across sessions | ✅ Done |
| 2 | **Structure Task Inputs** | Every task needs 4 elements: Goal, Context, Constraints, Done-when | TASKS.md (goal), CONTEXT.md (context), RULES.md (constraints), Self-verification checklist (done-when) | ✅ Done |
| 3 | **Plan Before Execution** | Complex tasks → plan first, implement second. Avoid immediate code generation | OpenCode: Plan mode + subagent delegation. Antigravity: Planning vs Fast mode. workflows/ = pre-defined plans | ✅ Done |
| 4 | **Project-Level Config Files** | Long-lived rules in config files, not repeated in prompts. *"Put temporary instructions in the prompt, long-lived rules in config files."* | sync.py generates AGENTS.md + `.agents/rules/` from `.ai-sync/` source files. Rules never repeated in prompts. | ✅ Done |
| 5 | **Execution Environment** | 3 context types: Task, Project, Environment. Environment determines what agent can do | Task = user prompt. Project = CONTEXT.md + RULES.md. Environment = platform permissions (OpenCode subagents, Antigravity `action(target)`) | ✅ Done |
| 6 | **Full Development Loop** | Agent participates in: Implement → Test → Run tests → Lint → Review | RULES.md "Self-Verification Checklist" enforces all 5 steps. workflows/code-review.md = structured review | ✅ Done |
| 7 | **MCP Integration** | Extend agent context beyond repo — issue tracking, CI/CD, databases, API docs | OpenCode: librarian + Context7 + web tools. Antigravity: MCP server support. `.ai-sync/` does not yet define shared MCP config | ⚠️ Partial |
| 8 | **Capture Repeated Workflows as Skills** | *"If a prompt pattern is used repeatedly, capture it as a Skill."* | workflows/ = basic skills (code-review, release). Antigravity: `.agents/skills/` SKILL.md format. OpenCode: `~/.agents/skills/` separate system | ⚠️ Partial |
| 9 | **Automate Stable Workflows** | Skills + schedule/trigger = automation. *"Skill = how, Automation = when."* | Not yet implemented. Future: `.ai-sync/automations/` or CI hooks | ❌ Not done |
| 10 | **Session Management** | Separate session per task, avoid overly long sessions, compress periodically, new sessions for branch explorations | HANDOFF.md = session handoff. TASKS.md = task tracking. Multi-agent: OpenCode subagents, Antigravity personas | ✅ Done |

### The Three Context Types (Principle 5)

Z.AI identifies 3 context types every coding agent depends on:

```
┌─────────────────────────────────────────────────┐
│ Task Context                                      │
│   The current prompt and user input               │
│   → Lives in the conversation                     │
├─────────────────────────────────────────────────┤
│ Project Context                                   │
│   Repository structure, engineering rules          │
│   → CONTEXT.md + RULES.md (version-controlled)    │
├─────────────────────────────────────────────────┤
│ Environment Context                               │
│   Tools, permissions, execution environment        │
│   → Platform-specific (OpenCode/Antigravity)       │
│   → Determines WHAT agent can do, HOW FAR it goes │
└─────────────────────────────────────────────────┘
```

When an agent "doesn't understand" or makes mistakes, the root cause is usually **Environment Context** (missing permissions, wrong directory, can't run commands) — not model capability.

### The Full Development Loop (Principle 6)

Both platforms enforce this 5-step loop via RULES.md:

```
1. Implement code changes
   ↓
2. Write or update tests
   ↓
3. Run test suite (pytest tests/ -v)
   ↓
4. Run code checks (ruff, npm run lint, npm run build)
   ↓
5. Review code changes (2-Pass Review Process)
```

> *"Shift from code generator to execution node within the development loop."*

### Gaps & Future Enhancements

**MCP Integration (Principle 7)** — Both platforms support MCP but `.ai-sync/` does not yet define a shared MCP configuration. Each platform configures MCP independently. To improve: add `.ai-sync/mcp/` with shared server definitions that sync.py translates to each platform's format.

**Skills Library (Principle 8)** — Workflows are basic skills. Full skill system would include:
- `.ai-sync/skills/` with SKILL.md format (YAML frontmatter + instructions)
- sync.py copies to `.agents/skills/` for Antigravity
- OpenCode skills remain at `~/.agents/skills/` (user-level, not project-level)

**Automation (Principle 9)** — Not yet implemented. When `.ai-sync/` matures:
- `.ai-sync/automations/` with trigger definitions (schedule, event-based)
- CI hooks to auto-run workflows (e.g., code review on PR, release notes on tag)
- Each platform implements automation differently — sync.py generates platform-specific configs

## File Descriptions

| File | Purpose | Editable |
|------|---------|----------|
| `CONTEXT.md` | Project overview, tech stack, architecture, constraints | ✅ Yes |
| `RULES.md` | Shared coding rules applied to both platforms | ✅ Yes |
| `MEMORY.md` | Learned lessons from past sessions (episodic memory) | ✅ Yes |
| `TASKS.md` | Active task tracking visible to both tools | ✅ Yes |
| `HANDOFF.md` | Session context transfer between tools | ✅ Yes |
| `extensions/opencode.md` | OpenCode-specific rules (subagent delegation, lsp tools) | ✅ Yes |
| `extensions/antigravity.md` | Antigravity-specific rules (agent personas, terminal policies) | ✅ Yes |
| `workflows/*.md` | Shared step-by-step procedures | ✅ Yes |
| `sync.py` | Sync script (generates platform configs) | ✅ Yes |
| `AGENTS.md` | **AUTO-GENERATED** for OpenCode | ❌ No — run sync.py |
| `.agents/rules/project-rules.md` | **AUTO-GENERATED** shared rules for Antigravity | ❌ No — run sync.py |
| `.agents/rules/platform-antigravity.md` | **AUTO-GENERATED** platform rules for Antigravity | ❌ No — run sync.py |

## When to Run sync.py

- **After editing** any file in `.ai-sync/`
- **Before starting** a session with either tool (if unsure about sync state)
- **In CI** (optional) — `python .ai-sync/sync.py --check` to verify configs are current

## Memory Architecture

Based on Z.AI's *Memory Mechanism for Coding Agents* (`docs.z.ai/devpack/resources/memory-mechanism`) — a generic framework applicable to all coding agents. Both OpenCode and Antigravity benefit from these patterns.

### 5 Memory Types

Z.AI defines 5 memory types for coding agents:

| Type | Description | `.ai-sync/` Location | Platform Mechanism |
|------|-------------|---------------------|--------------------|
| **Session** | Current task context — conversation history, tool outputs, execution plan | `HANDOFF.md` | OpenCode: context window. Antigravity: agent history |
| **Project** | Long-lived codebase info — architecture, coding standards, build commands | `CONTEXT.md` + `RULES.md` | OpenCode: `AGENTS.md`. Antigravity: `.agents/rules/` |
| **Semantic** | Factual knowledge, API docs, language rules — implemented via RAG | Not in `.ai-sync/` (use platform tools) | OpenCode: librarian + Context7. Antigravity: Google Search |
| **Episodic** | Past experiences — bug fixes, root causes, debugging strategies that worked | `MEMORY.md` | Both platforms: auto memory |
| **Procedural** | Step-by-step workflows for completing tasks | `workflows/*.md` | OpenCode: loaded via AGENTS.md. Antigravity: `/workflow-name` commands |

### Memory Flow

Every session follows this 3-step cycle (standard pattern from LangGraph, AutoGPT, Devin):

```
┌─────────────────┐     ┌─────────────────────┐     ┌──────────────────┐
│ 1. Retrieve      │ ──→ │ 2. Context Assembly  │ ──→ │ 3. Memory Update │
│ Read HANDOFF.md  │     │ sync.py generates    │     │ Write to         │
│ Read TASKS.md    │     │ AGENTS.md +          │     │ MEMORY.md,       │
│ Read MEMORY.md   │     │ .agents/rules/       │     │ HANDOFF.md,      │
│ Read RULES.md    │     │ from .ai-sync/ files │     │ TASKS.md         │
└─────────────────┘     └─────────────────────┘     └──────────────────┘
```

**Rule**: Agent retrieves memory before starting, updates memory after completing. Do not rely on conversation alone to preserve rules — write long-term instructions into `.md` files.

### Memory Separation Principle

**NEVER mix instruction and learning memory in the same section.** Mixing them causes behavior drift over time — experience-driven notes gradually pollute the system's core rules.

| Memory Kind | Location | Written By | Characteristics |
|-------------|----------|------------|-----------------|
| **Instruction** | `RULES.md` | Human | Rules, policies, behavioral constraints. Stable and predictable. Rarely changes. |
| **Learning** | `MEMORY.md` | Agent | Experience, preferences, failed attempts, takeaways. Grows and improves over time. |

### Layered Memory Scoping

Memory is organized by scope — *"who owns it, who shares it, and who it applies to"*:

| Scope | Location | Owner | `.ai-sync/` Status |
|-------|----------|-------|--------------------|
| **Organization** | Shared config / MDM / Ansible | IT/DevOps | ✅ Not needed (solo dev) |
| **Project** | `.ai-sync/RULES.md` (version-controlled) | Team | ✅ Done |
| **User** | `~/.opencode/`, `~/.gemini/GEMINI.md` | Individual | ✅ Platform-native |
| **Local** | `.gitignore`-d files | Machine-specific | ❌ Gap — see below |
| **Role/Subagent** | Subagent-specific memory | Specialized agent | ⚠️ Partial — see below |

### Episodic Memory Format

MEMORY.md entries should follow a structured format for consistency:

```markdown
### [Date] Short Description

**Problem**: What went wrong or what was discovered
**Root Cause**: Why it happened
**Solution**: What fixed it or what was learned
**Prevention**: How to avoid it in the future (optional)
```

Example:
```markdown
### 2025-04-17 Gemini @path/to/import Claim

**Problem**: Gemini-3.1 Pro claimed @path/to/import works in OpenCode AGENTS.md
**Root Cause**: Z.AI docs use Claude Code as reference example, Gemini generalized incorrectly
**Solution**: Verified against actual docs — @path/to/import is Claude Code-only feature
**Prevention**: Always verify platform-specific claims against official docs, not AI analysis
```

### Modular Rules Pattern

Keep the main memory file focused on **global shared context** (project background, high-level architecture). Split specialized rules into separate files, one per topic:

```
.ai-sync/
├── RULES.md                # Global shared rules (keep under 200 lines)
├── workflows/
│   ├── code-review.md      # Review procedure only
│   └── release.md          # Release procedure only
└── extensions/
    ├── opencode.md         # OpenCode-specific only
    └── antigravity.md      # Antigravity-specific only
```

**Benefits**: Easier to maintain, load on demand, and collaborate on. Different teams can own different rule files.

**Current state**: RULES.md is monolithic (163 lines). For larger projects, consider splitting into:
- `rules/code-style.md` — formatting, naming conventions
- `rules/testing.md` — test requirements, coverage rules
- `rules/security.md` — security constraints, forbidden patterns
- `rules/review.md` — review process, evidence requirements

### Writing Effective Rules

**Prefer concrete, verifiable rules over abstract principles.**

❌ **Vague** (agent has too much room for interpretation):
- "Keep the code clean"
- "Write good tests"
- "Be mindful of API design"

✅ **Concrete** (agent can check and execute):
- "Use **2-space indentation** in all TypeScript files"
- "Run `pytest tests/ -v` after modifying business logic"
- "Place all API handlers under `routes_*.py`"
- "Keep files **under 300 lines**; split larger ones into modules"

**Guidelines:**
- Keep instructions concise and explicit
- Keep rules consistent with one another
- Keep the main memory file **under 200 lines**
- Use Markdown headings and lists for readability
- Phrase requirements as rules that can be **checked and executed**

### Memory Gaps & Future Enhancements

**Local Memory Layer** — Z.AI recommends a `local.md` for machine-specific preferences that should not be committed to git (personal test accounts, local dev ports, temporary mock endpoints). To add:
- `.ai-sync/local.md` (added to `.gitignore`)
- Allows individual work without polluting team-shared memory

**Subagent/Role-Specific Memory** — Different subagents should maintain their own memory scopes:
- Testing agent remembers test commands, CI behavior, assertion style
- Refactoring agent remembers module boundaries, restricted dependencies
- Documentation agent remembers glossary, templates, audience style
- Currently: OpenCode subagents have session-specific context, no persistent per-role memory

**Cross-Repo Rule Packages** — Z.AI recommends reusable rule packages for shared conventions across repositories (e.g., `company-security-rules`, `python-testing-rules`). To add:
- `.ai-sync/templates/` with shared rule templates
- sync.py `--template` flag to import from a central location
- Each project references only the rule modules it needs

## Cross-Tool Workflow

### Starting a Session
1. Read `HANDOFF.md` for context from previous session
2. Read `TASKS.md` for active tasks
3. Read `MEMORY.md` for relevant lessons
4. Proceed with work, updating files as needed

### Ending a Session
1. Update `HANDOFF.md` with session summary
2. Update `TASKS.md` with task status changes
3. If learned new lessons → add to `MEMORY.md`
4. If rules changed → update `RULES.md` → run `sync.py`

### Switching Tools (OpenCode ↔ Antigravity)
1. End session in current tool (update HANDOFF.md)
2. Start session in other tool (read HANDOFF.md)
3. Both tools see the same RULES, MEMORY, and TASKS
4. No context lost in transition

## Adding to a New Project

```bash
# 1. Copy the entire .ai-sync/ folder to new project root
cp -r .ai-sync/ /path/to/new-project/

# 2. Edit CONTEXT.md with new project info
# 3. Edit RULES.md with new project rules (or keep shared rules)
# 4. Clear MEMORY.md (new project = no lessons yet)
# 5. Clear TASKS.md (no active tasks)
# 6. Run sync.py
python .ai-sync/sync.py

# 7. Commit .ai-sync/ to git (platform configs are auto-generated, add to .gitignore if desired)
```

## Git Integration

**Recommended `.gitignore` additions** (optional — if you want to enforce sync.py usage):
```gitignore
# Auto-generated platform configs — edit .ai-sync/ instead
# AGENTS.md
# .agents/rules/project-rules.md
# .agents/workflows/
```

**Or** commit generated files too (so CI and other tools can use them without running sync.py).

## FAQ

**Q: What if I edit AGENTS.md directly?**
A: Your changes will be OVERWRITTEN next time sync.py runs. Always edit .ai-sync/ files.

**Q: What if I only use one tool (OpenCode or Antigravity)?**
A: The protocol still works — just ignore the other platform's generated files. You still benefit from organized memory, tasks, and handoff files.

**Q: Can I add more platforms (e.g., Cursor, Claude Code)?**
A: Yes! Add a new `extensions/cursor.md` file and update `sync.py` to generate the Cursor config.

**Q: Who writes to HANDOFF.md?**
A: Whatever tool was last active. OpenCode and Antigravity take turns writing their session context.

**Q: What about conflicting edits to TASKS.md?**
A: Both tools append to the file. If both are active simultaneously, use git to resolve conflicts (rare case).
