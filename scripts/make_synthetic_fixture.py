"""Generate ORIGINAL, explicitly synthetic test footage; never real evidence."""
import csv
import json
import subprocess
from pathlib import Path
import cv2
import numpy as np
import imageio_ffmpeg
from backend.kinematics import Parameters, Calibration, solve, project

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'output'; OUT.mkdir(exist_ok=True)
p=Parameters(r=32,L=128,rpm=30)
cal=Calibration(ox=100,oy=180,scale=1.5)
fps=30; count=120
ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
cmd=[ffmpeg,'-y','-loglevel','error','-f','rawvideo','-vcodec','rawvideo','-pix_fmt','bgr24','-s','640x360','-r',str(fps),'-i','-','-an','-vcodec','libx264','-pix_fmt','yuv420p','-crf','16','-movflags','+faststart',str(OUT/'synthetic-slider-crank.mp4')]
process=subprocess.Popen(cmd,stdin=subprocess.PIPE)
rows=[]
for i in range(count):
    t=i/fps; state=solve(p,t)
    a=np.round(project(state['A'],cal)).astype(int);b=np.round(project(state['B'],cal)).astype(int)
    image=np.full((360,640,3),(235,239,235),np.uint8)
    cv2.putText(image,'SYNTHETIC TEST FIXTURE - NOT REAL FOOTAGE',(22,30),cv2.FONT_HERSHEY_SIMPLEX,.57,(70,86,90),1,cv2.LINE_AA)
    cv2.line(image,(180,202),(400,202),(140,160,156),3)
    cv2.line(image,(100,180),tuple(a),(95,116,49),5)
    cv2.line(image,tuple(a),tuple(b),(150,158,160),5)
    cv2.circle(image,(100,180),6,(70,80,70),-1)
    for joint,pt in [('crank',a),('slider',b)]:
        # A rich corner pattern gives LK a measurable local baseline.
        x,y=pt; cv2.rectangle(image,(x-9,y-9),(x+9,y+9),(25,45,50),-1)
        cv2.rectangle(image,(x-4,y-4),(x+4,y+4),(235,245,245),-1)
        cv2.circle(image,(x,y),2,(30,80,100),-1)
        exact=project(state['A' if joint=='crank' else 'B'],cal)
        rows.append({'frame':i,'t':t,'x':float(exact[0]),'y':float(exact[1]),'joint':joint,'source':'synthetic','split':'fit' if i<90 else 'validation'})
    process.stdin.write(image.tobytes())
process.stdin.close()
if process.wait()!=0: raise RuntimeError('FFmpeg fixture encoding failed')
with (OUT/'synthetic-ground-truth.csv').open('w',newline='') as file:
    writer=csv.DictWriter(file,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
(OUT/'synthetic-fixture.json').write_text(json.dumps({'label':'SYNTHETIC TEST ONLY','parameters':p.model_dump(),'calibration':cal.model_dump(),'frames':count,'fps':fps},indent=2))
print('Created synthetic-slider-crank.mp4 and ground truth in output/. Not evidence of real reconstruction.')
