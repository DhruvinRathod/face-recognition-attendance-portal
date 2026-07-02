from pathlib import Path
from src.database import init_db, upsert_student, mark_attendance, attendance_rows

def test_prevents_duplicate_daily_attendance(tmp_path: Path):
    db=tmp_path/"attendance.db"; init_db(db)
    upsert_student("101","Test Student","101__test_student",db)
    assert mark_attendance("101","demo.mp4",42.3,db) is True
    assert mark_attendance("101","demo.mp4",40.1,db) is False
    assert len(attendance_rows(db)) == 1
