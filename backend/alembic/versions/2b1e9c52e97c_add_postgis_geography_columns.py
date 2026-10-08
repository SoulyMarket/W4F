"""add postgis geography columns

Enables the postgis extension and adds douars.location / reports.location
as geography(Point, 4326), plus GIST indexes. Split out from the initial
schema migration so the rest of the schema can be created and tested on a
plain PostgreSQL instance without PostGIS installed — see PROGRESS.md.

Revision ID: 2b1e9c52e97c
Revises: e7ddb5e5e606
Create Date: 2026-10-08 21:25:26.923033

"""
from typing import Sequence, Union

import geoalchemy2
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2b1e9c52e97c'
down_revision: Union[str, Sequence[str], None] = 'e7ddb5e5e606'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_GEOGRAPHY_POINT = geoalchemy2.Geography(geometry_type="POINT", srid=4326)


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    op.add_column("douars", sa.Column("location", _GEOGRAPHY_POINT, nullable=True))
    op.create_index(
        "idx_douars_location", "douars", ["location"], unique=False, postgresql_using="gist"
    )

    op.add_column("reports", sa.Column("location", _GEOGRAPHY_POINT, nullable=True))
    op.create_index(
        "idx_reports_location", "reports", ["location"], unique=False, postgresql_using="gist"
    )


def downgrade() -> None:
    op.drop_index("idx_reports_location", table_name="reports", postgresql_using="gist")
    op.drop_column("reports", "location")

    op.drop_index("idx_douars_location", table_name="douars", postgresql_using="gist")
    op.drop_column("douars", "location")

    op.execute("DROP EXTENSION IF EXISTS postgis")
