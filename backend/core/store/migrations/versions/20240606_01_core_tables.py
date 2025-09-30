"""Create core persistence tables."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20240606_01"
down_revision = None
branch_labels = None
depends_on = None


RUN_STATUS = ("pending", "running", "completed", "failed", "cancelled")
STEP_STATUS = ("pending", "running", "completed", "failed", "skipped")
ARTIFACT_KINDS = ("diff", "doc", "log", "blob", "rej")
EVENT_TYPES = (
    "run.created",
    "run.completed",
    "step.planned",
    "step.executing",
    "step.validated",
    "step.failed",
    "step.committed",
    "step.merged",
)


CREATE_UPDATED_AT_TRIGGER = """
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""


RUN_TRIGGER = """
CREATE TRIGGER runs_set_updated_at
BEFORE UPDATE ON runs
FOR EACH ROW EXECUTE PROCEDURE set_updated_at();
"""


STEP_TRIGGER = """
CREATE TRIGGER steps_set_updated_at
BEFORE UPDATE ON steps
FOR EACH ROW EXECUTE PROCEDURE set_updated_at();
"""


DROP_RUN_TRIGGER = "DROP TRIGGER IF EXISTS runs_set_updated_at ON runs;"
DROP_STEP_TRIGGER = "DROP TRIGGER IF EXISTS steps_set_updated_at ON steps;"
DROP_TRIGGER_FUNCTION = "DROP FUNCTION IF EXISTS set_updated_at();"


def upgrade() -> None:
    run_status_enum = sa.Enum(*RUN_STATUS, name="run_status", native_enum=False, create_constraint=True)
    step_status_enum = sa.Enum(*STEP_STATUS, name="step_status", native_enum=False, create_constraint=True)
    artifact_kind_enum = sa.Enum(*ARTIFACT_KINDS, name="artifact_kind", native_enum=False, create_constraint=True)
    event_type_enum = sa.Enum(*EVENT_TYPES, name="event_type", native_enum=False, create_constraint=True)

    op.create_table(
        "runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("repo", sa.Text(), nullable=False),
        sa.Column("base_ref", sa.Text(), nullable=False),
        sa.Column("branch_ref", sa.Text(), nullable=False),
        sa.Column("status", run_status_enum, nullable=False, server_default=sa.text("'pending'")),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "steps",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("idx", sa.Integer(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("status", step_status_enum, nullable=False, server_default=sa.text("'pending'")),
        sa.Column("acceptance_criteria", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("plan_md", sa.Text(), nullable=True),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["run_id"], ["runs.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("run_id", "idx"),
    )
    op.create_index(op.f("ix_steps_run_id"), "steps", ["run_id"], unique=False)

    op.create_table(
        "artifacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("step_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("kind", artifact_kind_enum, nullable=False),
        sa.Column("uri", sa.Text(), nullable=False),
        sa.Column("meta", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["step_id"], ["steps.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_artifacts_step_id"), "artifacts", ["step_id"], unique=False)

    op.create_table(
        "validation_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("step_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("report", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("fatal_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("warnings_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["step_id"], ["steps.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_validation_reports_step_id"), "validation_reports", ["step_id"], unique=False)

    op.create_table(
        "pr_bindings",
        sa.Column("run_id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("pr_number", sa.Integer(), nullable=False),
        sa.Column("pr_url", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["runs.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "events",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("step_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("type", event_type_enum, nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("ts", postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["run_id"], ["runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["step_id"], ["steps.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_events_run_id"), "events", ["run_id"], unique=False)
    op.create_index(op.f("ix_events_step_id"), "events", ["step_id"], unique=False)

    op.execute(CREATE_UPDATED_AT_TRIGGER)
    op.execute(RUN_TRIGGER)
    op.execute(STEP_TRIGGER)


def downgrade() -> None:
    op.execute(DROP_RUN_TRIGGER)
    op.execute(DROP_STEP_TRIGGER)
    op.execute(DROP_TRIGGER_FUNCTION)

    op.drop_index(op.f("ix_events_step_id"), table_name="events")
    op.drop_index(op.f("ix_events_run_id"), table_name="events")
    op.drop_table("events")

    op.drop_table("pr_bindings")

    op.drop_index(op.f("ix_validation_reports_step_id"), table_name="validation_reports")
    op.drop_table("validation_reports")

    op.drop_index(op.f("ix_artifacts_step_id"), table_name="artifacts")
    op.drop_table("artifacts")

    op.drop_index(op.f("ix_steps_run_id"), table_name="steps")
    op.drop_table("steps")

    op.drop_table("runs")
