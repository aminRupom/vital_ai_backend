"""add human_review_tasks table
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004_human_review_tasks"
down_revision: Union[str, None] = "0003_vector_store"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE TYPE task_type AS ENUM ('triage_review', 'consent_review', 'escalation_review')")
    op.execute("CREATE TYPE task_status AS ENUM ('pending', 'in_progress', 'completed', 'cancelled')")
    op.create_table(
        "human_review_tasks",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("case_id", sa.UUID(), nullable=False),
        sa.Column("triage_id", sa.UUID(), nullable=True),
        sa.Column(
            "task_type",
            sa.Enum("triage_review", "consent_review", "escalation_review", name="task_type", create_type=False),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum("pending", "in_progress", "completed", "cancelled", name="task_status", create_type=False),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("assigned_to", sa.UUID(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["case_id"], ["intake_cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["triage_id"], ["triage_results.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["assigned_to"], ["users.id"], ondelete="SET NULL"),
    )


def downgrade() -> None:
    op.drop_table("human_review_tasks")
    op.execute("DROP TYPE IF EXISTS task_type")
    op.execute("DROP TYPE IF EXISTS task_status")
