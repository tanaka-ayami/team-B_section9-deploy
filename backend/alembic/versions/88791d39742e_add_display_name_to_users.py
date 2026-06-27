"""add display_name to users

Revision ID: 88791d39742e
Revises: 143ea6605dfc
Create Date: 2026-06-26 09:04:14.774732

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '88791d39742e'
down_revision: Union[str, Sequence[str], None] = '143ea6605dfc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ① まずNULL許容で追加（既存行が落ちないように）
    op.add_column('users', sa.Column('display_name', sa.String(length=50), nullable=True))

    # ② 既存行に「メールの@より前」を初期値として一括投入
    op.execute(
        "UPDATE users SET display_name = split_part(email, '@', 1) WHERE display_name IS NULL"
    )

    # ③ 全行に値が入った状態でNOT NULL制約を確定
    op.alter_column('users', 'display_name', nullable=False)


def downgrade() -> None:
    op.drop_column('users', 'display_name')