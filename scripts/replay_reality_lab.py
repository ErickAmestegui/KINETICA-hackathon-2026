"""Replay saved real evidence locally. Does not import any Meta transport."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.reality_lab import freeze,reveal
from backend.kinematics import Parameters

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project',type=Path,required=True)
    parser.add_argument('--object-id',required=True)
    parser.add_argument('--confirm-slider',action='store_true')
    parser.add_argument('--freeze-frame',type=int,default=29)
    parser.add_argument('--horizon',type=int,default=20)
    args=parser.parse_args();raw=args.project.read_bytes();project=json.loads(raw)
    result=project['samResult'];video=project['video'];identity=video['id']
    if len(identity)!=32 or any(c not in '0123456789abcdef' for c in identity):raise ValueError('Invalid source ID')
    folder=ROOT/'data'/identity;metadata=json.loads((folder/'metadata.json').read_text('utf-8'))
    if result.get('simulated'):raise ValueError('This private real-evidence reproduction rejects synthetic exports')
    state=project.get('maskMotionState') or {}
    prediction=freeze(result,metadata,Parameters(**project['parameters']),args.object_id,args.confirm_slider,args.freeze_frame,args.horizon,state.get('corrections',[]),state.get('assignments',[]))
    report=reveal(prediction['token'])
    report['source_video_sha256']=hashlib.sha256((folder/('source'+metadata['extension'])).read_bytes()).hexdigest()
    report['source_export_sha256']=hashlib.sha256(raw).hexdigest()
    report['inference_performed']=False
    encoded=json.dumps(report,indent=2,allow_nan=False)
    out=ROOT/'output'/'reality-lab';out.mkdir(exist_ok=True)
    path=out/('replay-'+hashlib.sha256(encoded.encode()).hexdigest()[:16]+'.json')
    if not path.exists():path.write_text(encoded,'utf-8')
    print(json.dumps({'report':str(path),'n':report['n'],'metrics':report['metrics'],'reason':report['reason'],'inference_performed':False},indent=2))

if __name__=='__main__':main()
