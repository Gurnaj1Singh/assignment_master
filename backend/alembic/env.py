"""Alembic environment configuration.

Reads DATABASE_URL from .env so migrations use the same connection as the app.
"""

import os
import sys
from logging.config import fileConfig

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import create_engine

# Add project root (assignment_master/) to sys.path.
# env.py lives at backend/alembic/env.py — two levels up reaches the project root,
# which is the directory that contains the `backend` package.
# `from backend.models import Base` then resolves correctly.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

from backend.models import Base  # noqa: E402

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Override sqlalchemy.url from environment
db_url = os.getenv("SQLALCHEMY_DATABASE_URL")
if db_url:
    config.set_main_option("sqlalchemy.url", db_url)


def run_migrations_offline():
    """Run migrations in 'offline' mode — generates SQL script."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode — connects to database."""
    connectable = create_engine(config.get_main_option("sqlalchemy.url"))

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
