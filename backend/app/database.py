import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row


load_dotenv(
    Path(__file__).resolve().parents[1] / ".env"
)


def conectar(**overrides):
    parameters = dict(
        host=os.environ["PGHOST"],
        port=int(os.environ["PGPORT"]),
        dbname=os.environ["PGDATABASE"],
        user=os.environ["PGUSER"],
        password=os.environ["PGPASSWORD"],
        row_factory=dict_row,
        connect_timeout=10,
    )
    if os.getenv('SF_ENV')=='production':parameters['options']='-c statement_timeout=10000 -c lock_timeout=3000'
    parameters.update(overrides)
    return psycopg.connect(**parameters)
