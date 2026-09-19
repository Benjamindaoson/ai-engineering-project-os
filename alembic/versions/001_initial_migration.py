"""Initial migration - create all tables

Revision ID: 001
Revises:
Create Date: 2026-09-19

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create projects table
    op.create_table(
        'projects',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, default=''),
        sa.Column('github_url', sa.String(500), nullable=True),
        sa.Column('local_path', sa.String(1000), nullable=True),
        sa.Column('current_maturity', sa.String(50), default='idea'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Create repository_snapshots table
    op.create_table(
        'repository_snapshots',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('repo_url', sa.String(500), nullable=False),
        sa.Column('branch', sa.String(255), default='main'),
        sa.Column('commit_sha', sa.String(40), nullable=False),
        sa.Column('workspace_path', sa.String(1000), nullable=False),
        sa.Column('imported_at', sa.DateTime, server_default=sa.func.now()),
    )

    # Create project_facts table
    op.create_table(
        'project_facts',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('snapshot_id', sa.String(36), sa.ForeignKey('repository_snapshots.id'), nullable=True),
        sa.Column('languages', sa.JSON, default=list),
        sa.Column('frameworks', sa.JSON, default=list),
        sa.Column('databases', sa.JSON, default=list),
        sa.Column('deployment', sa.JSON, default=list),
        sa.Column('total_files', sa.Integer, default=0),
        sa.Column('total_lines', sa.Integer, default=0),
        sa.Column('code_lines', sa.Integer, default=0),
        sa.Column('test_files', sa.Integer, default=0),
        sa.Column('config_files', sa.Integer, default=0),
        sa.Column('has_readme', sa.Boolean, default=False),
        sa.Column('has_api_docs', sa.Boolean, default=False),
        sa.Column('has_deployment_docs', sa.Boolean, default=False),
        sa.Column('project_type', sa.String(50), default='other'),
        sa.Column('implementation_status', sa.JSON, default=dict),
        sa.Column('raw_observations', sa.JSON, default=list),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    # Create maturity_assessments table
    op.create_table(
        'maturity_assessments',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('snapshot_id', sa.String(36), sa.ForeignKey('repository_snapshots.id'), nullable=True),
        sa.Column('overall_level', sa.String(50), nullable=False),
        sa.Column('dimension_scores', sa.JSON, default=dict),
        sa.Column('blockers', sa.JSON, default=list),
        sa.Column('recommendations', sa.JSON, default=list),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    # Create gaps table
    op.create_table(
        'gaps',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('dimension', sa.String(100), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('current_state', sa.Text, default=''),
        sa.Column('target_state', sa.Text, default=''),
        sa.Column('priority', sa.String(20), default='medium'),
        sa.Column('effort_estimate', sa.String(20), default='medium'),
        sa.Column('risk', sa.String(20), default='medium'),
        sa.Column('related_criteria', sa.JSON, default=list),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    # Create engineering_tasks table
    op.create_table(
        'engineering_tasks',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('gap_id', sa.String(36), sa.ForeignKey('gaps.id'), nullable=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text, default=''),
        sa.Column('learning_content', sa.JSON, default=dict),
        sa.Column('completion_criteria', sa.JSON, default=list),
        sa.Column('estimated_effort', sa.String(50), default=''),
        sa.Column('prerequisites', sa.JSON, default=list),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime, nullable=True),
    )

    # Create execution_runs table
    op.create_table(
        'execution_runs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('task_id', sa.String(36), sa.ForeignKey('engineering_tasks.id'), nullable=False),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('changes', sa.JSON, default=list),
        sa.Column('test_results', sa.JSON, default=list),
        sa.Column('benchmark_results', sa.JSON, default=list),
        sa.Column('execution_log', sa.Text, default=''),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('started_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime, nullable=True),
        sa.Column('error', sa.Text, nullable=True),
    )

    # Create verification_results table
    op.create_table(
        'verification_results',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('execution_id', sa.String(36), sa.ForeignKey('execution_runs.id'), nullable=False),
        sa.Column('task_id', sa.String(36), nullable=False),
        sa.Column('verification_results', sa.JSON, default=list),
        sa.Column('overall_status', sa.String(20), default='unverifiable'),
        sa.Column('missing_evidence', sa.JSON, default=list),
        sa.Column('recommendations', sa.JSON, default=list),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    # Create project_versions table (before evidence due to FK)
    op.create_table(
        'project_versions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('version_number', sa.Integer, nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text, default=''),
        sa.Column('maturity_before', sa.String(50), nullable=True),
        sa.Column('maturity_after', sa.String(50), nullable=True),
        sa.Column('files_changed', sa.JSON, default=list),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    # Create evidence table
    op.create_table(
        'evidence',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('version_id', sa.String(36), sa.ForeignKey('project_versions.id'), nullable=True),
        sa.Column('verification_id', sa.String(36), nullable=True),
        sa.Column('task_id', sa.String(36), nullable=True),
        sa.Column('execution_id', sa.String(36), nullable=True),
        sa.Column('evidence_type', sa.String(50), nullable=False),
        sa.Column('source_path', sa.String(1000), nullable=False),
        sa.Column('title', sa.String(500), default=''),
        sa.Column('description', sa.Text, default=''),
        sa.Column('content', sa.Text, default=''),
        sa.Column('line_start', sa.Integer, nullable=True),
        sa.Column('line_end', sa.Integer, nullable=True),
        sa.Column('score', sa.Float, default=0.0),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    # Create experiments table
    op.create_table(
        'experiments',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('name', sa.String(500), nullable=False),
        sa.Column('description', sa.Text, default=''),
        sa.Column('config', sa.JSON, default=dict),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    # Create experiment_runs table
    op.create_table(
        'experiment_runs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('experiment_id', sa.String(36), nullable=False),
        sa.Column('config', sa.JSON, default=dict),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('metrics', sa.JSON, default=dict),
        sa.Column('latency_ms', sa.Float, default=0.0),
        sa.Column('started_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    # Create interview_sessions table
    op.create_table(
        'interview_sessions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('task_id', sa.String(36), nullable=True),
        sa.Column('status', sa.String(20), default='in_progress'),
        sa.Column('started_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('ended_at', sa.DateTime, nullable=True),
    )

    # Create interview_questions table
    op.create_table(
        'interview_questions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('session_id', sa.String(36), sa.ForeignKey('interview_sessions.id'), nullable=False),
        sa.Column('parent_question_id', sa.String(36), nullable=True),
        sa.Column('question', sa.Text, nullable=False),
        sa.Column('context', sa.Text, default=''),
        sa.Column('user_answer', sa.Text, nullable=True),
        sa.Column('follow_ups', sa.JSON, default=list),
        sa.Column('current_follow_up', sa.Integer, default=0),
        sa.Column('gap_type', sa.String(50), nullable=True),
        sa.Column('status', sa.String(20), default='pending'),
    )

    # Create interview_answers table
    op.create_table(
        'interview_answers',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('session_id', sa.String(36), sa.ForeignKey('interview_sessions.id'), nullable=False),
        sa.Column('question_id', sa.String(36), sa.ForeignKey('interview_questions.id'), nullable=False),
        sa.Column('answer', sa.Text, nullable=False),
        sa.Column('quality', sa.String(20), nullable=True),
        sa.Column('gap_type', sa.String(50), nullable=True),
        sa.Column('suggestion', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    # Create interview_assessments table
    op.create_table(
        'interview_assessments',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('session_id', sa.String(36), sa.ForeignKey('interview_sessions.id'), nullable=False),
        sa.Column('question_id', sa.String(36), sa.ForeignKey('interview_questions.id'), nullable=False),
        sa.Column('answer_id', sa.String(36), sa.ForeignKey('interview_answers.id'), nullable=False),
        sa.Column('quality', sa.String(20), nullable=False),
        sa.Column('reasoning', sa.Text, nullable=True),
        sa.Column('knowledge_gap', sa.Text, nullable=True),
        sa.Column('engineering_gap', sa.Text, nullable=True),
        sa.Column('evidence_gap', sa.Text, nullable=True),
        sa.Column('experiment_gap', sa.Text, nullable=True),
        sa.Column('suggestion', sa.Text, nullable=True),
        sa.Column('has_example', sa.Boolean, default=False),
        sa.Column('has_reason', sa.Boolean, default=False),
        sa.Column('has_quantitative', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    # Create interview_gaps table
    op.create_table(
        'interview_gaps',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('session_id', sa.String(36), sa.ForeignKey('interview_sessions.id'), nullable=False),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('question_id', sa.String(36), sa.ForeignKey('interview_questions.id'), nullable=True),
        sa.Column('task_id', sa.String(36), nullable=True),
        sa.Column('gap_type', sa.String(50), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('severity', sa.String(20), default='medium'),
        sa.Column('status', sa.String(20), default='identified'),
        sa.Column('recommendation', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('resolved_at', sa.DateTime, nullable=True),
    )


def downgrade() -> None:
    """Drop all tables in reverse order of creation"""
    op.drop_table('interview_gaps')
    op.drop_table('interview_assessments')
    op.drop_table('interview_answers')
    op.drop_table('interview_questions')
    op.drop_table('interview_sessions')
    op.drop_table('experiment_runs')
    op.drop_table('experiments')
    op.drop_table('evidence')
    op.drop_table('project_versions')
    op.drop_table('verification_results')
    op.drop_table('execution_runs')
    op.drop_table('engineering_tasks')
    op.drop_table('gaps')
    op.drop_table('maturity_assessments')
    op.drop_table('project_facts')
    op.drop_table('repository_snapshots')
    op.drop_table('projects')
