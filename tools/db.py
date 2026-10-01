"""Connexion et exécution de scripts SQL sans SQLcl.

Usage :
    python tools/db.py init                 # (re)crée le schéma CBS_LAB depuis db/core/*.sql
    python tools/db.py run sql/00_sanity/sanity_checks.sql
"""
import os
import re
import sys
from pathlib import Path

import oracledb

ROOT = Path(__file__).resolve().parents[1]


def load_env() -> None:
    env = ROOT / ".env"
    if not env.exists():
        sys.exit("Fichier .env absent : copiez .env.example en .env")
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


def connect() -> oracledb.Connection:
    load_env()
    return oracledb.connect(user=os.environ["DB_USER"],
                            password=os.environ["DB_PASSWORD"],
                            dsn=os.environ["DB_DSN"])


def split_statements(text: str) -> list[str]:
    """Découpe un script : ';' en fin de ligne pour le SQL, '/' seul sur une ligne pour le PL/SQL."""
    text = re.sub(r"^\s*--.*$", "", text, flags=re.MULTILINE)
    stmts, buf, in_plsql = [], [], False
    for line in text.splitlines():
        stripped = line.strip()
        if not buf and re.match(r"(CREATE\s+(OR\s+REPLACE\s+)?(PACKAGE|PROCEDURE|FUNCTION|TRIGGER|TYPE)|DECLARE|BEGIN)\b",
                                stripped, re.IGNORECASE):
            in_plsql = True
        if in_plsql and stripped == "/":
            stmts.append("\n".join(buf).strip())
            buf, in_plsql = [], False
            continue
        buf.append(line)
        if not in_plsql and stripped.endswith(";"):
            stmts.append("\n".join(buf).strip().rstrip(";"))
            buf = []
    if "\n".join(buf).strip():
        stmts.append("\n".join(buf).strip().rstrip(";"))
    return [s for s in stmts if s]


def drop_all(cur) -> None:
    cur.execute("SELECT table_name FROM user_tables")
    for (t,) in cur.fetchall():
        cur.execute(f'DROP TABLE "{t}" CASCADE CONSTRAINTS PURGE')


def run_file(cur, path: Path, show: bool = False) -> None:
    for stmt in split_statements(path.read_text(encoding="utf-8")):
        cur.execute(stmt)
        if show and cur.description:
            cols = [d[0] for d in cur.description]
            print("\n" + stmt.splitlines()[0][:100])
            print(" | ".join(cols))
            for row in cur.fetchmany(50):
                print(" | ".join("" if v is None else str(v) for v in row))


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in ("init", "run"):
        sys.exit(__doc__)
    with connect() as conn, conn.cursor() as cur:
        if sys.argv[1] == "init":
            drop_all(cur)
            for f in sorted((ROOT / "db" / "core").glob("*.sql")):
                print(f"-> {f.relative_to(ROOT)}")
                run_file(cur, f)
            print("Schéma créé.")
        else:
            run_file(cur, Path(sys.argv[2]), show=True)


if __name__ == "__main__":
    main()
