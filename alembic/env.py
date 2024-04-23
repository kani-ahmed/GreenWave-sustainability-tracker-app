import os
import sys

sys.path.append(os.getcwd())

from flask import Flask
from dotenv import load_dotenv

load_dotenv()

# Import your application's configuration and models
from app import app as flask_app
from extensions import db
import models

from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

database_uri = os.getenv("DATABASE_URI").replace("%40", "@")

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

config.set_main_option("sqlalchemy.url", database_uri)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
#target_metadata = None
target_metadata = db.Model.metadata


# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline():
    """Run migrations in 'offline' mode."""
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
    """Run migrations in 'online' mode."""
    # Establishes an engine from existing SQLAlchemy engine
    connectable = db.engine

    with connectable.connect() as connection:
        with context.begin_transaction():
            # Configure the context with connection and metadata
            context.configure(
                connection=connection,
                target_metadata=target_metadata
            )

            # Wrapping the migration in the Flask application context
            with flask_app.app_context():
                context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
