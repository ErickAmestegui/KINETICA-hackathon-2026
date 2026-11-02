"""Offline frame/contour discontinuity investigation. No Meta transport imported."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.mask_motion import audit_masks


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project',type=Path,required=True)
    args=parser.parse_args()
    project=json.loads(args.project.read_text('utf-8'))
    video=project['video'];identity=video['id']
    if len(identity)!=32 or any(c not in '0123456789abcdef' for c in identity):raise ValueError('Invalid video ID')
    folder=ROOT/'data'/identity
    meta=json.loads((folder/'metadata.json').read_text('utf-8'))
    source=folder/('source'+meta['extension'])
    cap=cv2.VideoCapture(str(source));frames=[]
    while True:
        ok,frame=cap.read()
        if not ok:break
        frames.append(frame)
    cap.release()
    if len(frames)!=meta['frames']:raise ValueError('Decoded frame count differs')
    audit=audit_masks(project['samResult'],meta)
    gray=[cv2.cvtColor(f,cv2.COLOR_BGR2GRAY) for f in frames]
    pairs=[]
    # Upper right background, excluding the mechanical motion. This is a declared
    # Eitech-specific diagnostic ROI, not an automatically inferred world reference.
    roi=np.zeros_like(gray[0]);h,w=roi.shape;roi[:int(h*.55),int(w*.40):]=255
    for i,(a,b) in enumerate(zip(gray,gray[1:])):
        points=cv2.goodFeaturesToTrack(a,200,.01,8,mask=roi)
        row={'from_frame':i,'to_frame':i+1,'image_mae':float(np.abs(a.astype(float)-b).mean()),'identical_decoded_pixels':bool(np.array_equal(a,b))}
        if points is not None:
            q,ok,_=cv2.calcOpticalFlowPyrLK(a,b,points,None)
            back,ok_back,_=cv2.calcOpticalFlowPyrLK(b,a,q,None)
            valid=ok.ravel().astype(bool)&ok_back.ravel().astype(bool)&(np.linalg.norm(points-back,axis=2).ravel()<1.)
            p0=points[valid].reshape(-1,2);p1=q[valid].reshape(-1,2)
            row['background_tracks']=len(p0)
            if len(p0)>=6:
                cv2.setRNGSeed(0)
                transform,inliers=cv2.estimateAffinePartial2D(p0,p1,method=cv2.RANSAC,ransacReprojThreshold=1.5)
                if transform is not None:
                    residual=np.linalg.norm(p1-(p0@transform[:,:2].T+transform[:,2]),axis=1)
                    row.update(background_affine=transform.tolist(),inliers=int(inliers.sum()),median_residual_px=float(np.median(residual)),median_shift_px=np.median(p1-p0,axis=0).tolist())
        row['mask_steps']={}
        for obj in audit['objects']:
            samples={s['frame']:s for s in obj['samples']}
            if i in samples and i+1 in samples:
                p,q=samples[i],samples[i+1]
                row['mask_steps'][obj['object_id']]=[q['x']-p['x'],q['y']-p['y']]
        pairs.append(row)
    out=ROOT/'output'/'sam-motion'/'discontinuity';out.mkdir(parents=True,exist_ok=True)
    report={'video_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'decoded_frames':len(frames),'background_roi_fraction':[.4,0,1,.55],
        'method':'Local OpenCV LK forward/backward <1 px; affine RANSAC 1.5 px. Background ROI manually declared for this Eitech clip.',
        'limitations':['Image registration is diagnostic, not physical calibration.','Masks and raw video retained unchanged.','No inference, correction, retiming or exclusion performed.'], 'pairs':pairs}
    (out/'frame-diagnostics.json').write_text(json.dumps(report,indent=2,allow_nan=False),'utf-8')
    tiles=[]
    for i in range(35,min(43,len(frames))):
        frame=frames[i].copy()
        for obj in audit['objects']:
            s=next((s for s in obj['samples'] if s['frame']==i),None)
            if s:
                point=(round(s['x']),round(s['y']))
                cv2.circle(frame,point,7,(0,185,255),2)
                cv2.putText(frame,'#'+obj['object_id'],(point[0]+10,point[1]),cv2.FONT_HERSHEY_SIMPLEX,.6,(0,185,255),2)
        cv2.putText(frame,f'SOURCE FRAME {i}',(15,25),cv2.FONT_HERSHEY_SIMPLEX,.7,(0,0,0),3)
        cv2.putText(frame,f'SOURCE FRAME {i}',(15,25),cv2.FONT_HERSHEY_SIMPLEX,.7,(255,255,255),1)
        tiles.append(cv2.resize(frame,(480,270)))
    if len(tiles)==8:cv2.imwrite(str(out/'frames-35-42.jpg'),np.vstack([np.hstack(tiles[:4]),np.hstack(tiles[4:])]))
    print(json.dumps({'decoded_frames':len(frames),'pairs_35_40':pairs[35:40],'output':str(out)},indent=2))


if __name__=='__main__':main()
