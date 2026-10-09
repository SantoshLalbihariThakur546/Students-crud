"""FastAPI application: routes only. Logic lives in crud.py / schemas.py / ai.py."""
import sqlite3
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError

from . import ai, crud
from .database import get_db, init_db
from .schemas import (AskRequest, AskResponse, StudentCreate, StudentOut,
                      StudentUpdate)

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()          # creates students.db + table on first run
    yield


app = FastAPI(
    title="Students Database CRUD API",
    description="EWB internship project: FastAPI + SQLite (+ optional Ollama AI).",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count"],
)


# ---------- error handling ----------
@app.exception_handler(sqlite3.IntegrityError)
def integrity_error_handler(request, exc: sqlite3.IntegrityError):
    msg = ("A student with this email already exists."
           if "UNIQUE" in str(exc) else "Database constraint failed.")
    return JSONResponse(status_code=409, content={"detail": msg})


def _not_found(student_id: int) -> HTTPException:
    return HTTPException(status_code=404, detail=f"Student with id {student_id} not found")


# ---------- CREATE ----------
@app.post("/students", response_model=StudentOut, status_code=201, tags=["Students"])
def create_student(student: StudentCreate, conn: sqlite3.Connection = Depends(get_db)):
    return crud.create_student(conn, student.model_dump())


# ---------- READ (list + filter) ----------
@app.get("/students", response_model=List[StudentOut], tags=["Students"])
def list_students(
    response: Response,
    name: Optional[str] = Query(None, description="Partial name match"),
    course: Optional[str] = Query(None, description="Partial course match"),
    email: Optional[str] = Query(None, description="Exact email"),
    born_after: Optional[date] = Query(None, description="DOB on/after YYYY-MM-DD"),
    born_before: Optional[date] = Query(None, description="DOB on/before YYYY-MM-DD"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    conn: sqlite3.Connection = Depends(get_db),
):
    filters = dict(name=name, course=course, email=email,
                   born_after=born_after, born_before=born_before)
    response.headers["X-Total-Count"] = str(crud.count_students(conn, **filters))
    return crud.list_students(conn, limit=limit, offset=offset, **filters)


# ---------- READ (single) ----------
@app.get("/students/{student_id}", response_model=StudentOut, tags=["Students"])
def get_student(student_id: int, conn: sqlite3.Connection = Depends(get_db)):
    student = crud.get_student(conn, student_id)
    if student is None:
        raise _not_found(student_id)
    return student


# ---------- UPDATE (full replace) ----------
@app.put("/students/{student_id}", response_model=StudentOut, tags=["Students"])
def replace_student(student_id: int, student: StudentCreate,
                    conn: sqlite3.Connection = Depends(get_db)):
    updated = crud.update_student(conn, student_id, student.model_dump())
    if updated is None:
        raise _not_found(student_id)
    return updated


# ---------- UPDATE (partial) ----------
@app.patch("/students/{student_id}", response_model=StudentOut, tags=["Students"])
def patch_student(student_id: int, changes: StudentUpdate,
                  conn: sqlite3.Connection = Depends(get_db)):
    existing = crud.get_student(conn, student_id)
    if existing is None:
        raise _not_found(student_id)
    merged = {c: existing[c] for c in crud.COLUMNS}
    merged.update(changes.model_dump(exclude_unset=True))
    try:  # re-validate the final record (e.g. still has a contact)
        valid = StudentCreate(**merged)
    except ValidationError as exc:
        raise RequestValidationError(exc.errors(include_context=False, include_url=False))
    return crud.update_student(conn, student_id, valid.model_dump())


# ---------- DELETE ----------
@app.delete("/students/{student_id}", tags=["Students"])
def delete_student(student_id: int, conn: sqlite3.Connection = Depends(get_db)):
    if not crud.delete_student(conn, student_id):
        raise _not_found(student_id)
    return {"message": f"Student {student_id} deleted successfully"}


# ---------- OPTIONAL: local AI ----------
@app.post("/ai/ask", response_model=AskResponse, tags=["AI (optional)"])
def ask_ai(body: AskRequest, conn: sqlite3.Connection = Depends(get_db)):
    return ai.answer_question(conn, body.question)


# ---------- health + frontend ----------
@app.get("/health", tags=["System"])
def health():
    return {"status": "ok"}


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC_DIR / "index.html")
