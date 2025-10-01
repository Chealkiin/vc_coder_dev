"""Export artifacts from the happy-path demo run to disk."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.append(str(REPO_ROOT))


from backend.agents.orchestrator.orchestrator_state import StepState
from backend.agents.orchestrator.wiring_demo import DemoOrchestratorContext, build_demo_orchestrator
from scripts.demo_happy_path import DEMO_STEPS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the demo orchestrator and persist outputs to disk")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("demo_run"),
        help="Directory where run artifacts will be stored",
    )
    parser.add_argument("--repo", default="org/demo-repo", help="Repository slug to associate with the run")
    parser.add_argument("--base-ref", default="main", help="Base branch name used for the demo run")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    context = build_demo_orchestrator()
    orchestrator = context.orchestrator

    run_id = orchestrator.start_run(repo=args.repo, base_ref=args.base_ref, steps=list(DEMO_STEPS))
    _drain_steps(context, run_id)

    export_dir = args.output
    export_dir.mkdir(parents=True, exist_ok=True)

    _write_json(export_dir / "events.json", [payload for payload in context.events.iter_payloads()])
    _write_json(export_dir / "run.json", context.run_repo.get_run(run_id))
    _write_json(export_dir / "steps.json", list(context.step_repo.list_steps(run_id)))
    _write_json(export_dir / "artifacts.json", list(context.artifact_repo.all_artifacts()))
    _write_json(export_dir / "validation_reports.json", list(context.report_repo.list_reports(run_id)))

    _export_diffs(export_dir, context.artifact_repo.all_artifacts())

    print(f"Exported demo run '{run_id}' to {export_dir.resolve()}")
    return 0


def _drain_steps(context: DemoOrchestratorContext, run_id: str) -> None:
    while True:
        step_records = list(context.step_repo.list_steps(run_id))
        pending = [record for record in step_records if record.get("state") not in _terminal_states()]
        if not pending:
            break
        context.orchestrator.advance_step(run_id)


def _terminal_states() -> frozenset[str]:
    return frozenset({state.value for state in StepState if state in {StepState.MERGED, StepState.PR_UPDATED, StepState.FAILED}})


def _write_json(path: Path, payload: Any) -> None:
    data = _normalise(payload)
    path.write_text(json.dumps(data, indent=2, sort_keys=True, default=_json_default), encoding="utf-8")


def _normalise(payload: Any) -> Any:
    if isinstance(payload, Sequence) and not isinstance(payload, (str, bytes, bytearray)):
        return list(payload)
    return payload



def _json_default(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Path):
        return str(value)
    return value



def _export_diffs(export_dir: Path, artifacts: Iterable[Mapping[str, object]]) -> None:
    for artifact in artifacts:
        if artifact.get("kind") != "diff":
            continue
        step_id = artifact.get("step_id", "unknown-step")
        diff_path = export_dir / f"{step_id}.patch"
        diff_path.write_text(str(artifact.get("content", "")), encoding="utf-8")


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    raise SystemExit(main())
