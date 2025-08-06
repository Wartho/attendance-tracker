"""Change password_hash to Text for longer hashes

Revision ID: f26569842767
Revises: 5104a34db420
Create Date: 2025-07-19 01:42:40.236601

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f26569842767'
down_revision = '5104a34db420'
branch_labels = None
depends_on = None


def upgrade():
    # SQLite doesn't support ALTER COLUMN TYPE, so we need to recreate the table
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.alter_column('password_hash', type_=sa.Text())
        batch_op.alter_column('classes', type_=sa.String(length=32))


def downgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.alter_column('password_hash', type_=sa.String(length=128))
        batch_op.alter_column('classes', type_=sa.String(length=10))
