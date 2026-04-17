# OpenCode-Specific Extensions

> **Appended to AGENTS.md when running `python .ai-sync/sync.py`.**
> Rules that only apply to OpenCode (GLM-5.1 + Sisyphus agent system).

---

## AGENT SYSTEM (OpenCode Only)

### Subagent Delegation
- `explore` — Contextual codebase grep (FREE, always background)
- `librarian` — External docs/reference search (CHEAP, always background)
- `oracle` — High-IQ read-only consultant (EXPENSIVE, use sparingly)
- `metis` — Pre-planning ambiguity analysis (EXPENSIVE)
- `momus` — Plan quality reviewer (EXPENSIVE)

### Background Task Rules
- Explore/Librarian → ALWAYS `run_in_background=true`, ALWAYS parallel
- NEVER poll `background_output` before receiving system notification
- NEVER cancel Oracle tasks — wait for completion
- Collect ALL background results before delivering final answer

### Review Tools
- `lsp_diagnostics` — Check for errors on changed files
- `lsp_find_references` — Trace full dependency chain
- `ast_grep_search` — Pattern-based code search

### Pre-Push Self-Review (OpenCode Pattern)
1. Fire 2+ `explore` agents in parallel to audit code
2. Use `lsp_diagnostics` on ALL changed files
3. Run `pytest tests/ -q` for backend changes
4. Run `npm run build && npm run lint` for frontend changes

## BEFORE EVERY COMMIT (OpenCode-Specific)

- `lsp_diagnostics` shows no NEW errors on changed Python files
