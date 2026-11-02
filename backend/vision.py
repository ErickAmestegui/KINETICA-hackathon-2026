"""Local OpenCV baseline. Feature points are not segmentation or inferred joints."""
import math
import cv2
import numpy as np


def inspect_video(path):
    cap = cv2.VideoCapture(str(path))
    try:
        fps = cap.get(cv2.CAP_PROP_FPS)
        count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        ok, _ = cap.read()
        if not ok or not math.isfinite(fps) or fps <= 0 or count <= 1:
            raise ValueError("Video cannot be decoded; use H.264 MP4 or a compatible MOV")
        if w*h > 1920*1080 or count/fps > 60.1 or count > 3600:
            raise ValueError("MVP limit: 60 seconds, 1080p, 3600 frames. Trim the clip first.")
        # Retain decoder timestamps rather than silently imposing CFR.
        times = [max(0., cap.get(cv2.CAP_PROP_POS_MSEC)/1000)]
        while True:
            ok, _ = cap.read()
            if not ok:
                break
            times.append(cap.get(cv2.CAP_PROP_POS_MSEC)/1000)
        reliable = len(times) > 1 and all(b > a for a,b in zip(times,times[1:]))
        if not reliable:
            raise ValueError("Decoder did not provide monotonic frame timestamps. Transcode to constant-frame-rate H.264 MP4.")
        return {"fps": fps, "frames": len(times), "width": w, "height": h, "duration": times[-1]+1/fps,
                "timestamps": times, "timing": "OpenCV decoder presentation timestamps"}
    finally:
        cap.release()


def track_points(path, seeds, start_frame, max_frames=600, timestamps=None):
    cap = cv2.VideoCapture(str(path))
    try:
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        ok, frame = cap.read()
        if not ok:
            raise ValueError("Cannot read seed frame")
        h,w=frame.shape[:2]
        for seed in seeds:
            if not (0 <= seed['x'] < w and 0 <= seed['y'] < h):
                raise ValueError("Point outside frame")
        prev = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        points = np.array([[s['x'],s['y']] for s in seeds], dtype=np.float32).reshape(-1,1,2)
        ids = list(range(len(seeds)))
        tracks, lost = [], []
        fps = cap.get(cv2.CAP_PROP_FPS)
        def time_at(i):
            return timestamps[i] if timestamps and i < len(timestamps) else i/fps
        for index in range(start_frame+1, start_frame+1+max_frames):
            ok, frame = cap.read()
            if not ok or not ids:
                break
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            nxt, status, errors = cv2.calcOpticalFlowPyrLK(prev,gray,points,None,winSize=(25,25),maxLevel=3)
            if nxt is None:
                lost.extend({"joint": seeds[i]['joint'], "frame": index, "reason": "no flow"} for i in ids)
                break
            back, back_status, _ = cv2.calcOpticalFlowPyrLK(gray,prev,nxt,None,winSize=(25,25),maxLevel=3)
            survivors=[]
            for k,identity in enumerate(ids):
                x,y = map(float,nxt[k,0])
                fb = float(np.linalg.norm(back[k]-points[k])) if back is not None else math.inf
                good = bool(status[k,0]) and back is not None and bool(back_status[k,0]) and fb < 1.5 and float(errors[k,0]) < 30 and 0 <= x < w and 0 <= y < h
                if not good:
                    lost.append({"joint": seeds[identity]['joint'], "frame": index, "reason": "forward/backward or photometric check failed"})
                    continue
                survivors.append(k)
                tracks.append({"frame": index, "t": time_at(index), "x": x, "y": y, "joint": seeds[identity]['joint'],
                               "source": "opencv-lk", "split": "validation" if timestamps and index>=int(len(timestamps)*.75) else "fit"})
            if not survivors:
                break
            points=nxt[survivors]
            ids=[ids[k] for k in survivors]
            prev=gray
        return {"observations": tracks, "lost": lost, "method": "OpenCV pyramidal LK; forward/backward threshold 1.5 px, photometric error < 30", "provenance": "local baseline, not Meta"}
    finally:
        cap.release()
