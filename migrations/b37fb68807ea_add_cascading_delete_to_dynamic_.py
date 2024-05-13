"""Add cascading delete to dynamic challenges

Revision ID: b37fb68807ea
Revises:
Create Date: 2020-05-06 12:21:39.373983

"""
import sqlalchemy

revision = "b37fb68807ea"
down_revision = None
branch_labels = None
depends_on = None


def upgrade(op=None):
    bind = op.get_bind()
    url = str(bind.engine.url)

    try:
        if url.startswith("mysql"):
            op.drop_constraint(
                "delayed_result_ibfk_1", "delayed_result", type_="foreignkey"
            )
        elif url.startswith("postgres"):
            op.drop_constraint(
                "delayed_result_id_fkey", "delayed_result", type_="foreignkey"
            )
    except sqlalchemy.exc.InternalError as e:
        print(str(e))

    try:
        op.create_foreign_key(
            None, "delayed_result", "challenges", ["id"], ["id"], ondelete="CASCADE"
        )
    except sqlalchemy.exc.InternalError as e:
        print(str(e))


def downgrade(op=None):
    bind = op.get_bind()
    url = str(bind.engine.url)
    try:
        if url.startswith("mysql"):
            op.drop_constraint(
                "delayed_result_ibfk_1", "delayed_result", type_="foreignkey"
            )
        elif url.startswith("postgres"):
            op.drop_constraint(
                "delayed_result_id_fkey", "delayed_result", type_="foreignkey"
            )
    except sqlalchemy.exc.InternalError as e:
        print(str(e))

    try:
        op.create_foreign_key(None, "delayed_result", "challenges", ["id"], ["id"])
    except sqlalchemy.exc.InternalError as e:
        print(str(e))
