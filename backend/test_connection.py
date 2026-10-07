from sqlalchemy import text

from app.database.connection import engine


def test_connection():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            value = result.scalar()

            print("Conexión a PostgreSQL exitosa")
            print("Resultado:", value)

    except Exception as error:
        print("Error al conectar con PostgreSQL")
        print(error)


if __name__ == "__main__":
    test_connection()