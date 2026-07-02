"""Recognize a face in a webcam/video stream and mark daily attendance."""
from __future__ import annotations
import argparse, json
from collections import defaultdict
from pathlib import Path
import cv2
from database import mark_attendance

ROOT=Path(__file__).resolve().parents[1]
MODEL=ROOT/"models"/"lbph_face_model.yml"; LABELS=ROOT/"models"/"labels.json"
def source(v): return int(v) if v.isdigit() else v
def largest(faces): return max(faces,key=lambda f:f[2]*f[3]) if len(faces) else None

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",default="0",help="0 for webcam, or a path to .mp4/.avi")
    p.add_argument("--threshold",type=float,default=65.0,help="LBPH distance limit; lower is stricter")
    p.add_argument("--confirm-frames",type=int,default=8,help="Frames needed before marking")
    a=p.parse_args()
    if not hasattr(cv2,"face"): raise RuntimeError("cv2.face missing. Install opencv-contrib-python.")
    if not MODEL.exists() or not LABELS.exists(): raise RuntimeError("Model not found. Run: python src/train_model.py")
    labels=json.loads(LABELS.read_text(encoding="utf-8"))
    recognizer=cv2.face.LBPHFaceRecognizer_create(); recognizer.read(str(MODEL))
    cascade=cv2.CascadeClassifier(cv2.data.haarcascades+"haarcascade_frontalface_default.xml")
    src=source(a.source); cap=cv2.VideoCapture(src)
    if not cap.isOpened(): raise RuntimeError("Cannot open camera/video. Check source or permissions.")
    candidates=defaultdict(int); stream_name="webcam" if isinstance(src,int) else Path(src).name; status="Waiting for registered face"
    try:
        while True:
            ok,frame=cap.read()
            if not ok: break
            gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
            face=largest(cascade.detectMultiScale(gray,1.2,5,minSize=(120,120)))
            if face is None:
                candidates.clear()
            else:
                x,y,w,h=face; crop=cv2.equalizeHist(cv2.resize(gray[y:y+h,x:x+w],(200,200)))
                label,distance=recognizer.predict(crop); person=labels.get(str(label))
                matched=person is not None and distance<=a.threshold
                color=(0,0,255); text=f"Unknown ({distance:.1f})"
                if matched:
                    candidates[label]+=1
                    for other in list(candidates):
                        if other!=label: candidates[other]=0
                    text=f"{person['name']} ({distance:.1f})"; color=(0,255,0)
                    status=f"Recognizing {person['name']}: {candidates[label]}/{a.confirm_frames}"
                    if candidates[label]>=a.confirm_frames:
                        new=mark_attendance(person["student_id"],stream_name,distance)
                        status=(f"Attendance marked: {person['name']}" if new else f"Already marked today: {person['name']}")
                        candidates[label]=0
                else:
                    candidates.clear(); status="Unknown face — no attendance marked"
                cv2.rectangle(frame,(x,y),(x+w,y+h),color,2)
                cv2.putText(frame,text,(x,max(25,y-10)),cv2.FONT_HERSHEY_SIMPLEX,.7,color,2)
            cv2.putText(frame,status,(10,30),cv2.FONT_HERSHEY_SIMPLEX,.62,(255,255,255),2)
            cv2.putText(frame,"q: quit",(10,frame.shape[0]-15),cv2.FONT_HERSHEY_SIMPLEX,.55,(255,255,255),1)
            cv2.imshow("Live attendance — q to quit",frame)
            if cv2.waitKey(1)&0xFF==ord("q"): break
    finally:
        cap.release(); cv2.destroyAllWindows()
if __name__=="__main__": main()
