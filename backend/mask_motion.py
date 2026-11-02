"""Offline image-space measurements from saved SAM contours, never joint inference.

SVG contours are the geometry retained by the original adapter. Centroids/areas
refer to those contours, not to inaccessible original RLE pixels. No interpolation.
"""
import hashlib
import json
import math
import re
from collections import Counter, defaultdict

import numpy as np
from scipy.optimize import least_squares
from backend.kinematics import solve

NUMBER = r'[-+]?(?:\d*\.\d+|\d+\.?\d*)(?:[eE][-+]?\d+)?'
TOKENS = re.compile(r'[MLZmlz]|' + NUMBER)
LIMITATIONS = [
    'Mask contour centroid is a visible-area measurement, not a mechanical joint.',
    'Image motion includes camera movement, perspective, occlusion and segmentation drift.',
    'Shared object IDs are associations supplied by SAM; continuity is audited, not guaranteed.',
    'No physical scale, hidden geometry or 3D reconstruction is inferred.',
    'Only image gain and offset are fitted; geometry, eccentricity, speed and phase remain declared inputs.',
    'Held-out frames are reserved from axis estimation and projection fitting; they are not independent human ground truth.',
]


def finite(value):
    return isinstance(value, (int,float)) and not isinstance(value,bool) and math.isfinite(value)


def contour_centroid(row):
    path=row.get('path','')
    width,height=row.get('width'),row.get('height')
    bounds=row.get('bounds',{})
    if not isinstance(path,str) or not path or len(path)>2_000_000:
        raise ValueError('missing or oversized mask contour')
    if not all(finite(v) and v>0 for v in (width,height)):
        raise ValueError('invalid mask dimensions')
    if not all(finite(bounds.get(k)) for k in ('left','top','right','bottom')):
        raise ValueError('invalid mask bounds')
    left,top,right,bottom=(bounds[k] for k in ('left','top','right','bottom'))
    if right<=left or bottom<=top:raise ValueError('empty mask bounds')
    if re.sub(TOKENS,'',path).replace(',','').strip():
        raise ValueError('unsupported mask path; expected official M/L/Z contours')
    tokens=TOKENS.findall(path)
    if len(tokens)>300_000:raise ValueError('too many contour coordinates')
    rings=[];ring=[];i=0;command=None;x=y=0.
    while i<len(tokens):
        token=tokens[i]
        if token in 'MLZmlz':
            command=token;i+=1
            if command in 'Mm' and ring:raise ValueError('previous contour must be closed before moveto')
            if command in 'Ll' and not ring:raise ValueError('contour must start with moveto')
            if command in 'Zz':
                if len(ring)<3:raise ValueError('invalid closed contour')
                rings.append(ring);x,y=ring[0];ring=[];command=None
                continue
        if command not in ('M','m','L','l') or i+1>=len(tokens):raise ValueError('invalid contour command')
        try:u,v=float(tokens[i]),float(tokens[i+1])
        except ValueError:raise ValueError('invalid contour coordinates') from None
        if not all(math.isfinite(q) for q in (u,v)):raise ValueError('nonfinite contour')
        if command.islower():u+=x;v+=y
        x,y=u,v
        if not (-1<=x<=width+1 and -1<=y<=height+1):raise ValueError('contour outside mask dimensions')
        ring.append((x,y));i+=2
        if command in 'Mm':command='l' if command=='m' else 'L'
    if ring or not rings:raise ValueError('mask contour must be closed')
    twice_area=cx_sum=cy_sum=0.
    for points in rings:
        for a,b in zip(points,points[1:]+points[:1]):
            cross=a[0]*b[1]-b[0]*a[1]
            twice_area+=cross;cx_sum+=(a[0]+b[0])*cross;cy_sum+=(a[1]+b[1])*cross
    if abs(twice_area)<1e-9:raise ValueError('empty mask contour area')
    cx,cy=cx_sum/(3*twice_area),cy_sum/(3*twice_area)
    sx,sy=(right-left)/width,(bottom-top)/height
    return left+cx*sx,top+cy*sy,abs(twice_area/2*sx*sy)


def audit_masks(result,video,expected_diagnostic=None,jitter_px=2.):
    records=result.get('records')
    if not isinstance(records,list) or not records or len(records)>10000:
        raise ValueError('Need 1–10000 saved geometry records; no detections are invented')
    if sum(len(r.get('path','')) for r in records if isinstance(r,dict) and isinstance(r.get('path',''),str))>25_000_000:
        raise ValueError('Saved contour payload exceeds the offline limit')
    count=video['frames'];times=video['timestamps']
    if len(times)!=count or not all(finite(t) for t in times) or any(b<=a for a,b in zip(times,times[1:])):
        raise ValueError('Video timestamps must be finite, complete and strictly increasing')
    if not finite(jitter_px) or not 0<jitter_px<=100:raise ValueError('Invalid image jitter threshold')
    diagnostic=result.get('diagnostic') or {}
    if expected_diagnostic and diagnostic.get('id')!=expected_diagnostic:
        raise ValueError('Saved diagnostic does not match the expected original inference')
    groups=defaultdict(lambda:defaultdict(list));issues=[];kinds=Counter();valid_frames=set()
    for index,row in enumerate(records):
        if not isinstance(row,dict):issues.append(dict(record=index,reason='invalid record'));continue
        frame=row.get('frame');identity=row.get('object_id');kind=row.get('kind')
        if not isinstance(frame,int) or isinstance(frame,bool) or not 0<=frame<count or not isinstance(identity,str) or not identity or len(identity)>200 or kind not in ('box','mask'):
            issues.append(dict(record=index,reason='invalid frame, object ID or geometry kind'));continue
        kinds[kind]+=1;valid_frames.add(frame);groups[identity][frame].append(row)
    objects=[]
    for identity,frames in sorted(groups.items()):
        samples=[];boxes=0;masks=0
        for frame,rows in sorted(frames.items()):
            bs=[r for r in rows if r['kind']=='box'];ms=[r for r in rows if r['kind']=='mask']
            boxes+=len(bs);masks+=len(ms)
            if len(bs)>1 or len(ms)>1:issues.append(dict(object_id=identity,frame=frame,reason='duplicate geometry; ambiguous sample excluded'))
            for box in bs:
                if not all(finite(box.get(k)) for k in ('left','top','right','bottom')) or not (0<=box.get('left',-1)<box.get('right',-1)<=video['width'] and 0<=box.get('top',-1)<box.get('bottom',-1)<=video['height']):
                    issues.append(dict(object_id=identity,frame=frame,reason='invalid box'))
            if len(ms)!=1 or len(bs)>1:continue
            try:
                bounds=ms[0].get('bounds',{})
                if not all(finite(bounds.get(k)) for k in ('left','top','right','bottom')) or not (0<=bounds['left']<bounds['right']<=video['width'] and 0<=bounds['top']<bounds['bottom']<=video['height']):
                    raise ValueError('mask bounds outside source image')
                x,y,area=contour_centroid(ms[0])
                if not (0<=x<=video['width'] and 0<=y<=video['height']):raise ValueError('centroid outside source image')
                samples.append(dict(frame=frame,t=times[frame],x=x,y=y,area_px2=area,source='sam-contour',object_id=identity))
            except ValueError as exc:issues.append(dict(object_id=identity,frame=frame,reason=str(exc)))
        xy=np.array([[s['x'],s['y']] for s in samples])
        span=float(np.linalg.norm(np.ptp(xy,axis=0))) if len(xy) else None
        robust_span=float(np.linalg.norm(np.percentile(xy,95,axis=0)-np.percentile(xy,5,axis=0))) if len(xy)>=8 else None
        motion='insufficient_evidence' if robust_span is None else 'moving_in_image' if robust_span>2*jitter_px else 'stationary_in_image'
        observed={s['frame'] for s in samples}
        jumps=[b['frame'] for a,b in zip(samples,samples[1:]) if b['frame']==a['frame']+1 and math.hypot(b['x']-a['x'],b['y']-a['y'])>max(20,4*math.sqrt(a['area_px2']))]
        # A local bend in a centroid trajectory can indicate a cut, camera motion,
        # segmentation drift OR genuine acceleration. It is a review flag, not a loss
        # label. Interpolation respects VFR timestamps; no samples are changed.
        deviations=[]
        for a,b,c in zip(samples,samples[1:],samples[2:]):
            if (b['frame']!=a['frame']+1 or c['frame']!=b['frame']+1):continue
            fraction=(b['t']-a['t'])/(c['t']-a['t'])
            value=math.hypot(b['x']-(a['x']+fraction*(c['x']-a['x'])),b['y']-(a['y']+fraction*(c['y']-a['y'])))
            deviations.append(dict(frame=b['frame'],deviation_px=value,last_frame=c['frame']))
        training_deviations=[d['deviation_px'] for d in deviations if d['last_frame']<math.ceil(count*.75)]
        threshold=None;alerts=[]
        if len(training_deviations)>=6:
            median=float(np.median(training_deviations))
            mad=float(np.median(np.abs(np.array(training_deviations)-median)))
            threshold=max(5.,median+6*1.4826*mad)
            alerts=[dict(frame=d['frame'],deviation_px=d['deviation_px']) for d in deviations if d['deviation_px']>threshold]
        training=[s for s in samples if s['frame']<math.ceil(count*.75)]
        axis=None
        if len(training)>=3:
            positions=np.array([[s['x'],s['y']] for s in training])
            _,singular,vectors=np.linalg.svd(positions-positions.mean(axis=0),full_matrices=False)
            if singular[0]>1e-6:
                vector=vectors[0]
                if vector[0]<0 or (abs(vector[0])<1e-10 and vector[1]<0):vector=-vector
                axis=dict(direction=vector.tolist(),origin=positions[0].tolist(),linearity=float(singular[0]**2/np.sum(singular**2)))
        objects.append(dict(object_id=identity,boxes=boxes,masks=masks,valid_masks=len(samples),samples=samples,axis=axis,
            first_frame=min(frames),last_frame=max(frames),missing_mask_frames=sorted(set(range(count))-observed),
            missing_box_frames=sorted(set(range(count))-{f for f,rs in frames.items() if any(r['kind']=='box' for r in rs)}),
            motion=motion,span_px=span,robust_span_px=robust_span,possible_id_jumps=jumps,
            temporal_alerts=alerts,temporal_threshold_px=threshold,
            temporal_alert_method='Time-weighted centroid deviation from adjacent frames; threshold max(5 px, training median + 6 scaled MAD). Review only; no automatic exclusion or causal claim.',
            continuity='ID continuity is unverified; inspect occlusions, jumps and areas'))
    digest=hashlib.sha256(json.dumps(records,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    return dict(schema='kinetica-mask-audit/1',counts=dict(records=len(records),objects=len(objects),boxes=kinds['box'],masks=kinds['mask'],frames_with_geometry=len(valid_frames),source_frames=count),
        objects=objects,issues=issues,missing_geometry_frames=sorted(set(range(count))-valid_frames),
        evidence=dict(kind='synthetic_test' if result.get('simulated') or video.get('provenance')=='synthetic' else 'operator_imported_response',
            diagnostic_id=diagnostic.get('id'),outcome=result.get('outcome'),parser_diagnostics=len(result.get('diagnostics') or []),
            records_sha256=digest,remote_file_cleanup=result.get('remote_file_cleanup'),
            note='Local integrity hash; not cryptographic proof of provider origin'),
        jitter_px=jitter_px,centroid_method='Signed polygon area centroid of retained SVG contours; holes subtract by winding',limitations=LIMITATIONS)


def extract_track(audit,object_id,corrections=(),assignments=()):
    objects={o['object_id']:{s['frame']:s for s in o['samples']} for o in audit['objects']}
    if object_id not in objects:raise ValueError('Selected object is absent')
    by_frame={f:dict(s) for f,s in objects[object_id].items()}
    for changes,label in ((assignments,'assignment'),(corrections,'correction')):
        if len({c['frame'] for c in changes})!=len(changes):raise ValueError('duplicate '+label+' frame')
    for assignment in assignments:
        frame=assignment['frame'];other=objects.get(assignment['object_id'],{}).get(frame)
        if other is None:raise ValueError('Reassigned object has no valid mask in that frame')
        by_frame[frame]={**other,'source':'manual-ID-assignment'}
    for correction in corrections:
        frame=correction['frame']
        if correction.get('excluded'):
            by_frame.pop(frame,None);continue
        if frame not in by_frame:raise ValueError('Correction requires a measured frame; missing masks are not interpolated')
        if not finite(correction.get('x')) or not finite(correction.get('y')):raise ValueError('Correction needs finite image coordinates')
        by_frame[frame]={**by_frame[frame],'x':correction['x'],'y':correction['y'],'source':'manual-centroid'}
    return [by_frame[f] for f in sorted(by_frame)]


def fit_projection(audit,object_id,parameters,video,confirmed_slider=False,corrections=(),assignments=(),axis_angle=None,start_frame=0,end_frame=None,estimate_timing=False,training_only=False):
    if not confirmed_slider:raise ValueError('Manually confirm that the selected object is the slider before fitting')
    track=extract_track(audit,object_id,corrections,assignments)
    end_frame=video['frames']-1 if end_frame is None else end_frame
    if any(not isinstance(f,int) or isinstance(f,bool) for f in (start_frame,end_frame)) or not 0<=start_frame<=end_frame<video['frames']:
        raise ValueError('Invalid analysis frame interval')
    track=[s for s in track if start_frame<=s['frame']<=end_frame]
    split_frame=end_frame+1 if training_only else start_frame+math.ceil((end_frame-start_frame+1)*.75)
    train=[s for s in track if s['frame']<split_frame];held=[s for s in track if s['frame']>=split_frame]
    if len(train)<8 or (not training_only and len(held)<3):raise ValueError('Need at least 8 training and 3 reserved mask frames')
    xy=np.array([[s['x'],s['y']] for s in train]);center=xy.mean(axis=0)
    _,values,axes=np.linalg.svd(xy-center,full_matrices=False)
    if not len(values) or values[0]<1e-6:raise ValueError('Movement axis is not identifiable for a stationary object')
    direction=axes[0]
    if direction[0]<0 or (abs(direction[0])<1e-10 and direction[1]<0):direction=-direction
    if axis_angle is not None:
        if not finite(axis_angle):raise ValueError('Invalid manual axis angle')
        direction=np.array([math.cos(axis_angle),math.sin(axis_angle)])
    reference=xy[0];declared_parameters=parameters.model_dump()
    if estimate_timing:
        # Estimate timing in VIDEO seconds, conditional on the declared geometry.
        # No physical clock is inferred for edited or slow-motion source footage.
        times=np.array([s['t'] for s in train]);target=(xy-reference)@direction
        if np.std(target)<1.:raise ValueError('Insufficient motion to identify timing above pixel noise')
        def positions(frequency,phase):
            theta=2*np.pi*frequency*times+phase
            return parameters.r*np.cos(theta)+np.sqrt(parameters.L**2-(parameters.e-parameters.r*np.sin(theta))**2)
        def residual(z):return z[2]*positions(z[0],z[1])+z[3]-target
        best=None;initializations=[]
        for frequency in np.linspace(.2,3.,15):
            for phase in np.linspace(-np.pi,np.pi,8,endpoint=False):
                basis=positions(frequency,phase)
                initial_gain=max(.001,float(np.std(target)/max(np.std(basis),.001)))
                initial=[frequency,phase,initial_gain,float(target.mean()-initial_gain*basis.mean())]
                initializations.append(initial)
        # Interactive freeze ranks the same deterministic coarse grid first,
        # avoiding 120 expensive refinements on a CPU shared with WebGL/browser QA.
        # Existing Phase 2 fits retain their exhaustive multistart behavior.
        if training_only:initializations=sorted(initializations,key=lambda z:float(np.sum(residual(z)**2)))[:12]
        for initial in initializations:
            candidate=least_squares(residual,initial,bounds=([.1,-4*np.pi,0,-np.inf],[3.,4*np.pi,np.inf,np.inf]),max_nfev=180)
            if candidate.success and (best is None or np.sum(candidate.fun**2)<np.sum(best.fun**2)):best=candidate
        if best is None or (times[-1]-times[0])*best.x[0]<1.25 or best.x[0]<.1001 or best.x[0]>2.9999:
            raise ValueError('Timing not identifiable within 6–180 rpm and at least 1.25 observed training cycles')
        singular=np.linalg.svd(best.jac,compute_uv=False)
        if singular[-1]<=0 or singular[0]/singular[-1]>1e6:raise ValueError('Timing fit is ill-conditioned')
        parameters=parameters.model_copy(update={'rpm':float(best.x[0]*60),'phase':float((best.x[1]+np.pi)%(2*np.pi)-np.pi)})
    basis0=solve(parameters,0)['B'][0]
    basis=np.array([solve(parameters,s['t'])['B'][0]-basis0 for s in train])
    y=(xy-reference)@direction;design=np.column_stack([basis,np.ones(len(basis))])
    if np.linalg.matrix_rank(design)<2 or np.std(basis)<1e-6:raise ValueError('Image gain and offset are not identifiable for this declared model')
    condition=float(np.linalg.cond(design))
    if condition>1e6:raise ValueError('Image projection is too ill-conditioned to identify reliably')
    gain,offset=np.linalg.lstsq(design,y,rcond=None)[0]
    train_mean=float(y.mean());rows=[]
    for s in track:
        projected=float((np.array([s['x'],s['y']])-reference)@direction)
        predicted=float(offset+gain*(solve(parameters,s['t'])['B'][0]-basis0))
        cross=float((np.array([s['x'],s['y']])-reference)@np.array([-direction[1],direction[0]]))
        rows.append({**s,'split':'fit' if s['frame']<split_frame else 'validation','displacement_px':projected,'predicted_px':predicted,'residual_px':projected-predicted,'cross_axis_px':cross})
    def metric(split):
        subset=[r for r in rows if r['split']==split]
        if not subset:return dict(n=0,rmse_px=None,baseline_rmse_px=None,cross_axis_rms_px=None)
        return dict(n=len(subset),rmse_px=float(np.sqrt(np.mean([r['residual_px']**2 for r in subset]))),
            baseline_rmse_px=float(np.sqrt(np.mean([(r['displacement_px']-train_mean)**2 for r in subset]))),
            cross_axis_rms_px=float(np.sqrt(np.mean([r['cross_axis_px']**2 for r in subset]))))
    limits=list(LIMITATIONS)
    if estimate_timing:
        limits[4]='Geometry and eccentricity held fixed. Speed/phase estimated only in video time, conditional on this geometry; edited footage does not identify physical shaft rpm.'
    if start_frame!=0 or end_frame!=video['frames']-1:
        limits.append('Interval selected manually after source inspection. Reserved-frame evaluation is retrospective; do not compare it as the same test as the full clip.')
    return dict(schema='kinetica-mask-motion/1',object_id=object_id,role='slider confirmed manually',rows=rows,
        axis=dict(direction=direction.tolist(),origin=reference.tolist(),estimated_from='training frames only' if axis_angle is None else 'manual angle',
            linearity=float(values[0]**2/np.sum(values**2))),
        projection=dict(gain_px_per_model_unit=float(gain),offset_px=float(offset),basis_at_zero=basis0),
        design_condition_number=condition,
        parameters_held_fixed={k:v for k,v in declared_parameters.items() if not estimate_timing or k not in ('rpm','phase')},
        declared_parameters=declared_parameters,parameters_used=parameters.model_dump(),timing_estimated=estimate_timing,
        interval=dict(start_frame=start_frame,end_frame=end_frame,selection='manual; retrospective' if start_frame!=0 or end_frame!=video['frames']-1 else 'full clip'),
        fit=metric('fit'),validation=metric('validation'),
        fit_frames=[s['frame'] for s in train],validation_frames=[s['frame'] for s in held],
        split_frame=split_frame,evidence=audit['evidence'],corrections=list(corrections),assignments=list(assignments),limitations=limits)
