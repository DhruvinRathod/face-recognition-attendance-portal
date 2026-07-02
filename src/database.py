"""SQLite helpers for the local attendance prototype."""
from __future__ import annotations
import sqlite3
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "attendance.db"

def connect(db_path: Path | str = DB_PATH) -> sqlite3.Connection:
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: Path | str = DB_PATH) -> None:
    with connect(db_path) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS students (
            student_id TEXT PRIMARY KEY, name TEXT NOT NULL,
            folder_name TEXT NOT NULL, registered_at TEXT NOT NULL)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL, attendance_date TEXT NOT NULL,
            attendance_time TEXT NOT NULL, source TEXT NOT NULL,
            recognition_distance REAL NOT NULL,
            UNIQUE(student_id, attendance_date),
            FOREIGN KEY(student_id) REFERENCES students(student_id))""")

def upsert_student(student_id: str, name: str, folder_name: str, db_path: Path | str = DB_PATH) -> None:
    init_db(db_path)
    with connect(db_path) as conn:
        conn.execute("""INSERT INTO students(student_id,name,folder_name,registered_at)
            VALUES(?,?,?,?) ON CONFLICT(student_id) DO UPDATE SET
            name=excluded.name, folder_name=excluded.folder_name""",
            (student_id, name, folder_name, datetime.now().isoformat(timespec="seconds")))

def mark_attendance(student_id: str, source: str, recognition_distance: float, db_path: Path | str = DB_PATH) -> bool:
    init_db(db_path)
    now = datetime.now()
    with connect(db_path) as conn:
        result = conn.execute("""INSERT OR IGNORE INTO attendance
            (student_id,attendance_date,attendance_time,source,recognition_distance)
            VALUES(?,?,?,?,?)""", (student_id, now.date().isoformat(),
            now.isoformat(timespec="seconds"), source, float(recognition_distance)))
        return result.rowcount == 1

def attendance_rows(db_path: Path | str = DB_PATH):
    init_db(db_path)
    with connect(db_path) as conn:
        return conn.execute("""SELECT a.student_id,s.name,a.attendance_date,a.attendance_time,
            a.source,a.recognition_distance FROM attendance a JOIN students s
            ON a.student_id=s.student_id ORDER BY a.attendance_time DESC""").fetchall()
