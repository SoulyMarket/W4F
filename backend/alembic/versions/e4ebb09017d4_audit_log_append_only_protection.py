"""audit log append only protection

section 6.6: every create/update/delete/status change writes to audit_log,
and audit_log itself must never be rewritten — not even by a bug in the app
role, and not even by a superuser issuing routine DML by mistake. A
BEFORE UPDATE/DELETE trigger raising an exception is used instead of a bare
REVOKE, because REVOKE only constrains a specific DB role (not yet defined
here, and bypassed entirely by whichever role actually owns/connects as the
app in a given deployment) — the trigger applies unconditionally to anyone
on this table, including the owner.

Revision ID: e4ebb09017d4
Revises: 2b1e9c52e97c
Create Date: 2026-10-08 21:26:40.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'e4ebb09017d4'
down_revision: Union[str, Sequence[str], None] = '2b1e9c52e97c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION reject_audit_log_mutation()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'audit_log is append-only: % is not permitted', TG_OP;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER audit_log_append_only
        BEFORE UPDATE OR DELETE ON audit_log
        FOR EACH ROW EXECUTE FUNCTION reject_audit_log_mutation();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS audit_log_append_only ON audit_log")
    op.execute("DROP FUNCTION IF EXISTS reject_audit_log_mutation()")
