from __future__ import annotations

import argparse
import os
from pathlib import Path

import pymysql

IGNORED_ERROR_CODES = {
    1060,  # duplicate column
    1061,  # duplicate key name
    1091,  # can't drop; check that column/key exists
    1826,  # duplicate foreign key constraint name
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Initialize MySQL auth schema for auto-driving-segmentation-system."
    )
    parser.add_argument("--host", default=os.getenv("DB_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("DB_PORT", "3306")))
    parser.add_argument("--user", default=os.getenv("DB_USER", "root"))
    parser.add_argument("--password", default=os.getenv("DB_PASSWORD", ""))
    parser.add_argument(
        "--sql-file",
        default=str(Path(__file__).resolve().parents[1] / "sql" / "init_auth_mysql.sql"),
    )
    return parser.parse_args()


def split_sql_statements(sql_text: str) -> list[str]:
    statements = []
    for chunk in sql_text.split(";"):
        stmt = chunk.strip()
        if not stmt:
            continue
        statements.append(stmt)
    return statements


def main() -> None:
    args = parse_args()
    sql_file = Path(args.sql_file)
    if not sql_file.exists():
        raise FileNotFoundError(f"SQL file not found: {sql_file}")

    sql_text = sql_file.read_text(encoding="utf-8-sig")
    statements = split_sql_statements(sql_text)

    conn = pymysql.connect(
        host=args.host,
        port=args.port,
        user=args.user,
        password=args.password,
        charset="utf8mb4",
        autocommit=True,
    )
    try:
        with conn.cursor() as cursor:
            for index, stmt in enumerate(statements, start=1):
                try:
                    cursor.execute(stmt)
                except pymysql.MySQLError as ex:
                    code = int(ex.args[0]) if ex.args else 0
                    if code in IGNORED_ERROR_CODES:
                        print(f"[{index}] skipped, code={code}, message={ex}")
                        continue
                    raise

                if cursor.description:
                    rows = cursor.fetchall()
                    print(f"[{index}] result={rows}")
                else:
                    print(f"[{index}] ok, affected_rows={cursor.rowcount}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
