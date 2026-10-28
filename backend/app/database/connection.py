from fastapi import HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import DATABASE_URL


if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL no está configurada. Revisa backend/.env "
        "y coloca la conexión PostgreSQL del laboratorio."
    )


engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


Base = declarative_base()


def get_db():
    db = SessionLocal()

    try:
        yield db

    except SQLAlchemyError as exc:
        db.rollback()

        raise HTTPException(
            status_code=503,
            detail=(
                "Base de datos no disponible. "
                "Revisa PostgreSQL y DATABASE_URL en backend/.env."
            ),
        ) from exc

    finally:
        db.close()


def check_database_connection() -> bool:
    """
    Comprueba si PostgreSQL acepta una consulta sencilla.
    No modifica información.
    """

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return True

    except SQLAlchemyError:
        return False