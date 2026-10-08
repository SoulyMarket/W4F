"""add postgis geography columns

Enables the postgis extension and adds douars.location / reports.location
as geography(Point, 4326). Split out from the initial schema migration so
the rest of the schema can be created and tested on a plain PostgreSQL
instance without PostGIS installed — see PROGRESS.md.

No manual op.create_index() here for the GIST index: GeoAlchemy2's Alembic
integration hooks op.add_column()/op.drop_column() and already creates/
drops the spatial index itself whenever the column's spatial_index=True
(the Geography default) — found by hitting "relation already exists" on a
manual op.create_index() placed right after op.add_column() for the same
column, which turned out to be racing GeoAlchemy2's own index creation,
not a real naming collision with anything else in the schema.

Revision ID: 2b1e9c52e97c
Revises: 6fa4e9cbc1db
Create Date: 2026-10-08 21:25:26.923033

"""
from typing import Sequence, Union

import geoalchemy2
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2b1e9c52e97c'
down_revision: Union[str, Sequence[str], None] = '6fa4e9cbc1db'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_GEOGRAPHY_POINT = geoalchemy2.Geography(geometry_type="POINT", srid=4326)


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.add_column("douars", sa.Column("location", _GEOGRAPHY_POINT, nullable=True))
    op.add_column("reports", sa.Column("location", _GEOGRAPHY_POINT, nullable=True))


def downgrade() -> None:
    op.drop_column("reports", "location")
    op.drop_column("douars", "location")
    op.execute("DROP EXTENSION IF EXISTS postgis")
