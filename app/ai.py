"""Optional bonus: natural-language questions answered by a local Ollama model.

Security design (matches the assignment):
  * The model NEVER writes or runs SQL.
  * Backend code decides which records are relevant (fixed, parameterised
    queries through crud.py) and passes only those rows as context.
  * temperature=0 and a strict system prompt keep answers grounded.
  * If Ollama is not running, a rule-based answer built from the same
    retrieved records is returned, so the endpoint never breaks.
"""
import json
import os
import re
import urllib.error
import urllib.request

from . import crud

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
MAX_CONTEXT_ROWS = 50

YEAR_RE = re.compile(r"\b(19\d{2}|20\d{2})\b")
COUNT_RE = re.compile(r"\b(how many|count|number of|total)\b")

SYSTEM_PROMPT = (
    "You are an assistant for a student records system. Answer ONLY using the "
    "records provided in the message. Never invent students or fields. If the "
    "answer is not in the records, say you do not have that information. "
    "Use the TOTAL numbers exactly as given for any counting question. "
    "Keep the answer short and clear."
)


# ---------- 1. Retrieval (plain Python, no model involved) ----------
def retrieve(conn, question: str) -> dict:
    q = question.lower()
    filters, notes = {}, []

    m = YEAR_RE.search(q)
    if m:
        y = int(m.group(1))
        if re.search(r"\b(after|later than)\b", q):
            filters["born_after"] = f"{y + 1}-01-01"
            notes.append(f"born after {y}")
        elif re.search(r"\b(before|earlier than|prior to)\b", q):
            filters["born_before"] = f"{y - 1}-12-31"
            notes.append(f"born before {y}")
        elif "born" in q or re.search(r"\bin\b", q):
            filters["born_after"] = f"{y}-01-01"
            filters["born_before"] = f"{y}-12-31"
            notes.append(f"born in {y}")

    for course in crud.distinct_courses(conn):
        if course.lower() in q:
            filters["course"] = course
            notes.append(f"course = {course}")
            break

    matched = None
    if not filters:  # try to find a student mentioned by name
        words = set(re.findall(r"[a-z]+", q))
        everyone = crud.list_students(conn, limit=500)
        matched = [
            s for s in everyone
            if s["name"].lower() in q
            or any(len(t) > 2 and t in words for t in s["name"].lower().split())
        ]
        if matched:
            notes.append("name mentioned in question")

    if matched:
        students, total = matched[:MAX_CONTEXT_ROWS], len(matched)
    else:
        students = crud.list_students(conn, limit=MAX_CONTEXT_ROWS, **filters)
        total = crud.count_students(conn, **filters)

    return {
        "filters": filters,
        "description": ", ".join(notes) if notes else "all students",
        "students": students,
        "total_matching": total,
        "total_in_db": crud.count_students(conn),
    }


# ---------- 2. Prompt + model call ----------
def build_prompt(question: str, ctx: dict) -> str:
    lines = [
        f"TOTAL_STUDENTS_IN_DATABASE: {ctx['total_in_db']}",
        f"TOTAL_MATCHING_THE_QUESTION ({ctx['description']}): {ctx['total_matching']}",
        "RECORDS:",
    ]
    for s in ctx["students"]:
        lines.append(
            f"- id={s['id']}; name={s['name']}; dob={s['date_of_birth']}; "
            f"email={s['email']}; phone={s['phone']}; course={s['course']}; "
            f"enrolled={s['enrollment_date']}"
        )
    if not ctx["students"]:
        lines.append("(no matching records)")
    lines.append(f"\nQUESTION: {question}")
    return "\n".join(lines)


def call_ollama(prompt: str):
    payload = json.dumps({
        "model": OLLAMA_MODEL,
        "stream": False,
        "options": {"temperature": 0},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    }).encode()
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/chat", data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            return json.loads(resp.read())["message"]["content"].strip()
    except (urllib.error.URLError, TimeoutError, OSError, KeyError, ValueError):
        return None


# ---------- 3. Fallback when Ollama is offline ----------
def fallback_answer(question: str, ctx: dict) -> str:
    n, desc = ctx["total_matching"], ctx["description"]
    if COUNT_RE.search(question.lower()):
        return f"There are {n} student(s) ({desc})."
    if n == 0:
        return f"No students found ({desc})."
    items = "; ".join(f"{s['name']} (DOB {s['date_of_birth']})" for s in ctx["students"])
    return f"Found {n} student(s) ({desc}): {items}"


def answer_question(conn, question: str) -> dict:
    ctx = retrieve(conn, question)
    reply = call_ollama(build_prompt(question, ctx))
    if reply:
        answer, source = reply, "ollama"
    else:
        answer = fallback_answer(question, ctx) + "  (Ollama offline: answered from retrieved records)"
        source = "fallback"
    return {
        "question": question,
        "answer": answer,
        "source": source,
        "model": OLLAMA_MODEL if source == "ollama" else None,
        "filters_applied": ctx["filters"],
        "records_used": [
            {"id": s["id"], "name": s["name"], "date_of_birth": s["date_of_birth"]}
            for s in ctx["students"]
        ],
    }
