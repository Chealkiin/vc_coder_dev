
# Agent Group Standards & Starter Spec (v0–prod)

**Purpose**: One living document that keeps the repo clean, consistent, and production‑grade while we bootstrap an agent group that executes *sequential* tasks against GitHub using GPT‑5 (planning) and GPT‑5‑Codex (coding). Postgres from day one. Clean, modular, dependency‑injected.

---

## 1) Architecture at a glance

```
[Vercel Chat UI/CLI]
        │
        ▼
  [Gateway/API] ──────► [Orchestrator] ── state machine (per step)
                           │   │   │
       ┌───────────────────┘   │   └──────────────────────────┐
       ▼                       ▼                              ▼
 [Planner (GPT‑5)]     [Sub‑Planner (GPT‑5)]           [Coder (GPT‑5‑Codex)]
   - normalize             - produce WorkOrder              - return unified diff
   - (future) enrich       - scope & constraints            - no deps unless allowed

       ▼                       ▼                              ▼
                 [Validator hooks] ── fatal/warn surface
                           │
                           ▼
                    [GitHub Integrator]
                     - branch/commit/PR
                     - status comments
                     - (manual merge by default)

       ▼
                [Postgres] (runs, steps, artifacts,
                 validation_reports, pr_bindings, events)
```

### 1.1 Core patterns we are carrying over
- **BaseAgent + LifecycleMixin + LoggingMixin**: prepare → build → execute → postprocess with consistent metadata and error handling.
- **Contracts + Registry**: strict Pydantic v2 models, versioned, with normalization transforms defined per contract and logged as artifacts.
- **Output Handler pipeline**: validates & routes normalized results (esp. `unified-diff`) and records metrics/artifacts.
- **Dependency Injection (DI)**: agents receive dependencies (store, github, memory, logger, config) via constructors; registries are *read‑only metadata*, not service locators.

---

## 2) Repository & project standards

### 2.1 Layout
```
backend/
  agents/
    orchestrator/
    planner/
    sub_planner/
    coder/
    github/
    validator/
    shared/               # base_agent, lifecycle_mixin, logging_mixin, errors
  core/
    contracts/            # pydantic models + registry + mapping tables
    events/               # types and helpers
    models/               # SQLAlchemy models
    store/                # Postgres repositories + session mgmt
  api/
    server.py             # minimal HTTP API (POST /runs etc.)
  tools/
    codex_client.py
    github_client.py
  tests/
    unit/
    integration/
README.md
```

### 2.2 Languages & tooling
- **Python (backend)**: `black`, `isort`, `ruff`, `mypy --strict`, SQLAlchemy 2.x, Psycopg 3, Alembic.
- **TypeScript (UI/bridge later)**: `strict`, ESLint, Prettier, Zod for runtime validation.
- All public functions **typed**; docstrings **Google style**.
- No `print()` in prod paths. Structured JSON logs only.

### 2.3 Naming
- Files/dirs: `snake_case` (py), `kebab-case` (ts files).
- Classes: `PascalCase`. Functions/vars: `snake_case` (py), `camelCase` (ts).
- Branches: `feat/<topic>-<id>`, `fix/...`, `chore/...`.
- Commits: **Conventional Commits**; one logical change per commit.

### 2.4 Comments & TODOs
- Explain **why**, not what. `# TODO(name, YYYY‑MM‑DD): ...` with link.

---

## 3) Contracts & registries (production rules)

- **Pydantic v2**, `extra="forbid"`, `model_config` includes version & schema id.
- **Normalization transforms** are defined per contract (e.g., `depends_on → dependencies`) and are **logged** into an artifact alongside the final payload.
- **Registry** discovers contract classes (decorators or explicit table), caches them at startup; no runtime scanning loops.
- **Mapping table**: `step_type → output_type` with aliases as data. Single source of truth.

### 3.1 Canonical WorkOrder (Sub‑planner → Coder)
```json
{
  "work_order_id": "uuid",
  "title": "Implement Settings route",
  "objective": "Create /settings with nav placeholders",
  "constraints": ["no global refactors", "return unified diff"],
  "acceptance_criteria": ["route exists","nav items present","validators pass"],
  "context_files": ["README.md","frontend/src/app/router.tsx"],
  "return_format": "unified-diff"
}
```

### 3.2 CoderResult
```json
{"work_order_id":"uuid","diff":"diff --git a/...","notes":"Added route and placeholders"}
```

### 3.3 ValidationReport (fatal surface)
```json
{"step_id":"uuid","fatal":[{"code":"PY_SYNTAX","file":"...","line":42,"msg":"..."}],
 "warnings":[{"code":"STYLE_NAMING","file":"...","msg":"..."}],
 "metrics":{"lint_errors":0,"tests_run":12,"tests_failed":0}}
```

---

## 4) Prompt & message standards
- Agent prompts are **deterministic templates**; no free‑form chatter.
- Coders must return **`diff --git` unified diffs**. If a tool returns files, they must be absolute repo‑relative paths (fallback path, discouraged).
- Sub‑planner is the **scope police**: narrow impact, set constraints, forbid dependencies unless allowed.

---

## 5) Execution pipeline (v0 sequence)

**States**: `QUEUED → PLANNED → EXECUTING → VALIDATING → COMMITTING → PR_UPDATED → (MERGED|PAUSED|FAILED)`

1. Orchestrator normalizes user steps.
2. Planner (v0 pass‑through) → Sub‑planner creates a **WorkOrder**.
3. Coder (GPT‑5‑Codex) returns **unified diff**.
4. Validator runs on **changed files only**, produces **fatal/warn** surface.
5. If fatal → **PAUSED**, record artifacts & recovery tip; else commit + update PR.
6. Merge is **manual** by default; proceed to next step after commit (or merge, if enabled).

**Diff size guard (configurable):**
- Defaults: `max_changed_lines = 5000`, `max_new_files = 50`.  
- Behavior: if exceeded → **PAUSED** with reason; operator may toggle off or raise limits and **retry**.
- Feature flag: `SIZE_GUARDS_ENABLED=true|false` (off → proceed but still log metrics).

---

## 6) Validation & quality gates
- Fast checks only in v0: Python (`ruff`, `mypy` on changed), JS/TS (`eslint`, `tsc` on changed).
- Any **fatal** blocks progress (PAUSED). **Warnings** annotate PR and continue.
- Future: **QualityAgent** for improvements (not a gatekeeper).

---

## 7) GitHub integrator
- **GitHub App** (least privilege): contents read/write, pulls, optional checks.
- Create branch from base if absent; `git apply` patch; commit; open/update PR.
- Update PR body per step with summary + validator metrics.
- Final merge: **manual** (toggle auto‑merge later).

---

## 8) Persistence (Postgres only)
- Tables: `runs`, `steps`, `artifacts`, `validation_reports`, `pr_bindings`, `events`.
- UUIDs for primary keys (except `events.id` bigserial). Strict FKs, unique `(run_id, idx)` on steps.
- Alembic migrations committed with each schema change. No SQLite anywhere.

**DDL (concise)**
```sql
create table runs (
  id uuid primary key,
  repo text not null,
  base_ref text not null,
  branch_ref text not null,
  status text not null check (status in ('queued','running','paused','failed','completed')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create table steps (
  id uuid primary key,
  run_id uuid not null references runs(id) on delete cascade,
  idx int not null,
  title text not null,
  body text not null,
  status text not null check (status in ('queued','planned','executing','validating','committing','pr_updated','merged','paused','failed')),
  acceptance_criteria jsonb,
  plan_md text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(run_id, idx)
);
create table artifacts (
  id uuid primary key,
  step_id uuid not null references steps(id) on delete cascade,
  kind text not null check (kind in ('diff','doc','log','blob','rej')),
  uri text not null,
  meta jsonb default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create table validation_reports (
  id uuid primary key,
  step_id uuid not null references steps(id) on delete cascade,
  report jsonb not null,
  fatal_count int not null default 0,
  warnings_count int not null default 0,
  created_at timestamptz not null default now()
);
create table pr_bindings (
  run_id uuid primary key references runs(id) on delete cascade,
  pr_number int not null,
  pr_url text not null
);
create table events (
  id bigserial primary key,
  run_id uuid not null references runs(id) on delete cascade,
  step_id uuid null references steps(id) on delete cascade,
  type text not null,
  payload jsonb not null default '{}'::jsonb,
  ts timestamptz not null default now()
);
```

---

## 9) Logging & observability
- **Stdlib JSON logging** only; fields: `ts`, `level`, `run_id`, `step_id`, `agent`, `phase`, `message`, `meta`.
- Each lifecycle phase emits start/finish with durations.
- Events also persisted to `events` table and streamed to UI.
- Optional (future): OpenTelemetry spans/traces.

---

## 10) Secrets & config (2025 best practice)
- **Workload identity / OIDC** for CI to cloud (short‑lived tokens). No long‑lived PATs in CI.
- **Managed secret stores** (cloud Secret Manager) or **Vault / 1Password Connect** for server workloads.
- **KMS‑backed encryption** for config at rest; never commit secrets; enable secret scanning.
- For Vercel: use **encrypted environment variables**, scoped per environment, rotation policy documented.
- Redaction at logger boundary; never echo tokens in PRs or artifacts.

---

## 11) Future features (design now, implement later)
- **Context enrichment** (planner): memory/codegraph retrieval with retries, caching, token budget, and telemetry.
- **DocsAgent**: PR descriptions, ADRs, changelog.
- **QualityAgent**: post‑diff hardening (TODOs/placeholders, tests), non‑blocking in v0.
- **Concurrency**: multiple sub‑planners/coders with file locking/blackboards.

---

## 12) Implementation order
1) Postgres models, repositories, migrations.  
2) Contracts package (Pydantic v2) + registry + mapping tables + transform logging.  
3) BaseAgent + Lifecycle + Logging mixins (timeouts/retries/cancellation).  
4) Output/Normalization pipeline (unified diff enforcement, artifacts).  
5) GitHub integrator (App auth, PR body updater).  
6) Sub‑planner (scope/constraints), Coder adapter (Codex API).  
7) Orchestrator state machine + event stream (pause/resume/retry).  
8) Validator hooks (changed‑files only).  
9) Minimal CLI & gateway; CI with linters/types/tests.

---

## 13) Decision log (locked)
- **DB**: Postgres only (no SQLite).  
- **Auth**: GitHub App; manual merge default.  
- **DI**: manual wiring + small factories (no hidden globals).  
- **Contracts**: Pydantic v2, versioned, transforms logged.  
- **Logging**: stdlib JSON; traces optional later.  
- **Guards**: max 5000 changed lines / 50 new files; feature flag to disable.  
- **Coders**: must return `diff --git` unified diffs.
