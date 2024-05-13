"""Add func column to delayed_results

Revision ID: eb68f277ab61
Revises: b37fb68807ea
Create Date: 2023-06-28 17:37:48.244827

"""
import sqlalchemy as sa

from CTFd.plugins.migrations import get_columns_for_table

revision = "eb68f277ab61"
down_revision = "b37fb68807ea"
branch_labels = None
depends_on = None


def upgrade(op=None):
    columns = get_columns_for_table(
        op=op, table_name="delayed_result", names_only=True
    )
    if "function" not in columns:
        op.add_column(
            "delayed_result",
            sa.Column("function", sa.String(length=32), nullable=True),
        )
        conn = op.get_bind()
        url = str(conn.engine.url)
        if url.startswith("postgres"):
            conn.execute(
                "UPDATE delayed_result SET function = 'logarithmic' WHERE function IS NULL"
            )
        else:
            conn.execute(
                "UPDATE delayed_result SET `function` = 'logarithmic' WHERE `function` IS NULL"
            )


def downgrade(op=None):
    columns = get_columns_for_table(
        op=op, table_name="delayed_result", names_only=True
    )
    if "function" in columns:
        op.drop_column("delayed_result", "function")
