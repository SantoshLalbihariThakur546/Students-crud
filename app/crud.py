"""All database access. Every query is parameterised (no SQL injection)."""
import sqlite3
from typing import Optional

COLUMNS = ["name", "date_of_birth", "email", "phone", "course", "address", "enrollment_date"]


def _iso(v):
    return v.isoformat() if hasattr(v, "isoformat") else v


def _where(name=None, course=None, email=None, born_after=None, born_before=None):
    clauses, params = [], []
    if name:
        clauses.append("name LIKE ?")
        params.append(f"%{name}%")
    if course:
        clauses.append("course LIKE ?")
        params.append(f"%{course}%")
    if email:
        clauses.append("email = ?")
        params.append(email.strip().lower())
    if born_after:
        clauses.append("date_of_birth >= ?")
        params.append(_iso(born_after))
    if born_before:
        clauses.append("date_of_birth <= ?")
        params.append(_iso(born_before))
    sql = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    return sql, params


def create_student(conn: sqlite3.Connection, data: dict) -> dict:
    params = {c: _iso(data.get(c)) for c in COLUMNS}
    cols = ", ".join(COLUMNS)
    marks = ", ".join(f":{c}" for c in COLUMNS)
    cur = conn.execute(f"INSERT INTO students ({cols}) VALUES ({marks})", params)
    conn.commit()
    return get_student(conn, cur.lastrowid)


def get_student(conn: sqlite3.Connection, student_id: int) -> Optional[dict]:
    row = conn.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    return dict(row) if row else None


def list_students(conn, *, limit=100, offset=0, **filters) -> list:
    where, params = _where(**filters)
    rows = conn.execute(
        f"SELECT * FROM students{where} ORDER BY id LIMIT ? OFFSET ?",
        params + [limit, offset],
    ).fetchall()
    return [dict(r) for r in rows]


def count_students(conn, **filters) -> int:
    where, params = _where(**filters)
    return conn.execute(f"SELECT COUNT(*) FROM students{where}", params).fetchone()[0]


def distinct_courses(conn) -> list:
    rows = conn.execute(
        "SELECT DISTINCT course FROM students WHERE course IS NOT NULL ORDER BY course"
    ).fetchall()
    return [r[0] for r in rows]


def update_student(conn, student_id: int, data: dict) -> Optional[dict]:
    params = {c: _iso(data.get(c)) for c in COLUMNS}
    params["id"] = student_id
    sets = ", ".join(f"{c} = :{c}" for c in COLUMNS)
    cur = conn.execute(f"UPDATE students SET {sets} WHERE id = :id", params)
    conn.commit()
    if cur.rowcount == 0:
        return None
    return get_student(conn, student_id)


def delete_student(conn, student_id: int) -> bool:
    cur = conn.execute("DELETE FROM students WHERE id = ?", (student_id,))
    conn.commit()
    return cur.rowcount > 0
