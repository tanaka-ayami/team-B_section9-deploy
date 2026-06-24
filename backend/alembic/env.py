from logging.config import fileConfig

from alembic import context

from app.db.base import Base, engine

# 全モデルをここでimportしておくことで、Base.metadataに全テーブルが登録される。
# （app/models/__init__.py が全モデルをまとめてimportしている）
from app.models import (  # noqa: F401
    AppNotification,
    Category,
    Document,
    Group,
    GroupMember,
    Invitation,
    NotificationSchedule,
    User,
)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    alembic.ini の sqlalchemy.url はコメントアウトしたままでよい。
    接続URLは app/db/base.py の engine（= settings.DATABASE_URL）から取得する。
    """
    url = str(engine.url)
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    engine_from_config(alembic.ini由来)ではなく、
    app/db/base.py で既に作られている engine をそのまま使う。
    """
    connectable = engine

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()