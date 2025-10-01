# Run and Test Coding Agents – First Milestone

## A. Overview
The first milestone wires the Coding Agents end-to-end using in-memory fakes so contributors can iterate on orchestration logic without external services. The orchestrator sequences planning, coding, validation, and GitHub summarisation to generate deterministic artifacts for every step while publishing lifecycle events for observability.【F:scripts/demo_happy_path.py†L1-L53】【F:backend/agents/orchestrator/wiring_demo.py†L1-L96】

Key components:
- **OrchestratorAgent** – coordinates run and step state transitions, persists artifacts, and emits lifecycle events.【F:backend/agents/orchestrator/orchestrator_agent.py†L25-L226】
- **Planner adapters** – planner passthrough plus sub-planner fake that normalises step metadata for the coder.【F:backend/agents/orchestrator/wiring_demo.py†L37-L76】
- **CoderAdapterFake** – returns a canned diff and notes to represent DeveloperAgent output.【F:backend/agents/coder/coder_adapter_fake.py†L1-L53】
- **FakeValidator** – records metrics and warnings without blocking progress, validating the ValidatorAgent contract.【F:backend/agents/validator/fake_validator.py†L1-L55】
- **In-memory repos & events publisher** – capture run/step records, diff artifacts, validation reports, and lifecycle events for inspection.【F:core/store/memory_repos.py†L1-L210】【F:core/events/capture.py†L1-L78】

## B. Prerequisites
| Tool | macOS / Linux | Windows (PowerShell) |
| --- | --- | --- |
| **Python 3.11** | `brew install python@3.11` or `pyenv install 3.11.8` then `pyenv local 3.11.8` | `winget install Python.Python.3.11` or `pyenv-win install 3.11.8`
| **pip** | Bundled with Python; upgrade via `python3.11 -m pip install --upgrade pip` | `py -3.11 -m pip install --upgrade pip`
| **Git** | `brew install git` or use distro package manager | `winget install Git.Git`
| **Make (optional)** | Included on macOS with Xcode CLT or install via package manager | Install `choco install make` or use the explicit commands listed below

Recommended Python version manager: [pyenv](https://github.com/pyenv/pyenv) / [pyenv-win](https://github.com/pyenv-win/pyenv-win) to guarantee `3.11` required by `pyproject.toml` (`requires-python = ">=3.11"`).【F:pyproject.toml†L13-L16】

Optional container: no devcontainer is provided; use local tooling or add Docker as needed.

## C. Quick start
1. **Clone the repository**
   - macOS / Linux
     ```bash
     git clone https://example.com/coding-agents.git
     cd coding-agents
     ```
   - Windows (PowerShell)
     ```powershell
     git clone https://example.com/coding-agents.git
     Set-Location coding-agents
     ```

2. **Create and activate a virtual environment** (explicit commands if `make` is unavailable)
   - macOS / Linux
     ```bash
     python3.11 -m venv .venv
     source .venv/bin/activate
     python -m pip install --upgrade pip
     pip install -e .[dev]
     ```
   - Windows (PowerShell)
     ```powershell
     py -3.11 -m venv .venv
     .\.venv\Scripts\Activate.ps1
     python -m pip install --upgrade pip
     pip install -e .[dev]
     ```

   The editable install pulls the orchestration packages and dev dependencies (`pytest`, `ruff`, `black`, `isort`, `mypy`).【F:pyproject.toml†L18-L35】

3. **One-command bootstrap (optional)**
   - macOS / Linux: `make bootstrap`
   - Windows (PowerShell): `make bootstrap` (if GNU Make is installed) or run the explicit commands above.

Repository layout highlights: `backend/` (agent implementations), `core/` (events & storage primitives), `scripts/` (CLI demos), `tests/` (pytest suites).【F:backend/README.md†L1-L4】【F:scripts/demo_happy_path.py†L1-L58】【F:core/store/memory_repos.py†L1-L210】【F:backend/tests/unit/agents/test_orchestrator_wiring.py†L1-L120】

## D. Configuration
1. Copy the environment example and adjust as needed:
   ```bash
   cp .env.example .env
   ```
   `.env.example` captures non-secret defaults for demo runs: Python version hint, size guard toggle, and repository metadata used by helper scripts.【F:.env.example†L1-L7】

2. The orchestration demo reads configuration via dependency injection rather than environment variables. `build_demo_orchestrator()` seeds `feature_branch` and uses in-memory stores, so no external credentials are required for the first milestone.【F:backend/agents/orchestrator/wiring_demo.py†L64-L95】

3. The only environment variable referenced in the pipeline today is `SIZE_GUARDS_ENABLED`; `scripts/demo_happy_path.py` defaults it to `false` for repeatable runs.【F:scripts/demo_happy_path.py†L31-L34】

4. Optional: If you want to override the canned diff for local experiments, point `CoderAdapterFake` at a different file by instantiating it with `diff_path=Path("path/to/diff")`.【F:backend/agents/coder/coder_adapter_fake.py†L21-L48】

## E. Running the agents
1. **Happy-path demo (console streaming)**
   - macOS / Linux: `python scripts/demo_happy_path.py`
   - Windows (PowerShell): `python scripts/demo_happy_path.py`

   The script wires the orchestrator against fakes, starts a run with two steps, advances each step sequentially, prints lifecycle events, and summarizes stored artifacts.【F:scripts/demo_happy_path.py†L1-L58】 Logs stream to stdout via `InMemoryEventsPublisher`. Artifacts include a diff (`diff` kind) and two doc entries (notes + patch summary) per step.【F:core/events/capture.py†L18-L62】【F:backend/agents/orchestrator/serialization.py†L1-L41】

2. **Export deterministic artifacts to disk**
   - macOS / Linux: `python scripts/export_demo_run.py --output demo_run`
   - Windows (PowerShell): `python scripts/export_demo_run.py --output demo_run`

   The helper script reuses the demo wiring, drains all steps, and writes JSON payloads (`events.json`, `run.json`, `steps.json`, `artifacts.json`, `validation_reports.json`) plus `.patch` files for each diff into the chosen directory.【F:scripts/export_demo_run.py†L1-L104】 Data is normalised with ISO timestamps and enum values for easy inspection.

3. **Makefile shortcuts**
   - `make demo` → runs the streaming demo.
   - `make export-demo` → runs the exporter with default output directory `demo_run/`.
   - `make bootstrap`, `make test`, `make lint`, `make format` wrap the commands above for quick iteration.【F:Makefile†L1-L48】

Artifacts and logs live in memory during the run; use `scripts/export_demo_run.py` when you need persistent copies for debugging or verification.【F:scripts/export_demo_run.py†L39-L85】【F:core/store/memory_repos.py†L209-L274】

## F. Sample task to verify the first milestone
1. **Task input** – two deterministic work orders baked into `scripts/demo_happy_path.DEMO_STEPS`, covering a UI scaffold and matching tests.【F:scripts/demo_happy_path.py†L14-L28】
2. **Execution** – run the exporter so you have files to inspect:
   ```bash
   python scripts/export_demo_run.py --output demo_run
   ```
3. **Expected artifacts**
   - `demo_run/events.json` – chronological lifecycle events for run `run-0001` including `step.planned`, `step.executing`, `step.validated`, `step.committed`, and `run.status_changed` records.【F:core/events/capture.py†L30-L62】
   - `demo_run/artifacts.json` – contains three artifacts per step (`diff`, coder notes doc, patch summary doc) mirroring repository persistence.【F:backend/agents/orchestrator/serialization.py†L1-L41】【F:core/store/memory_repos.py†L209-L274】
   - `demo_run/validation_reports.json` – non-fatal reports with informational warnings produced by `FakeValidator`.【F:backend/agents/validator/fake_validator.py†L18-L55】
   - `demo_run/run-0001-step-*.patch` – unified diffs matching `backend/agents/coder/diffs/demo_patch.txt` to validate DeveloperAgent output.【F:backend/agents/coder/coder_adapter_fake.py†L1-L47】
4. **Quick validation**
   ```bash
   jq '. | length' demo_run/artifacts.json       # expect 6 artifacts
   jq '.[0].kind' demo_run/artifacts.json        # expect "diff"
   jq '.[0].meta.summary.additions' demo_run/artifacts.json
   jq '.[0].report.metrics' demo_run/validation_reports.json
   ```
   On Windows (PowerShell), use `Get-Content demo_run\artifacts.json | ConvertFrom-Json` to inspect equivalent fields.

## G. Testing
- **All tests**: `pytest` (or `make test`). Pytest is configured under `backend/tests` with minimal integration and unit suites.【F:pyproject.toml†L55-L59】
- **Filter suites**: `pytest backend/tests/unit -k orchestrator`.
- **Parallelism**: Install `pytest-xdist` if desired and run `pytest -n auto` (optional, not bundled by default).
- **Coverage**: `pytest --cov=backend --cov=core --cov-report=term-missing` (install `pytest-cov` locally if required).
- **Static checks**: `ruff check backend core scripts tests`, `black --check backend core scripts tests`, `isort --check-only backend core scripts tests`, `mypy backend` (mypy strict mode is configured for backend packages).【F:pyproject.toml†L23-L49】【F:Makefile†L33-L48】

## H. Verification checklist
- [ ] Virtual environment created with Python 3.11 and dependencies installed via `pip install -e .[dev]` or `make bootstrap`.
- [ ] `python scripts/demo_happy_path.py` streams lifecycle events without errors and reports diff/doc artifacts per step.
- [ ] `python scripts/export_demo_run.py --output demo_run` completes and writes JSON + patch files.
- [ ] `demo_run/validation_reports.json` shows zero fatal findings and at least one warning per diff.
- [ ] `demo_run/*.patch` apply cleanly (optional) and match the canned diff from `backend/agents/coder/diffs/demo_patch.txt`.
- [ ] `pytest` succeeds.
- [ ] Optional lint/format commands succeed (Ruff, Black, isort, mypy) when run locally.

## I. Troubleshooting
- **Missing Python 3.11** – install via pyenv/pyenv-win or platform package manager, then re-run `make bootstrap` or the explicit pip commands.【F:pyproject.toml†L13-L16】
- **`ModuleNotFoundError: backend`** – ensure you run scripts from the repo root or use `python -m scripts.demo_happy_path`; helper scripts inject the repo root into `sys.path` automatically.【F:scripts/demo_happy_path.py†L7-L12】【F:scripts/export_demo_run.py†L9-L18】
- **`pip install` build errors** – upgrade pip (`python -m pip install --upgrade pip`) and ensure compiler toolchain is available if optional native extras are added later (current milestone uses pure-Python fakes).
- **Windows path separators** – when referencing generated artifacts use `demo_run\events.json` and `demo_run\run-0001-step-0.patch` in PowerShell commands.
- **Lint/format fail due to missing tools** – confirm dev extras installed (`pip install -e .[dev]`) or run `make bootstrap`.

## J. Make it fast to iterate
- Use the `Makefile` shortcuts for bootstrap, demo runs, artifact export, tests, lint, and format tasks to avoid repeating long commands.【F:Makefile†L1-L48】
- Modify `.env` or pass CLI flags (`--repo`, `--base-ref`, `--output`) to `scripts/export_demo_run.py` for scenario testing without touching agent logic.【F:scripts/export_demo_run.py†L20-L44】
- Generated artifacts from the exporter are deterministic; re-run after changes to diff outputs quickly.

## K. Provenance
Assumptions:
- External APIs are intentionally stubbed for this milestone; no network or credential setup is required.
- Developers have Git and a supported Python toolchain installed locally.

Files created or updated for this guide:
- `docs/RUN_AND_TEST_CODING_AGENTS.md` – this run-and-test playbook.
- `.env.example` – environment defaults for demo runs.【F:.env.example†L1-L7】
- `Makefile` – reproducible bootstrap/run/test/lint shortcuts.【F:Makefile†L1-L48】
- `scripts/export_demo_run.py` – helper CLI that exports demo artifacts for verification.【F:scripts/export_demo_run.py†L1-L104】
