from dotenv import load_dotenv
import os

# Load the .env file manually
load_dotenv(".env")

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

from app.db.session import Base  # Your SQLAlchemy base
from app import models  # Import all models so Alembic sees them

# Load config and log settings
config = context.config
fileConfig(config.config_file_name)

# Inject DB URL from ENV
import os
config.set_main_option("sqlalchemy.url", os.getenv("DATABASE_URL"))

target_metadata = Base.metadata

def run_migrations_offline():
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
