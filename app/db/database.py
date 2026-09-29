import os

import psycopg
from dotenv import load_dotenv

load_dotenv()


# ---------------------------------------------------------
# Configuración de PostgreSQL.
#
# Los valores se obtienen desde las variables de entorno.
# ---------------------------------------------------------

POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")


# ---------------------------------------------------------
# Excepción utilizada cuando PostgreSQL no está disponible.
# ---------------------------------------------------------

class DatabaseConnectionError(Exception):
    pass


# ---------------------------------------------------------
# Crea una conexión con PostgreSQL.
# ---------------------------------------------------------

def get_connection():

    try:

        return psycopg.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            dbname=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            connect_timeout=5
        )

    except psycopg.OperationalError as e:

        raise DatabaseConnectionError(
            "La base de datos PostgreSQL no está disponible. "
            "Encienda el contenedor de PostgreSQL e inténtelo nuevamente."
        ) from e