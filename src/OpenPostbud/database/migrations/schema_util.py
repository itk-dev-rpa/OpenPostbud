
from pathlib import Path
import difflib

from sqlalchemy import create_engine


def compare_schemas(db_path_1: Path, db_path_2: Path):
    """Compare the two given SQLite databases."""
    with create_engine(f"sqlite+pysqlite:///{db_path_1}").begin() as conn:
        db_1_schemas = conn.exec_driver_sql("SELECT type, name, tbl_name, sql FROM sqlite_master;").fetchall()

    with create_engine(f"sqlite+pysqlite:///{db_path_2}").begin() as conn:
        db_2_schemas = conn.exec_driver_sql("SELECT type, name, tbl_name, sql FROM sqlite_master;").fetchall()

    schema_table_1: dict[tuple, str] = {(type, tbl_name, name): sql for type, name, tbl_name, sql in db_1_schemas}
    schema_table_2: dict[tuple, str] = {(type, tbl_name, name): sql for type, name, tbl_name, sql in db_2_schemas}

    print("Uniques in schema", db_path_1)
    _print_table(("Type", "Table", "Name"), tuple(schema_table_1.keys() - schema_table_2.keys()))
    print("-----")
    print("Uniques in schema", db_path_2)
    _print_table(("Type", "Table", "Name"), tuple(schema_table_2.keys() - schema_table_1.keys()))
    print("-----")

    for key in schema_table_1:
        if key in schema_table_2 and schema_table_1[key] != schema_table_2[key]:
            print("Difference in sql in: ", key)
            diff = difflib.context_diff(
                schema_table_1[key].splitlines(True),
                schema_table_2[key].splitlines(True),
                fromfile=str(db_path_1),
                tofile=str(db_path_2),
                n=1
            )
            print(*diff, sep="")


def _print_table(header: tuple[str], rows: tuple[tuple[str]]):
    """Print a tuple of string tuples as a nicely formatted table."""
    assert all(len(header) == len(row) for row in rows)
    if not rows:
        return

    column_widths = []
    for i in range(len(header)):
        column_widths.append(
            max(len(header[i]), *(len(row[i]) for row in rows))
        )

    for i, cell in enumerate(header):
        print(cell.ljust(column_widths[i]), end=" | ")
    print()

    for row in rows:
        for i, cell in enumerate(row):
            print(cell.ljust(column_widths[i]), end=" | ")
        print()


if __name__ == '__main__':
    path1 = Path("database.db")
    path2 = Path("database.backup")
    compare_schemas(path1, path2)
