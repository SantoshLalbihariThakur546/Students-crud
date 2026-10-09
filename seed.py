"""Insert DUMMY students (fake data only). Run:  python seed.py"""
from app import crud
from app.database import get_connection, init_db

DUMMY = [
    ("Aarav Sharma",  "2004-05-17", "aarav.sharma@example.com", "+91 90000 00001", "Computer Science", "Amritsar, Punjab", "2022-08-01"),
    ("Priya Singh",   "2005-11-02", "priya.singh@example.com",  "+91 90000 00002", "Data Science",     "Ludhiana, Punjab", "2023-08-01"),
    ("Rohan Verma",   "2006-03-21", "rohan.verma@example.com",  None,             "Cyber Security",    "Jalandhar, Punjab", "2024-08-01"),
    ("Simran Kaur",   "2003-09-09", "simran.kaur@example.com",  "+91 90000 00004", "AI & ML",          "Patiala, Punjab", "2021-08-01"),
    ("Karan Mehta",   "2007-01-14", None,                       "+91 90000 00005", "Computer Science", "Chandigarh", "2025-08-01"),
    ("Neha Gupta",    "2005-06-30", "neha.gupta@example.com",   "+91 90000 00006", "Data Science",     "Delhi", "2023-08-01"),
    ("Aditya Rao",    "2002-12-25", "aditya.rao@example.com",   "+91 90000 00007", "Cyber Security",   "Pune", "2020-08-01"),
    ("Meera Nair",    "2006-08-08", "meera.nair@example.com",   "+91 90000 00008", "AI & ML",          "Kochi", "2024-08-01"),
    ("Harpreet Gill", "2004-02-11", "harpreet.gill@example.com", None,            "Computer Science", "Bathinda, Punjab", "2022-08-01"),
    ("Ananya Das",    "2007-07-19", "ananya.das@example.com",   "+91 90000 00010", "Data Science",     "Kolkata", "2025-08-01"),
]
KEYS = ["name", "date_of_birth", "email", "phone", "course", "address", "enrollment_date"]

init_db()
conn = get_connection()
if crud.count_students(conn):
    print("Database already has data; nothing inserted.")
else:
    for row in DUMMY:
        crud.create_student(conn, dict(zip(KEYS, row)))
    print(f"Inserted {len(DUMMY)} dummy students.")
conn.close()
