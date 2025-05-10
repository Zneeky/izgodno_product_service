from dotenv import load_dotenv
load_dotenv(".env")

import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

from app.db.session import Base
from app import models

config = context.config
fileConfig(config.config_file_name)

ASYNC_DB_URL = os.getenv("DATABASE_URL")
SYNC_DB_URL = ASYNC_DB_URL.replace("postgresql+asyncpg", "postgresql+psycopg2")
config.set_main_option("sqlalchemy.url", SYNC_DB_URL)

target_metadata = Base.metadata
