"""added columns for soft delete

Revision ID: 0f99b6e976c4
Revises: ecc22170b5e7
Create Date: 2026-02-09 15:48:00.767252
"""

import sqlalchemy as sa
from alembic import op

revision = '0f99b6e976c4'
down_revision = 'ecc22170b5e7'
branch_labels = None
depends_on = None


def upgrade():
    # ---------- products ----------
    with op.batch_alter_table('products') as batch_op:
        batch_op.add_column(sa.Column('is_deleted', sa.Boolean(), nullable=True))

    op.execute("UPDATE products SET is_deleted = FALSE WHERE is_deleted IS NULL")

    with op.batch_alter_table('products') as batch_op:
        batch_op.alter_column('is_deleted', nullable=False, server_default=sa.false())

    # ---------- sellers ----------
    with op.batch_alter_table('sellers') as batch_op:
        batch_op.add_column(sa.Column('is_active', sa.Boolean(), nullable=True))

    op.execute("UPDATE sellers SET is_active = TRUE WHERE is_active IS NULL")

    with op.batch_alter_table('sellers') as batch_op:
        batch_op.alter_column('is_active', nullable=False, server_default=sa.true())


def downgrade():
    with op.batch_alter_table('sellers') as batch_op:
        batch_op.drop_column('is_active')

    with op.batch_alter_table('products') as batch_op:
        batch_op.drop_column('is_deleted')
