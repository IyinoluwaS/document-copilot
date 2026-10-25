from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

from app.config import settings
from app.database.models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def database_url() -> str:
    # Supabase hands out postgresql:// URLs, which SQLAlchemy maps to psycopg2.
    # We ship psycopg 3, so name the driver explicitly. The URL is passed straight
    # to SQLAlchemy rather than via config.set_main_option, because ConfigParser
    # would choke on %-encoded characters in the password.
    url = settings.database_url.get_secret_value()
    return url.replace("postgresql://", "postgresql+psycopg://", 1)


def include_object(obj, name, type_, reflected, compare_to) -> bool:
    # FKs into Supabase-managed schemas (e.g. users.id -> auth.users.id) are
    # created by hand in migrations and can't live on the models.
    if type_ == "foreign_key_constraint" and reflected and compare_to is None:
        return obj.referred_table.schema != "auth"
    return True


def run_migrations_offline() -> None:
    context.configure(
        url=database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(database_url(), poolclass=pool.NullPool)

    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
