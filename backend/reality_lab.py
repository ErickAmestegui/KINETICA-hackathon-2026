"""Local replay protocol. No provider transport, credentials or generated observations."""
import hashlib
import json
import time
import uuid

import numpy as np
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal
from backend.mask_motion import audit_masks,fit_projection,extract_track
from backend.kinematics import Parameters,solve

SESSIONS={}


def freeze(result,video,p,object_id,confirmed,freeze_frame,horizon,corrections=(),assignments=()):
    if not confirmed:raise ValueError('Confirm the slider identity before freezing reality')
    if not 7<=freeze_frame<video['frames']-1 or not 1<=horizon<=120 or freeze_frame+horizon>=video['frames']:
        raise ValueError('Invalid fixed temporal split or horizon')
    cutoff=freeze_frame+1
    # Discard hidden geometry and hidden corrections BEFORE any axis/optimizer call.
    prior={**result,'records':[r for r in result.get('records',[]) if isinstance(r,dict) and isinstance(r.get('frame'),int) and r['frame']<cutoff]}
    past_video={**video,'frames':cutoff,'timestamps':video['timestamps'][:cutoff]}
    audit=audit_masks(prior,past_video)
    # Prior timing is deliberately reset: earlier full-study fits cannot seed this fit.
    declared=p.model_copy(update={'rpm':40.,'phase':0.})
    fit=fit_projection(audit,object_id,declared,past_video,True,[c for c in corrections if c['frame']<cutoff],[a for a in assignments if a['frame']<cutoff],estimate_timing=True,training_only=True)
    used=Parameters(**fit['parameters_used']);origin=np.array(fit['axis']['origin']);direction=np.array(fit['axis']['direction'])
    samples=fit['rows'];tail=samples[-min(8,len(samples)):]
    linear=np.polyfit([s['t'] for s in tail],[s['displacement_px'] for s in tail],1)
    rows=[]
    for frame in range(cutoff,cutoff+horizon):
        t=video['timestamps'][frame]
        value=fit['projection']['offset_px']+fit['projection']['gain_px_per_model_unit']*(solve(used,t)['B'][0]-fit['projection']['basis_at_zero'])
        point=origin+value*direction
        rows.append(dict(frame=frame,t=t,predicted_px=value,x=float(point[0]),y=float(point[1]),constant_px=samples[-1]['displacement_px'],linear_px=float(np.polyval(linear,t))))
    protocol=dict(freeze_frame=freeze_frame,horizon=horizon,training_frames=[s['frame'] for s in samples],prediction_frames=[r['frame'] for r in rows],kind='Fixed split replay; previously inspected dataset, not independent prospective validation',geometry='User-declared r/L/e; not identified from masks',segmentation_causality='Unverified: the saved SAM request processed the whole video. Local optimizer isolation does not verify causal online segmentation.')
    public=dict(protocol=protocol,parameters=used.model_dump(),axis=fit['axis'],projection=fit['projection'],predictions=rows,training_sha256=hashlib.sha256(json.dumps(prior,sort_keys=True).encode()).hexdigest(),simulated=bool(result.get('simulated') or video.get('provenance')=='synthetic'),diagnostic_id=(result.get('diagnostic') or {}).get('id'))
    for token,entry in list(SESSIONS.items()):
        if time.monotonic()-entry['created']>900:SESSIONS.pop(token,None)
    if len(SESSIONS)>=8:SESSIONS.pop(next(iter(SESSIONS)))
    token=uuid.uuid4().hex
    SESSIONS[token]=dict(created=time.monotonic(),public=public,result=result,video=video,object_id=object_id,corrections=corrections,assignments=assignments)
    return dict(token=token,**public)


def reveal(token):
    entry=SESSIONS.get(token)
    if not entry or time.monotonic()-entry['created']>900:raise ValueError('Prediction expired; freeze again locally')
    public=entry['public'];audit=audit_masks(entry['result'],entry['video'])
    samples={s['frame']:s for s in extract_track(audit,entry['object_id'],entry['corrections'],entry['assignments'])}
    origin=np.array(public['axis']['origin']);direction=np.array(public['axis']['direction']);rows=[]
    for prediction in public['predictions']:
        sample=samples.get(prediction['frame'])
        if sample is None:continue
        observed=float((np.array([sample['x'],sample['y']])-origin)@direction)
        rows.append({**prediction,'observed_px':observed,'observed_x':sample['x'],'observed_y':sample['y'],'source':sample['source']})
    crossing=public['diagnostic_id']=='e14d21bb8f3c' and any(r['frame']>=38 for r in public['predictions'])
    complete=len(rows)==len(public['predictions'])
    valid=not crossing and complete and len(rows)>=3
    metrics={name:float(np.sqrt(np.mean([(r[key]-r['observed_px'])**2 for r in rows]))) if valid else None for name,key in [('model_rmse_px','predicted_px'),('constant_rmse_px','constant_px'),('linear_rmse_px','linear_px')]}
    return dict(**public,rows=rows,metrics=metrics,n=len(rows),evaluation_valid=valid,reason='Known source framing/temporal discontinuity at 37–38; a continuous single-camera model is not comparable across it' if crossing else 'Missing observations or fewer than three evaluation frames' if not valid else 'Replay agreement in pixels; not independent ground truth',reconstruction_verified=False)


class ChangeArgs(BaseModel):
    model_config=ConfigDict(extra='forbid',allow_inf_nan=False,strict=True)
    parameter:Literal['r','L','rpm','phase','stroke']
    value:float=Field(ge=-10000,le=50000)


class ToolCall(BaseModel):
    model_config=ConfigDict(extra='forbid')
    name:Literal['get_mechanism_state','calculate_slider_motion','validate_geometry','propose_parameter_change','compare_scenarios','explain_measurement_errors']
    arguments:ChangeArgs|None


def muse_request(messages):
    """Build-only adapter for a future authorized call. This function cannot send I/O."""
    return dict(model='muse-spark-1.3',messages=messages,response_format={'type':'json_schema','json_schema':{'name':'kinetica_tool','schema':ToolCall.model_json_schema(),'strict':True}})


def parse_muse_response(response):
    """Validate one proposed tool; never execute model output or log its body."""
    try:
        choice=response['choices'][0]
        if choice.get('finish_reason')!='stop':raise ValueError()
        content=choice['message']['content']
        if not isinstance(content,str) or len(content)>10000:raise ValueError()
        return ToolCall.model_validate_json(content)
    except (KeyError,IndexError,TypeError,ValueError):
        raise ValueError('Invalid, refused or incomplete Muse tool proposal') from None


def mock_intent(text,p):
    lower=text.lower()
    change=None
    if any(s in lower for s in ('duplic','double')) and any(s in lower for s in ('velocidad','speed','angular','rpm')):change=ChangeArgs(parameter='rpm',value=2*p.rpm)
    elif any(s in lower for s in ('duplic','double')):change=ChangeArgs(parameter='stroke',value=4*p.r)
    elif any(s in lower for s in ('rápido','rapido','faster')):change=ChangeArgs(parameter='rpm',value=p.rpm*1.5)
    name='propose_parameter_change' if change else 'validate_geometry' if any(s in lower for s in ('funciona','invalid','why','por qué')) else 'compare_scenarios' if any(s in lower for s in ('diferencia','difference')) else 'get_mechanism_state'
    return ToolCall(name=name,arguments=change)


def execute_tool(call,p,alternate=None):
    if call.name=='propose_parameter_change':
        if call.arguments is None:raise ValueError('Change arguments required')
        change=call.arguments;values=p.model_dump()
        values['r' if change.parameter=='stroke' else change.parameter]=change.value/2 if change.parameter=='stroke' else change.value
        try:candidate=Parameters(**values)
        except ValueError:return dict(valid=False,proposed=values,reason='Full rotation requires L > r + |e|, positive lengths and bounded finite speed. Stroke=2r only for e=0.')
        if change.parameter=='stroke' and p.e!=0:return dict(valid=False,reason='Requested stroke inversion currently requires centered geometry e=0')
        return dict(valid=True,proposed=candidate.model_dump(),requires_confirmation=True)
    if call.arguments is not None:raise ValueError('Read-only tools take null arguments')
    if call.name=='explain_measurement_errors':return dict(explanation='Mask centroid drift, perspective, camera cuts and timing changes affect pixel residuals; segmentation is not a joint measurement.')
    if call.name=='validate_geometry':return dict(valid=True,constraint='L > r + |e|',margin=p.L-p.r-abs(p.e))
    if call.name=='calculate_slider_motion':return dict(samples=[solve(p,i/60) for i in range(61)])
    if call.name=='compare_scenarios':return dict(original=p.model_dump(),alternate=(alternate or p).model_dump(),original_x=solve(p,0)['B'][0],alternate_x=solve(alternate or p,0)['B'][0])
    return dict(parameters=p.model_dump(),state=solve(p,0),physical_buildability='Not evaluated; no forces/material properties measured')
