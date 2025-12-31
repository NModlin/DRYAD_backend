import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Explicitly add current directory to python path to allow imports
import sys
import os
sys.path.append(os.getcwd())

# Import the Base and your models
from app.university_system.database.database import Base
# Make sure to import all models so they are registered with Base.metadata
from app.university_system.database.models_university import *  # noqa

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# target_metadata is the MetaData collection that your
# models are registered to.
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    # Check if we are using SQLite, which is synchronous by default in SQLAlchemy
    # unless using a specific async driver. For this codebase, it seems we use
    # standard create_engine in database.py, but Alembic often prefers async.
    # However, since the main codebase database.py uses synchronous create_engine,
    # we should stick to synchronous execution for simplicity unless specifically async.
    # WAIT: database.py uses create_engine (sync).
    # So we should actually run synchronous migrations.
    pass


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.
    """
    # Override sqlalchemy.url with environment variable if present
    # This matches the logic in database.py
    
    # We need to get the URL from the same place database.py gets it, 
    # OR rely on config. But for better reliability:
    from app.university_system.database.database import DATABASE_URL, engine
    
    # Use the engine from app.university_system.database.py directly if possible, or create a new one
    # configuration = config.get_section(config.config_ini_section)
    # configuration["sqlalchemy.url"] = DATABASE_URL
    
    # connectable = engine
    
    # Direct connection via the engine created in project
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
