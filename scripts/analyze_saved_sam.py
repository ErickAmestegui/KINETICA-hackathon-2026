"""Reproduce a preserved SAM study entirely offline; no Meta imports or transport."""
import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.mask_motion import audit_masks, extract_track, fit_projection
from backend.kinematics import Parameters


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project',type=Path,required=True)
    p.add_argument('--expected-diagnostic',default='e14d21bb8f3c')
    p.add_argument('--expected-records',type=int,default=300)
    p.add_argument('--object-id')
    p.add_argument('--confirm-slider',action='store_true')
    p.add_argument('--write-demo',action='store_true',help='Save a private replay project using the unchanged original geometry')
    p.add_argument('--start-frame',type=int,default=0)
    p.add_argument('--end-frame',type=int)
    p.add_argument('--estimate-timing',action='store_true',help='Conditional video-time speed/phase fit; geometry is fixed')
    p.add_argument('--output',type=Path,default=ROOT/'output'/'sam-motion')
    args=p.parse_args()
    original=args.project.read_bytes()
    if len(original)>50_000_000:raise ValueError('Export exceeds the local 50 MB limit')
    project=json.loads(original)
    result=project.get('samResult') or project.get('result')
    if not isinstance(result,dict):raise ValueError('Export lacks samResult/result; do not repeat inference')
    video=project.get('video')
    if not isinstance(video,dict):raise ValueError('Export lacks source video metadata')
    identity=video.get('id','')
    if len(identity)!=32 or any(c not in '0123456789abcdef' for c in identity):raise ValueError('Invalid local video ID')
    folder=ROOT/'data'/identity
    metadata=json.loads((folder/'metadata.json').read_text('utf-8'))
    if any(video.get(k)!=metadata[k] for k in ('frames','width','height')):raise ValueError('Export and local footage metadata differ')
    if args.expected_records is not None and len(result.get('records',[]))!=args.expected_records:raise ValueError('Record count differs from expected original inference')
    if result.get('simulated'):raise ValueError('SIMULATED TEST cannot be used as original real SAM evidence')
    if result.get('outcome',{}).get('status')!='completed':raise ValueError('Original response did not complete')
    audit=audit_masks(result,metadata,args.expected_diagnostic)
    source=folder/('source'+metadata['extension'])
    evidence=audit['evidence']
    evidence.update(video_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),export_sha256=hashlib.sha256(original).hexdigest(),export_path=str(args.project.resolve()),video_id=identity)
    report={'audit':audit,'motion':None,'inference_performed':False,'manual_selection':{'object_id':args.object_id,'confirmed_slider':args.confirm_slider}}
    if args.object_id:
        state=project.get('maskMotionState') or {}
        report['motion']=fit_projection(audit,args.object_id,Parameters(**project['parameters']),metadata,args.confirm_slider,state.get('corrections',[]),state.get('assignments',[]),state.get('axisAngle'),args.start_frame,args.end_frame,args.estimate_timing)
    args.output.mkdir(parents=True,exist_ok=True)
    # Source hash + complete analysis hash: different decisions never replace a run.
    run_digest=hashlib.sha256(json.dumps(report,sort_keys=True,allow_nan=False).encode()).hexdigest()[:16]
    run=args.output/evidence['export_sha256'][:16]/run_digest
    run.mkdir(parents=True,exist_ok=True)
    (run/'audit.json').write_text(json.dumps(report,indent=2,allow_nan=False),encoding='utf-8')
    for obj in audit['objects']:
        # Object IDs are data, never filesystem paths.
        name=hashlib.sha256(obj['object_id'].encode()).hexdigest()[:12]
        with (run/('object-'+name+'.csv')).open('w',newline='',encoding='utf-8') as out:
            writer=csv.DictWriter(out,fieldnames=['object_id','frame','t','x','y','area_px2','source'])
            writer.writeheader();writer.writerows(obj['samples'])
    if report['motion']:
        with (run/'selected-motion.csv').open('w',newline='',encoding='utf-8') as out:
            writer=csv.DictWriter(out,fieldnames=list(report['motion']['rows'][0]))
            writer.writeheader();writer.writerows(report['motion']['rows'])
    if args.write_demo:
        if not args.object_id or not args.confirm_slider:raise ValueError('Replay needs an explicitly selected and manually confirmed slider')
        demo={**project,'name':'Eitech · saved SAM · offline motion measurement',
            'maskMotionState':{'objectId':args.object_id,'confirmedSlider':True,'corrections':state.get('corrections',[]),'assignments':state.get('assignments',[]),'axisAngle':state.get('axisAngle'),'jitterPx':2,'startFrame':args.start_frame,'endFrame':args.end_frame,'estimateTiming':args.estimate_timing},
            'maskAnalysis':None,'fitNote':'Geometry, speed and phase are declared inputs, not measurements from the masks. Re-audit and fit image projection locally.'}
        (run/'replay-project.json').write_text(json.dumps(demo,ensure_ascii=False,allow_nan=False),encoding='utf-8')
    print(json.dumps({'verified_export':True,'counts':audit['counts'],'diagnostic_id':evidence['diagnostic_id'],'objects':[{k:o[k] for k in ('object_id','valid_masks','motion','span_px')} for o in audit['objects']],'report':str(run/'audit.json'),'motion_evaluated':report['motion'] is not None,'inference_performed':False},indent=2))


if __name__=='__main__':main()
