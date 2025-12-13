"""Add system_settings table and user session columns

Revision ID: 0002
Revises: 0001
Create Date: 2024-12-14

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add session columns to users table (if they don't exist)
    try:
        op.add_column('users', sa.Column('session_token', sa.String(255), nullable=True))
        op.add_column('users', sa.Column('session_expires', sa.DateTime(), nullable=True))
        op.create_index('ix_users_session_token', 'users', ['session_token'])
    except Exception:
        pass  # Columns may already exist
    
    # Create system_settings table
    op.create_table(
        'system_settings',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('key', sa.String(100), unique=True, nullable=False, index=True),
        sa.Column('value', sa.Float(), nullable=True),
        sa.Column('min_value', sa.Float(), nullable=True),
        sa.Column('max_value', sa.Float(), nullable=True),
        sa.Column('default_value', sa.Float(), nullable=True),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('updated_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True)
    )


def downgrade() -> None:
    op.drop_table('system_settings')
    
    try:
        op.drop_index('ix_users_session_token', 'users')
        op.drop_column('users', 'session_expires')
        op.drop_column('users', 'session_token')
    except Exception:
        pass

