import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool
from alembic import context

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.config import settings
from app.db.base_class import Base
from app import models  # noqa: F401 -- registers all models on Base.metadata

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Ensure the local SQLite data directory exists before Alembic tries to
# connect -- on a fresh clone this directory doesn't exist yet (git doesn't
# track empty dirs), and `alembic upgrade head` is the very first command
# a new developer runs, so this must not depend on app.db.session having
# been imported first.
if settings.DATABASE_URL.startswith("sqlite"):
    _db_path = settings.DATABASE_URL.replace("sqlite:///", "")
    if _db_path != ":memory:":
        Path(_db_path).parent.mkdir(parents=True, exist_ok=True)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(config.get_section(config.config_ini_section), prefix="sqlalchemy.",
                                       poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
