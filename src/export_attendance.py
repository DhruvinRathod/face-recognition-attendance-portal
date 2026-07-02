"""Export local attendance records to CSV."""
from __future__ import annotations
import csv
from datetime import date
from pathlib import Path
from database import attendance_rows
ROOT=Path(__file__).resolve().parents[1]
def main():
    out_dir=ROOT/"data"/"exports"; out_dir.mkdir(parents=True,exist_ok=True)
    output=out_dir/f"attendance_{date.today().isoformat()}.csv"; rows=attendance_rows()
    with output.open("w",newline="",encoding="utf-8") as f:
        writer=csv.writer(f); writer.writerow(["student_id","name","attendance_date","attendance_time","source","recognition_distance"])
        for row in rows: writer.writerow([row[k] for k in row.keys()])
    print(f"Exported {len(rows)} record(s) to {output}")
if __name__=="__main__": main()
