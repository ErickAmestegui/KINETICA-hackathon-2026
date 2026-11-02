"""Separate future manual annotations from a hash-sealed forecast. No fitting here."""
import hashlib
import json
import math

def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def seal(protocol,forecast):
    if protocol.get('status')!='preregistered_local' or len(protocol.get('video_sha256',''))!=64:raise ValueError('Need a locally preregistered protocol and source hash')
    if any(key in forecast for key in ('rows','metrics','observed_px')):raise ValueError('Revealed evidence cannot be sealed as a blind forecast')
    split=forecast['protocol']
    if split['freeze_frame']!=protocol['freeze_frame'] or split['horizon']!=protocol['horizon']:raise ValueError('Split differs from preregistration')
    if any(f>protocol['freeze_frame'] for f in split['training_frames']):raise ValueError('Future training leakage')
    expected=list(range(protocol['freeze_frame']+1,protocol['freeze_frame']+1+protocol['horizon']))
    if [r['frame'] for r in forecast['predictions']]!=expected:raise ValueError('Prediction grid differs from preregistration')
    value={'protocol':protocol,'forecast':{k:v for k,v in forecast.items() if k!='token'}}
    return {**value,'seal_sha256':digest(value),'independence_verified':False,'status':'sealed_before_manual_evaluation_claimed_by_operator'}

def evaluate(sealed,annotations):
    value={k:sealed[k] for k in ('protocol','forecast')}
    if digest(value)!=sealed['seal_sha256']:raise ValueError('Sealed forecast or protocol changed')
    protocol=sealed['protocol'];forecast=sealed['forecast']
    if annotations.get('video_sha256')!=protocol['video_sha256'] or annotations.get('source')!='manual_future_blinded':raise ValueError('Need separate future manual annotations from the same source')
    points=annotations['points']
    if len({p['frame'] for p in points})!=len(points):raise ValueError('Duplicate annotation frame')
    observed={p['frame']:p for p in points};rows=[]
    if set(observed)!={p['frame'] for p in forecast['predictions']}:raise ValueError('Incomplete or overlapping evaluation frame set')
    origin=forecast['axis']['origin'];direction=forecast['axis']['direction']
    for r in forecast['predictions']:
        p=observed[r['frame']]
        if not all(isinstance(p[k],(int,float)) and not isinstance(p[k],bool) and math.isfinite(p[k]) for k in ('x','y','t')):raise ValueError('Nonfinite annotation')
        if abs(p['t']-r['t'])>1e-6:raise ValueError('Annotation timestamps differ')
        v=(p['x']-origin[0])*direction[0]+(p['y']-origin[1])*direction[1]
        rows.append({**r,'observed_px':v,'source':'manual_future_blinded'})
    n=len(rows)
    if n<3:raise ValueError('Need at least three complete future annotations')
    metrics={name:(sum((r[key]-r['observed_px'])**2 for r in rows)/n)**.5 for name,key in [('model_rmse_px','predicted_px'),('constant_rmse_px','constant_px'),('linear_rmse_px','linear_px')]}
    return {'n':n,'metrics':metrics,'rows':rows,'protocol_sha256':digest(protocol),'seal_sha256':sealed['seal_sha256'],'annotation_sha256':digest(annotations),'independence_verified':False,'limitations':['Local hashes establish integrity, not prior external registration or annotator blinding.','Continuous fixed-camera source, independent labels and past-only segmentation require separate evidence.','Existing Eitech full-video SAM masks cannot establish causal segmentation.']}
