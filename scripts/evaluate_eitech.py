"""Local real-video audit with explicitly MANUAL, approximate annotations.

No Meta call. No media redistribution. Run with --video pointing at your copy.
Coordinates were read from crops of the actual frames (not SAM predictions).
Blur, perspective and camera motion make these diagnostic annotations, not metrology ground truth.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import httpx
import numpy as np
from backend.kinematics import Parameters,Calibration,Observation,fit_parameters,compare
from backend.vision import inspect_video,track_points

# frame, crank x/y, slider pin x/y, source image coordinates at 1920x1080.
ANNOTATIONS=[
 (150,286,382,916,847),(152,306,380,948,862),(154,317,330,951,859),
 (156,309,278,900,823),(158,250,240,865,799),(160,220,226,818,798),
 (162,188,260,778,803),(164,198,322,796,809),(166,234,368,838,832),
 (168,278,411,880,846),(170,294,405,932,868),(172,320,374,946,880),
]


def main():
    args=argparse.ArgumentParser();args.add_argument('--video',required=True);args.add_argument('--url',default='http://127.0.0.1:8000');ns=args.parse_args()
    path=Path(ns.video);info=inspect_video(path)
    if info['width']!=1920 or info['height']!=1080 or info['frames']!=442:
        raise ValueError('This manual annotation set applies only to the reviewed 1920x1080, 442-frame copy')
    observations=[]
    for frame,ax,ay,bx,by in ANNOTATIONS:
        for joint,x,y in [('crank',ax,ay),('slider',bx,by)]:
            observations.append(Observation(frame=frame,t=info['timestamps'][frame],x=x,y=y,joint=joint,source='manual',split='fit' if frame<=166 else 'validation'))
    # Deliberately approximate image calibration, selected using the training portion.
    calibration=Calibration(ox=265,oy=306,angle=.35,scale=6,unit='relative')
    initial=Parameters(r=14,L=145,rpm=75,e=-60,phase=2.19)
    fit=fit_parameters(initial,observations,calibration)
    p=Parameters(**fit['parameters'])
    baseline=track_points(path,[{'x':288,'y':388,'joint':'crank'},{'x':905,'y':891,'joint':'slider'}],150,180,info['timestamps'])
    constant=[]
    for joint in ['crank','slider']:
        train=np.array([[o.x,o.y] for o in observations if o.joint==joint and o.split=='fit'])
        mean=train.mean(axis=0)
        constant.extend(float(np.linalg.norm(np.array([o.x,o.y])-mean)) for o in observations if o.joint==joint and o.split=='validation')
    source_hash=hashlib.sha256(path.read_bytes()).hexdigest()
    evidence={'source_sha256':source_hash,'source_name':path.name,'source_kind':'real video; manual approximate center annotations',
              'sample_frames':[a[0] for a in ANNOTATIONS],'fit':fit,'calibration':calibration.model_dump(),
              'lk_baseline':{'samples':len(baseline['observations']),'lost':baseline['lost'],'held_out_coverage':0,'held_out_rmse_px':None},
              'constant_training_mean_baseline_validation_rmse_px':float(np.sqrt(np.mean(np.array(constant)**2))),
              'limitations':['Manual centers approximate because of motion blur; not independently verified ground truth',
              'Strong perspective and handheld camera motion; fixed similarity calibration is inadequate',
              'Eccentricity and calibration were chosen manually, not recovered by AI',
              'Only 0.88 seconds sampled from 17.68 seconds; no full-video accuracy claim',
              'No SAM or Muse inference performed','Residuals are diagnostic image-plane discrepancies, not proof of accurate reconstruction']}
    output=Path('output/real-video');output.mkdir(parents=True,exist_ok=True)
    (output/'eitech-evaluation.json').write_text(json.dumps(evidence,indent=2),'utf-8')
    with httpx.Client(timeout=120) as client:
        with path.open('rb') as f: response=client.post(ns.url+'/api/videos',files={'file':(path.name,f,'video/mp4')})
        response.raise_for_status();video={**response.json(),'provenance':'real'}
    project={'schema':'kinetica/1','name':'Eitech · manual diagnostic study','parameters':p.model_dump(),'calibration':calibration.model_dump(),
             'observations':[o.model_dump() for o in observations],'video':video,'regions':[],'sam':[],'proposal':None,'aiEvidence':[],
             'fitNote':'Diagnostic fit of 18 manually annotated training samples; 6 held-out manual samples. Perspective/camera motion uncorrected. See output/real-video/eitech-evaluation.json.',
             'lost':baseline['lost'],'trainedFrames':fit['fit_frames']}
    (output/'eitech-project.json').write_text(json.dumps(project,indent=2),'utf-8')
    print(json.dumps({'manual_samples':len(observations),'fit_rmse_px':fit['comparison']['fit']['rmse_px'],
                     'held_out_rmse_px':fit['comparison']['validation']['rmse_px'],
                     'constant_baseline_rmse_px':evidence['constant_training_mean_baseline_validation_rmse_px'],
                     'LK_samples':len(baseline['observations']),'LK_lost':baseline['lost'],
                     'parameters':p.model_dump(),'meta_inference':False},indent=2))

if __name__=='__main__': main()
