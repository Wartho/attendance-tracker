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
    op.alter_column('user', 'password_hash', type_=sa.Text())
    op.alter_column('user', 'classes', type_=sa.String(length=32))


def downgrade():
    op.alter_column('user', 'password_hash', type_=sa.String(length=128))
    op.alter_column('user', 'classes', type_=sa.String(length=10))
