"""Build an explicitly SYNTHETIC saved-mask UI fixture from existing test footage."""
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.kinematics import Parameters,solve,project,Calibration

settings=json.loads((ROOT/'output/synthetic-fixture.json').read_text('utf-8'))
metadata=None
for path in sorted((ROOT/'data').glob('*/metadata.json')):
    candidate=json.loads(path.read_text('utf-8'))
    if candidate['name']=='synthetic-slider-crank.mp4':metadata=candidate;break
if metadata is None:raise ValueError('Import the existing synthetic test video locally first')
p=Parameters(**settings['parameters']);cal=Calibration(**settings['calibration']);records=[]
for frame,t in enumerate(metadata['timestamps']):
    point=project(solve(p,t)['B'],cal)
    for identity,x,y in [('SYNTHETIC-FIXED',100,180),('SYNTHETIC-SLIDER',float(point[0]),float(point[1]))]:
        bounds={'left':x-8,'top':y-8,'right':x+8,'bottom':y+8}
        records.extend([dict(kind='box',object_id=identity,frame=frame,**bounds),
            dict(kind='mask',object_id=identity,frame=frame,bounds=bounds,width=16,height=16,path='M0 0L16 0L16 16L0 16Z')])
result={'records':records,'outcome':{'status':'completed'},'diagnostic':{'id':'SYNTHETIC-ONLY'},'simulated':True,'diagnostics':[],'remote_file_cleanup':'not_needed'}
payload={'schema':'kinetica/1','name':'SYNTHETIC TEST — saved-mask motion','parameters':p.model_dump(),'calibration':cal.model_dump(),'observations':[],
    'video':{**metadata,'provenance':'synthetic'},'sam':records,'samResult':result,'regions':[],'aiEvidence':[]}
out=ROOT/'output/SYNTHETIC-mask-motion-project.json'
out.write_text(json.dumps(payload),'utf-8')
print('SYNTHETIC TEST ONLY:',out,'records:',len(records),'No inference performed.')
