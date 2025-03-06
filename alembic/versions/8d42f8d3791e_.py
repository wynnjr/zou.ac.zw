"""Add session column to users table

Revision ID: 8d42f8d3791e
Revises: 
Create Date: 2025-02-24 14:12:54.908320

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic
revision = '8d42f8d3791e'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Get database connection
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)

    # Get existing column names in 'users' table
    columns = [col["name"] for col in inspector.get_columns("users")]

    # Only add column if it doesn't exist
    if "session" not in columns:
        op.add_column('users', sa.Column('session', sa.Boolean(), nullable=False, server_default=sa.text("TRUE")))
    else:
        print("Column 'session' already exists. Skipping migration.")

def downgrade():
    op.drop_column('users', 'session')



