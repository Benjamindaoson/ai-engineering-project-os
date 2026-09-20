"""Add Agent Harness observability, eval, approval and recovery persistence.

Revision ID: 002
Revises: 001
"""

from alembic import op
import sqlalchemy as sa


revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("execution_runs") as batch:
        batch.add_column(sa.Column("trace_id", sa.String(64), nullable=True))
        batch.add_column(sa.Column("harness_metadata", sa.JSON(), nullable=True))
        batch.create_index("ix_execution_runs_trace_id", ["trace_id"], unique=False)

    op.create_table(
        "agent_traces",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("trace_id", sa.String(64), nullable=False),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("task_id", sa.String(36), nullable=True),
        sa.Column("execution_id", sa.String(36), sa.ForeignKey("execution_runs.id"), nullable=True),
        sa.Column("spans", sa.JSON(), nullable=True),
        sa.Column("summary", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint("trace_id", name="uq_agent_traces_trace_id"),
    )
    op.create_index("ix_agent_traces_trace_id", "agent_traces", ["trace_id"], unique=True)

    op.create_table(
        "agent_evaluations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("task_id", sa.String(36), nullable=True),
        sa.Column("execution_id", sa.String(36), sa.ForeignKey("execution_runs.id"), nullable=False),
        sa.Column("verification_id", sa.String(36), nullable=True),
        sa.Column("metrics", sa.JSON(), nullable=True),
        sa.Column("gate_passed", sa.Boolean(), nullable=True),
        sa.Column("gate_failures", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "harness_approvals",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id"), nullable=True),
        sa.Column("task_id", sa.String(36), nullable=True),
        sa.Column("execution_id", sa.String(36), sa.ForeignKey("execution_runs.id"), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("risk", sa.String(20), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("decided_by", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("decided_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "failure_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id"), nullable=True),
        sa.Column("task_id", sa.String(36), nullable=True),
        sa.Column("execution_id", sa.String(36), sa.ForeignKey("execution_runs.id"), nullable=True),
        sa.Column("failure_type", sa.String(50), nullable=False),
        sa.Column("phase", sa.String(50), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("return_code", sa.Integer(), nullable=True),
        sa.Column("recovery_action", sa.String(50), nullable=True),
        sa.Column("retryable", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("resolved", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("failure_events")
    op.drop_table("harness_approvals")
    op.drop_table("agent_evaluations")
    op.drop_index("ix_agent_traces_trace_id", table_name="agent_traces")
    op.drop_table("agent_traces")
    with op.batch_alter_table("execution_runs") as batch:
        batch.drop_index("ix_execution_runs_trace_id")
        batch.drop_column("harness_metadata")
        batch.drop_column("trace_id")
