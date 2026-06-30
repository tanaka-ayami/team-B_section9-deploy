"""add email_notify_enabled to users

Revision ID: c4e7bfe19ef1
Revises: 38ea6523f258
Create Date: 2026-06-30 11:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4e7bfe19ef1'
down_revision: Union[str, Sequence[str], None] = '38ea6523f258'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # display_nameのときと異なり、デフォルト値（true）が決まっているため
    # server_defaultを指定すれば、NULL許容→UPDATE→NOT NULL化の3段階は不要。
    # 既存行にも一括でtrueが入った状態でNOT NULL制約までこの1文で完了する。
    op.add_column(
        'users',
        sa.Column(
            'email_notify_enabled',
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )


def downgrade() -> None:
    op.drop_column('users', 'email_notify_enabled')