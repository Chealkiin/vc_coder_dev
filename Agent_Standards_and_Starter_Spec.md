# Agent Group Standards & Starter Spec (v0-min)

**Purpose:** keep the repo clean, consistent, and resilient while we bootstrap an agent group that (for now) runs tasks *sequentially* via GitHub and GPT-5-Codex. This is the single living doc we’ll expand over time.

---

## 1) Guiding Principles
- **Clarity over cleverness.** Prefer boring, readable solutions.
- **Small surface, explicit contracts.** Every agent input/output is a typed object.
- **Deterministic steps.** Each step is idempotent; re-running a step never double-commits.
- **PR-only safety.** No direct pushes to default. All changes via PR with checks.
- **Tight prompts, tight diffs.** Sub-planners must constrain coder scope; avoid repo-wide edits.
- **No drift.** Conventions are enforced by tooling. Failing checks block merges.

---

## 2) Repository & Project Standards

### 2.1 Repo Layout (service-first; adapt as we grow)
```
backend/
  agents/
    orchestrator/
    planner/
    sub_planner/
    coder/
    github/
    validator/
  core/
    contracts/        # JSON/Type/Schema definitions
    events/
    models/           # Run, Step, Artifact, ValidationReport
    store/            # SQLite/PG adapters
  api/
    server.py         # minimal HTTP API (POST /runs etc.)
  tools/
    codex_client.py
    github_client.py
  tests/
    unit/
    integration/
README.md
```

### 2.2 Languages & Tooling
- **Python (backend/agents)**  
  - Formatting: `black`, imports: `isort`, lint: `ruff`, types: `mypy --strict`.
  - Docstrings: Google-style. Type annotate all public functions.
  - Logging: structured (JSON). No print() in production paths.
  - Exceptions: raise specific errors; never swallow without logging context.
- **TypeScript (UI or Vercel bridge when added)**  
  - `tsconfig` strict true. ESLint + Prettier. Runtime validation with Zod.
  - Avoid `any`. Use discriminated unions for agent message types.

### 2.3 Naming Conventions
- **Files/dirs:** `snake_case` for Python, `kebab-case` for TS/JS files.
- **Classes:** `PascalCase`. **Functions/vars:** `snake_case` (py), `camelCase` (ts).
- **Branches:** `feat/<short-topic>-<ticket|date>`, `fix/...`, `chore/...`.
- **Commits:** Conventional Commits (`feat: ...`, `fix: ...`, `docs: ...`). One logical change per commit.

### 2.4 Comments & TODOs
- Explain *why*, not *what*. Keep comments close to non-obvious code.
- `# TODO(username, date): ...` and link issue/ticket if applicable.
- Prohibit long commented-out blocks; delete dead code.

### 2.5 Tests & Quality Gates
- **Unit first.** Minimum coverage gate 70% (raise later).
- Lint + typecheck must pass. Run quick language linters on only changed files if needed.
- Validator emits a **fatal-only** summary for gating (see §6).

### 2.6 Secrets & Config
- No secrets in code or logs. Use env vars + local .env (gitignored).
- Redact sensitive tokens in agent logs and PR comments.

---

## 3) AI Prompt & Message Standards

### 3.1 General
- Prompts from agents must be **deterministic templates** with explicit fields. Avoid free-form chatter.
- For multi-line or complex prompts sent to tools, prefer **codebox blocks** where required by the target UI. Avoid triple backticks inside the **prompt text itself** when that breaks the consumer.

### 3.2 Canonical Step Message (Planner → Sub-planner → Coder)
```json
{
  "step_id": "run-123.step-02",
  "repo": "org/repo",
  "base_ref": "main",
  "branch_ref": "feature/run-123",
  "title": "Implement Settings page scaffold",
  "objective": "Add /settings route with nav placeholders",
  "constraints": [
    "Scope limited to /settings, no global refactors",
    "Return a unified diff (diff --git) with correct paths"
  ],
  "acceptance_criteria": [
    "Route exists and loads",
    "Nav shows Profile/Billing/Teams/Danger Zone",
    "Build passes validators"
  ],
  "context_files": ["README.md", "frontend/src/app/router.tsx"],
  "return_format": "unified-diff"
}
```

### 3.3 Diff Expectations
- Prefer `diff --git` unified diffs. If the tool returns files, include absolute repo-relative paths. No ambiguous patches.

---

## 4) Minimal Agent Roles (v0)

### 4.1 Orchestrator
- Accepts a **sequence** of tasks.
- Manages run state, step queue, pause/resume/retry.
- Publishes step lifecycle events: `planned`, `executing`, `validated`, `committed`, `merged`, `failed`.

### 4.2 Planner (GPT‑5)
- v0: pass-through to sub-planner with minimal normalization.
- Future: take prompt/high level plan and turn into full design and development plan; make executive decisions when underspecified; call doc/analysis tools to generate plans; various other tools.

### 4.3 Sub‑Planner (GPT‑5)
- Expand each step into a constrained work order:
  - objective, acceptance_criteria, constraints, impacted files, return_format.
- Sequence the steps correctly (may be identical to input order in v0).

### 4.4 Coder (GPT‑5‑Codex)
- Execute the work order strictly within constraints.
- Return unified diff plus brief notes.
- Avoid creating new dependencies unless explicitly allowed.

### 4.5 GitHub Integrator
- Create branch from base if absent; apply patch; commit; open/update PR.
- Status check summary comment including validator results.
- Merge policy: **manual merge by default** (auto-merge later).

### 4.6 Validator (hook)
- Run fast checks (linters, syntax, minimal tests) on changed files.
- Emit `ValidationReport` with `fatal` and `warnings` aligned to a shared schema.

---

## 5) Contracts (v0)

### 5.1 Work Order (Sub‑planner → Coder)
```json
{
  "work_order_id": "run-123.step-02",
  "title": "Implement Settings route",
  "objective": "Create /settings with nav placeholders",
  "constraints": ["no global refactors", "return unified diff"],
  "acceptance_criteria": [
    "Route exists",
    "Nav items present",
    "Validators pass"
  ],
  "context_files": ["README.md", "frontend/src/app/router.tsx"],
  "return_format": "unified-diff"
}
```

### 5.2 Coder Result
```json
{
  "work_order_id": "run-123.step-02",
  "result": {
    "diff": "diff --git a/...",
    "notes": "Added route and placeholders"
  }
}
```

### 5.3 ValidationReport (fatal-only surface)
```json
{
  "step_id": "run-123.step-02",
  "fatal": [
    {"code": "PY_SYNTAX", "file": "backend/api/server.py", "line": 42, "msg": "SyntaxError: ..."}
  ],
  "warnings": [
    {"code": "STYLE_NAMING", "file": "frontend/src/app/router.tsx", "msg": "CamelCase component name expected"}
  ],
  "metrics": {"lint_errors": 0, "tests_run": 12, "tests_failed": 0}
}
```

---

## 6) Step Execution Outline (v0)

1. **Receive tasks** (CLI or basic GUI). Normalize to Steps.
2. **For each step** in order:
   1. Planner forwards to Sub‑planner to produce Work Order.
   2. Coder (GPT‑5‑Codex) executes with repo context → returns diff.
   3. Validator runs on changed files → produce ValidationReport.
   4. If **fatal issues** → pause run (operator fixes or retry).
   5. If pass → GitHub Integrator commits to `feature/<run>` and updates/creates PR.
   6. Optionally merge PR (manual default) or keep updating the same PR per step.
3. **Proceed** to next step after commit (and merge, if policy requires).

Pseudo‑control:
```text
for step in steps:
  work = sub_planner.plan(step)
  result = coder.execute(work)
  report = validator.check(result.diff)
  if report.fatal: pause_and_wait()
  else:
    commit_pr(result.diff)
    maybe_merge()
continue
```

---

## 7) Coding Standards (Concrete Rules)

### 7.1 Python
- `black`, `isort`, `ruff` (CI-enforced). `mypy --strict` on agents/core.
- Docstrings: Google style. Example:
```
def apply_patch(repo: Path, diff: str) -> None:
    """Apply a unified diff to a git repo.

    Args:
        repo: Repository root path.
        diff: Unified diff text (diff --git).
    Raises:
        PatchApplyError: If apply fails.
    """
```
- Imports: stdlib, third-party, local — in that order; no wildcard imports.
- Dependency hygiene: pin versions; prefer stdlib; avoid heavy libs unless justified.

### 7.2 TypeScript
- `strict` true; no `any`. ESLint/Prettier in CI.
- Types for all HTTP contracts. Validate with Zod at runtime.
- Avoid stateful singletons; favor explicit dependency injection in constructors.

### 7.3 Logging
- Structured JSON: `level`, `ts`, `run_id`, `step_id`, `agent`, `message`, `meta`.
- No secrets; redact tokens and file contents where necessary.

### 7.4 Error Handling
- Raise/return typed errors with actionable messages.
- Never catch-and-drop. Always include context (run_id, step_id, file).

### 7.5 PR Template (v0)
```
## Summary
<what/why>

## Changes
- ...

## Validation
- [ ] Lint/typecheck green
- [ ] Unit tests pass
- [ ] Acceptance criteria met

## Notes
<risk, follow-ups>
```

---

## 8) Basic “What to Build First”
1. **Core models & store**: Run, Step, Artifact, ValidationReport (SQLite).
2. **Contracts**: WorkOrder, CoderResult, ValidationReport schemas.
3. **GitHub integrator**: branch/create PR/apply patch (PAT ok for now).
4. **Validator stub**: Python + JS quick linters; fatal-only surface.
5. **Sub‑planner**: convert a Step → WorkOrder with strict constraints.
6. **Coder adapter**: call GPT‑5‑Codex; enforce unified diff return.
7. **Orchestrator**: sequential loop with pause/resume/retry.
8. **CLI**: `runs start --repo org/repo --base main --steps file.steps`.

---

## 9) Future Additions (brief)
- **QualityAgent**: review diffs; fix TODOs/placeholders; harden code.
- **DocsAgent**: PR descriptions, ADRs, changelog.
- **Memory/Context**: vector summaries per step; retrieval for next steps.
- **Concurrency**: multiple sub‑planners/coders with locks and blackboards.

---

## 10) Decision Log (placeholders to fill as we agree)
- GitHub auth: PAT vs App → _TBD_
- Merge policy: manual vs auto at end → _TBD_
- DB: SQLite now, PG later → _TBD_
- Validator minimum set → _TBD_

---

## 11) Observability
- Emit lifecycle events per step. Persist logs and artifacts.
- Attach run/step IDs to PR comments for traceability.
