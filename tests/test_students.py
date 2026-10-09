import os
import tempfile

os.environ["STUDENTS_DB"] = os.path.join(tempfile.mkdtemp(), "test.db")

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

NEW = {"name": "Test User", "date_of_birth": "2004-04-04",
       "email": "test@example.com", "course": "CS"}


def test_full_crud_flow():
    with TestClient(app) as c:
        r = c.post("/students", json=NEW)
        assert r.status_code == 201
        sid = r.json()["id"]

        assert c.post("/students", json=NEW).status_code == 409          # duplicate email
        assert c.get(f"/students/{sid}").json()["name"] == "Test User"
        assert c.get("/students?course=cs").headers["X-Total-Count"] == "1"

        r = c.patch(f"/students/{sid}", json={"phone": "+91 98765 43210"})
        assert r.status_code == 200 and r.json()["phone"] == "+91 98765 43210"

        r = c.put(f"/students/{sid}", json={**NEW, "name": "Renamed User"})
        assert r.json()["name"] == "Renamed User"

        assert c.delete(f"/students/{sid}").status_code == 200
        assert c.get(f"/students/{sid}").status_code == 404
        assert c.delete(f"/students/{sid}").status_code == 404


def test_validation():
    with TestClient(app) as c:
        assert c.post("/students", json={"name": "A", "date_of_birth": "2004-01-01", "email": "a@b.co"}).status_code == 422
        assert c.post("/students", json={"name": "No Contact", "date_of_birth": "2004-01-01"}).status_code == 422
        assert c.post("/students", json={**NEW, "email": "bad-email"}).status_code == 422
        assert c.post("/students", json={**NEW, "date_of_birth": "2999-01-01"}).status_code == 422


def test_ai_fallback_is_grounded():
    with TestClient(app) as c:
        c.post("/students", json={"name": "Old Timer", "date_of_birth": "2001-01-01", "email": "old@example.com"})
        c.post("/students", json={"name": "Young Gun", "date_of_birth": "2006-06-06", "email": "young@example.com"})
        r = c.post("/ai/ask", json={"question": "List students born after 2005"}).json()
        names = [s["name"] for s in r["records_used"]]
        assert "Young Gun" in names and "Old Timer" not in names
