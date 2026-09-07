"""SQLAlchemy engine, session factory and the FastAPI ``get_db`` dependency."""

from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

# ``check_same_thread=False`` is required because FastAPI serves requests from a
# threadpool while SQLite defaults to single-thread ownership of a connection.
_connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(
    settings.database_url,
    connect_args=_connect_args,
    # Verifies a pooled connection is alive before handing it out, which keeps
    # the app healthy across a database restart.
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


@event.listens_for(Engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
    """SQLite ignores foreign keys unless told otherwise, per connection.

    Without this the cascade rules declared on the models would silently do
    nothing, so the schema's referential integrity is enforced here.
    """
    if not settings.database_url.startswith("sqlite"):
        return
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


class Base(DeclarativeBase):
    """Declarative base shared by every model."""


def get_db() -> Generator[Session, None, None]:
    """Yield a request-scoped session and always close it.

    Routers depend on this rather than constructing sessions themselves, so the
    session lifetime is tied to the request and never leaks.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
