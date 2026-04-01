from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

import pymysql
from pymysql.connections import Connection
from pymysql.cursors import Cursor, DictCursor

from app.core.config import settings


def get_connection(database: str | None = None, autocommit: bool = True) -> Connection:
    return pymysql.connect(
        host=settings.db_host,
        port=settings.db_port,
        user=settings.db_user,
        password=settings.db_password,
        database=database or settings.db_name,
        charset="utf8mb4",
        cursorclass=DictCursor,
        autocommit=autocommit,
    )


@contextmanager
def db_cursor(database: str | None = None) -> Iterator[Cursor]:
    connection = get_connection(database=database, autocommit=False)
    cursor = connection.cursor()
    try:
        yield cursor
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


def fetch_one_dict(cursor: Cursor) -> dict[str, Any] | None:
    row = cursor.fetchone()
    if row is None:
        return None
    return dict(row)
