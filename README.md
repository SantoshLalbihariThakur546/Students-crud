# Students Database CRUD Application

EWB Edu Tech internship project: a Python backend that manages student records
(Create, Read, Update, Delete) using **FastAPI** and **SQLite**, with a simple
web frontend and an **optional local AI extension (Ollama)**.

> All sample data is dummy data. Never commit real student information.

## Features

- Full CRUD API: `POST / GET / PUT / PATCH / DELETE /students`
- Filtering: name, course, email, born_after, born_before, pagination
- Input validation (name, date of birth, email, phone, contact required) and
  proper `404` / `409` / `422` errors
- SQLite file database (`students.db`) that persists between runs
- Web UI at `http://127.0.0.1:8000/` and Swagger docs at `/docs`
- Optional: ask questions in plain English through a local Ollama model
  (answers are grounded in records fetched by backend code; the model never runs SQL)

## Project structure

```
students-crud/
├── app/
│   ├── main.py        # FastAPI routes + error handling + serves the frontend
│   ├── schemas.py     # Pydantic models and validation rules
│   ├── crud.py        # All SQL (parameterised) for create/read/update/delete
│   ├── database.py    # SQLite connection + table creation
│   └── ai.py          # Optional Ollama integration
├── static/index.html  # Frontend (HTML + CSS + JavaScript)
├── tests/test_students.py
├── seed.py            # Inserts dummy students
├── requirements.txt
└── README.md
```

## Prerequisites

- Python 3.9 or newer (`python --version`)
- pip
- (Optional) [Ollama](https://ollama.com) for the AI bonus

## Installation
    python -m venv venv
    venv\Scripts\activate
    python -m pip install -r requirements.txt
    python seed.py
    uvicorn app.main:app --reload
```bash
# 1. open the project folder
cd students-crud

# 2. create and activate a virtual environment
python -m venv venv
# Windows:      venv\Scripts\activate
# macOS/Linux:  source venv/bin/activate

# 3. install dependencies
pip install -r requirements.txt
```

## Run

```bash
python seed.py                         # optional: add 10 dummy students
uvicorn app.main:app --reload          # start the server
```

Open:

| URL | What |
|-----|------|
| http://127.0.0.1:8000/ | Frontend |
| http://127.0.0.1:8000/docs | Interactive API docs (Swagger UI) |

The database file `students.db` is created automatically on first start.

## API endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/students` | Create a student (201) |
| GET | `/students` | List / filter (header `X-Total-Count` = total matches) |
| GET | `/students/{id}` | View one student (404 if missing) |
| PUT | `/students/{id}` | Replace all details |
| PATCH | `/students/{id}` | Update only the fields sent |
| DELETE | `/students/{id}` | Delete a student |
| POST | `/ai/ask` | Optional: natural-language question |

Filter query parameters for `GET /students`: `name`, `course`, `email`,
`born_after`, `born_before` (YYYY-MM-DD), `limit` (1-500), `offset`.

## Testing the API (curl)

```bash
# Create
curl -X POST http://127.0.0.1:8000/students -H "Content-Type: application/json" \
  -d '{"name":"Test Student","date_of_birth":"2004-05-17","email":"test@example.com","phone":"+91 90000 00099","course":"Computer Science","enrollment_date":"2024-08-01"}'

# List and filter
curl http://127.0.0.1:8000/students
curl "http://127.0.0.1:8000/students?course=data&born_after=2005-01-01"

# View one
curl http://127.0.0.1:8000/students/1

# Partial update
curl -X PATCH http://127.0.0.1:8000/students/1 -H "Content-Type: application/json" \
  -d '{"course":"AI & ML"}'

# Full update
curl -X PUT http://127.0.0.1:8000/students/1 -H "Content-Type: application/json" \
  -d '{"name":"Test Student","date_of_birth":"2004-05-17","email":"test@example.com","course":"Cyber Security"}'

# Delete
curl -X DELETE http://127.0.0.1:8000/students/1

# Error cases
curl http://127.0.0.1:8000/students/9999                       # 404
curl -X POST http://127.0.0.1:8000/students -H "Content-Type: application/json" \
  -d '{"name":"X","date_of_birth":"2004-01-01"}'               # 422 (bad name, no contact)
```

Automated tests:

```bash
pip install pytest httpx
pytest -v
```

## Optional: local AI with Ollama

```bash
ollama pull llama3.2:1b
ollama serve            # if it is not already running
```

Then use the "Ask about the data" box in the UI, or:

```bash
curl -X POST http://127.0.0.1:8000/ai/ask -H "Content-Type: application/json" \
  -d '{"question":"List students born after 2005"}'
```

Environment variables (optional): `OLLAMA_URL` (default `http://localhost:11434`),
`OLLAMA_MODEL` (default `llama3.2:1b`).

How it stays safe and accurate:

1. Backend code reads the question, picks fixed filters (year, course, name) and
   fetches matching rows with parameterised queries.
2. Only those rows (plus exact counts) are sent to the model as context.
3. The model has `temperature=0` and is told to answer only from the records.
4. The model never writes or executes SQL. If Ollama is offline, the API answers
   from the same retrieved records instead of failing.

## Upload to GitHub

```bash
git init
git add .
git commit -m "Students CRUD app with FastAPI and SQLite"
git branch -M main
git remote add origin https://github.com/<your-username>/students-crud.git
git push -u origin main
```

`.gitignore` already excludes `students.db`, `venv/` and `.env`.
