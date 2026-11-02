import asyncio
import io
import csv
import json
import os
import re
import time
import uuid
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit
import cv2
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile, File, Request
from fastapi.responses import FileResponse, Response, JSONResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, Field, ConfigDict, model_validator
from starlette.concurrency import run_in_threadpool
from backend.kinematics import Parameters, Observation, Calibration, compare, fit_parameters, solve
from backend.vision import inspect_video, track_points
from backend import meta

ROOT=Path(__file__).resolve().parent.parent
load_dotenv(ROOT/'.env',override=False)
DATA=ROOT/'data'; DATA.mkdir(exist_ok=True)
app=FastAPI(title='KINETICA local API',version='0.1.0')
app.add_middleware(TrustedHostMiddleware,allowed_hosts=['127.0.0.1','localhost','testserver'])
quotes={}
inference_lock=asyncio.Lock()


@app.middleware('http')
async def local_only(request:Request,call_next):
    origin=request.headers.get('origin')
    if request.method not in ('GET','HEAD','OPTIONS') and origin and origin != str(request.base_url).rstrip('/') and origin not in ('http://127.0.0.1:5173','http://localhost:5173','http://127.0.0.1:8000','http://localhost:8000'):
        return JSONResponse({'detail':'Only the local studio can modify data'},status_code=403)
    response=await call_next(request)
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['Cache-Control']='no-store'
    return response


def video_files(identity):
    if not re.fullmatch(r'[a-f0-9]{32}',identity): raise HTTPException(404,'Video not found')
    folder=DATA/identity
    if not (folder/'metadata.json').exists(): raise HTTPException(404,'Video not found')
    info=json.loads((folder/'metadata.json').read_text('utf-8'))
    return folder/('source'+info['extension']),info


@app.get('/api/health')
def health():
    return {'status':'ok','engine':'slider-crank/open assembly','meta':meta.status()}


@app.post('/api/videos')
async def upload_video(file:UploadFile=File(...)):
    extension=Path(file.filename or '').suffix.lower()
    if extension not in ('.mp4','.mov'): raise HTTPException(415,'Only MP4 and MOV are accepted')
    identity=uuid.uuid4().hex; folder=DATA/identity; folder.mkdir()
    path=folder/('source'+extension); size=0
    try:
        with path.open('wb') as out:
            while chunk:=await file.read(1024*1024):
                size+=len(chunk)
                if size>100*1024*1024: raise HTTPException(413,'Upload exceeds 100 MB')
                out.write(chunk)
        info=await run_in_threadpool(inspect_video,path)
        info.update(id=identity,name=Path(file.filename).name,extension=extension,bytes=size)
        (folder/'metadata.json').write_text(json.dumps(info),'utf-8')
        return info
    except (ValueError,HTTPException) as exc:
        path.unlink(missing_ok=True); folder.rmdir()
        if isinstance(exc,HTTPException): raise
        raise HTTPException(422,str(exc)) from None
    finally:
        await file.close()


@app.get('/api/videos/{identity}')
def video_metadata(identity:str): return video_files(identity)[1]


@app.get('/api/videos/{identity}/media')
def media(identity:str):
    path,_=video_files(identity)
    return FileResponse(path,media_type='video/mp4' if path.suffix=='.mp4' else 'video/quicktime')


@app.get('/api/videos/{identity}/thumbnail/{frame}')
def thumbnail(identity:str,frame:int):
    path,info=video_files(identity)
    if not 0<=frame<info['frames']: raise HTTPException(422,'Frame out of range')
    cap=cv2.VideoCapture(str(path))
    try:
        cap.set(cv2.CAP_PROP_POS_FRAMES,frame); ok,image=cap.read()
        if not ok: raise HTTPException(422,'Frame decode failed')
        image=cv2.resize(image,(240,round(240*image.shape[0]/image.shape[1])))
        ok,jpg=cv2.imencode('.jpg',image)
        if not ok: raise HTTPException(422,'Thumbnail encode failed')
        return Response(jpg.tobytes(),media_type='image/jpeg')
    finally: cap.release()


class AnalysisRequest(BaseModel):
    parameters: Parameters
    calibration: Calibration
    observations: list[Observation] = Field(max_length=10000)
    trained_frames: list[int] = Field(default_factory=list,max_length=10000)

    @model_validator(mode='after')
    def disjoint(self):
        splits={}; identities=set()
        for o in self.observations:
            if o.frame in splits and splits[o.frame]!=o.split: raise ValueError('A frame cannot be used for both fitting and validation')
            splits[o.frame]=o.split
            key=(o.frame,o.joint)
            if key in identities: raise ValueError('Duplicate frame/joint observation')
            identities.add(key)
        return self


@app.post('/api/compare')
def comparison(body:AnalysisRequest): return compare(body.parameters,body.observations,body.calibration,body.trained_frames)


@app.post('/api/fit')
def fit(body:AnalysisRequest):
    try: return fit_parameters(body.parameters,body.observations,body.calibration)
    except ValueError as exc: raise HTTPException(422,str(exc)) from None


@app.post('/api/export/csv')
def export_csv(body:AnalysisRequest):
    rows=compare(body.parameters,body.observations,body.calibration)['rows']
    stream=io.StringIO(); writer=csv.DictWriter(stream,fieldnames=['frame','t','x','y','joint','source','split','predicted_x','predicted_y','error_px']);writer.writeheader();writer.writerows(rows)
    return Response(stream.getvalue(),media_type='text/csv',headers={'Content-Disposition':'attachment; filename="kinetica-observations.csv"'})


class Seed(BaseModel):
    model_config=ConfigDict(allow_inf_nan=False)
    x:float
    y:float
    joint:Literal['crank','slider']


class TrackRequest(BaseModel):
    start_frame:int=Field(ge=0)
    seeds:list[Seed]=Field(min_length=1,max_length=2)
    max_frames:int=Field(default=600,ge=1,le=600)


@app.post('/api/videos/{identity}/track')
def track(identity:str,body:TrackRequest):
    path,info=video_files(identity)
    if body.start_frame>=info['frames']: raise HTTPException(422,'Seed frame out of range')
    if len({s.joint for s in body.seeds})!=len(body.seeds): raise HTTPException(422,'Duplicate joint seed')
    try: return track_points(path,[s.model_dump() for s in body.seeds],body.start_frame,body.max_frames,info['timestamps'])
    except ValueError as exc: raise HTTPException(422,str(exc)) from None


@app.get('/api/meta/status')
def meta_status(): return meta.status()


@app.get('/api/meta/catalogue')
async def meta_catalogue(): return await meta.catalogue()


class QuoteRequest(BaseModel):
    video_id:str
    action:Literal['sam','muse']


@app.post('/api/meta/quote')
def quote(body:QuoteRequest):
    _,info=video_files(body.video_id)
    token=uuid.uuid4().hex
    # Quotes are short-lived and single-use. This endpoint never calls Meta.
    for old in list(quotes):
        if quotes[old]['expires']<time.time(): quotes.pop(old,None)
    if len(quotes)>100: raise HTTPException(429,'Too many pending estimates')
    amount=max(50,info['frames'])*.0002 if body.action=='sam' else .03
    quotes[token]={'video_id':body.video_id,'action':body.action,'expires':time.time()+300}
    return {'token':token,'video_id':body.video_id,'action':body.action,'request_count':1,
            'source':{'name':info['name'],'frames':info['frames'],'width':info['width'],'height':info['height'],'duration':info['duration']},
            'estimated_usd':round(amount,5),'kind':'frame-based estimate' if body.action=='sam' else 'planning estimate, actual image/input/reasoning tokens vary',
            'detail':f"SAM: {max(50,info['frames'])} billable frames at $0.20 / 1000. One request; full clip would be uploaded only after authorization." if body.action=='sam' else 'Muse: 3 resized frames, up to 1800 output tokens. $1.25/M input and $4.25/M output. Estimate is not a guaranteed ceiling.',
            'price_checked':'2026-10-28','expires_in_seconds':300,'status':meta.status()}


class Region(BaseModel):
    model_config=ConfigDict(allow_inf_nan=False)
    frame:int=Field(ge=0)
    id:int=Field(ge=0)
    left:float=Field(ge=0)
    top:float=Field(ge=0)
    right:float=Field(gt=0)
    bottom:float=Field(gt=0)


class InferRequest(BaseModel):
    token:str
    video_id:str
    approved:bool=False
    prompt:str=Field(default='connecting rod',max_length=120)
    regions:list[Region]=Field(default_factory=list,max_length=16)


@app.post('/api/meta/run')
async def infer(body:InferRequest):
    meta.authorize(body.approved)
    approval=quotes.pop(body.token,None)
    if not approval or approval['expires']<time.time(): raise HTTPException(403,'Estimate expired or already used; request another estimate')
    if approval['video_id']!=body.video_id: raise HTTPException(409,'Selected video differs from the estimate; prepare a new estimate')
    path,info=video_files(approval['video_id'])
    for r in body.regions:
        if not (r.left<r.right<=info['width'] and r.top<r.bottom<=info['height'] and r.frame<info['frames']): raise HTTPException(422,'Invalid segmentation region')
    if len({r.id for r in body.regions})!=len(body.regions): raise HTTPException(422,'Region IDs must be unique')
    if inference_lock.locked(): raise HTTPException(409,'One inference is already running')
    async with inference_lock:
        if approval['action']=='sam': return await meta.segment(path,info,body.prompt,body.regions,body.approved)
        return await meta.propose(path,info,body.approved)


@app.post('/api/proposal/validate')
def validate_proposal(body:meta.Proposal): return body.model_dump()


# Saved-mask analysis is local-only and never calls the Meta adapter.
class MaskMotionRequest(BaseModel):
    result: dict
    parameters: Parameters = Field(default_factory=Parameters)
    object_id: str | None = Field(default=None, max_length=200)
    confirmed_slider: bool = False
    corrections: list[dict] = Field(default_factory=list, max_length=3600)
    assignments: list[dict] = Field(default_factory=list, max_length=3600)
    expected_diagnostic: str | None = Field(default=None, max_length=64)
    jitter_px: float = Field(default=2, gt=0, le=100)
    axis_angle: float | None = None
    simulated: bool = False
    start_frame: int = Field(default=0,ge=0)
    end_frame: int | None = Field(default=None,ge=0)
    estimate_timing: bool = False


@app.post('/api/videos/{identity}/mask-motion')
def mask_motion(identity: str, body: MaskMotionRequest):
    from backend.mask_motion import audit_masks, extract_track, fit_projection
    import hashlib
    path, info = video_files(identity)
    try:
        info = {**info, 'provenance': 'synthetic' if body.simulated else 'unclassified'}
        for change in body.corrections + body.assignments:
            if not isinstance(change.get('frame'), int) or not 0 <= change['frame'] < info['frames']:
                raise ValueError('Correction/assignment frame outside source footage')
        for change in body.corrections:
            if not change.get('excluded') and not (isinstance(change.get('x'), (int, float)) and isinstance(change.get('y'), (int, float)) and 0 <= change['x'] <= info['width'] and 0 <= change['y'] <= info['height']):
                raise ValueError('Correction outside source image')
        audit = audit_masks(body.result, info, body.expected_diagnostic, body.jitter_px)
        selected = extract_track(audit, body.object_id, body.corrections, body.assignments) if body.object_id else []
        motion = fit_projection(audit, body.object_id, body.parameters, info, body.confirmed_slider,
            body.corrections, body.assignments, body.axis_angle,body.start_frame,body.end_frame,body.estimate_timing) if body.confirmed_slider and body.object_id else None
        media_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        audit['evidence']['video_sha256'] = media_hash
        audit['evidence']['video_id'] = identity
        if motion: motion['evidence'] = audit['evidence']
        return {'audit': audit, 'track': selected, 'motion': motion}
    except (ValueError, TypeError, KeyError) as exc:
        raise HTTPException(422, str(exc)) from None


@app.post('/api/videos/{identity}/preserve-segmentation')
def preserve_segmentation(identity: str, body: MaskMotionRequest):
    from backend.mask_motion import audit_masks
    import hashlib
    path, info = video_files(identity)
    info = {**info, 'provenance': 'synthetic' if body.simulated else info.get('provenance', 'unclassified')}
    try: audit = audit_masks(body.result, info, body.expected_diagnostic, body.jitter_px)
    except (ValueError, TypeError, KeyError) as exc: raise HTTPException(422, str(exc)) from None
    digest = audit['evidence']['records_sha256']
    payload = {'schema': 'kinetica-preserved-sam/1', 'video': info, 'video_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'result': body.result, 'origin': 'operator-supplied saved response; no inference performed'}
    # Include outcome and provenance: identical geometry may belong to different
    # partial/complete or synthetic responses. Never collapse these snapshots.
    snapshot_hash = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    destination = path.parent / ('sam-saved-' + snapshot_hash + '.json')
    payload['recorded_at'] = time.time()
    # Content-addressed, append-only snapshots; original input files are never overwritten.
    if not destination.exists():
        with destination.open('x', encoding='utf-8') as out: json.dump(payload, out, allow_nan=False)
    return {'records': len(body.result['records']), 'diagnostic_id': audit['evidence']['diagnostic_id'],
        'records_sha256': digest, 'snapshot_sha256': snapshot_hash, 'local_file': str(destination.relative_to(ROOT)), 'inference_performed': False}


class LabPredictionRequest(MaskMotionRequest):
    freeze_frame: int = Field(default=29,ge=7)
    horizon: int = Field(default=20,ge=1,le=120)


@app.post('/api/videos/{identity}/lab/freeze')
def lab_freeze(identity: str, body: LabPredictionRequest):
    from backend.reality_lab import freeze
    _, info = video_files(identity)
    try:
        return freeze(body.result,info,body.parameters,body.object_id,body.confirmed_slider,body.freeze_frame,body.horizon,body.corrections,body.assignments)
    except (ValueError,TypeError,KeyError) as exc: raise HTTPException(422,'Insufficient evidence: '+str(exc)) from None


class LabRevealRequest(BaseModel):
    token: str = Field(min_length=32,max_length=32)


@app.post('/api/lab/reveal')
def lab_reveal(body: LabRevealRequest):
    from backend.reality_lab import reveal,SESSIONS
    import hashlib
    try:
        result=reveal(body.token)
        info=SESSIONS[body.token]['video']
        path,_=video_files(info['id'])
        result['source_video_id']=info['id']
        result['source_video_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
        encoded=json.dumps(result,sort_keys=True,allow_nan=False)
        digest=hashlib.sha256(encoded.encode()).hexdigest()
        folder=path.parent/'lab-results';folder.mkdir(exist_ok=True)
        destination=folder/(digest+'.json')
        if not destination.exists():
            with destination.open('x',encoding='utf-8') as out:out.write(encoded)
        return {**result,'evidence_id':digest}
    except ValueError as exc: raise HTTPException(422,str(exc)) from None


@app.get('/api/videos/{identity}/lab/results')
def lab_results(identity:str):
    path,_=video_files(identity)
    return [{'evidence_id':p.stem} for p in sorted((path.parent/'lab-results').glob('*.json'),key=lambda p:p.stat().st_mtime,reverse=True) if re.fullmatch('[a-f0-9]{64}',p.stem)]


@app.get('/api/videos/{identity}/lab/results/{evidence_id}')
def lab_result(identity:str,evidence_id:str):
    import hashlib
    path,_=video_files(identity)
    if not re.fullmatch('[a-f0-9]{64}',evidence_id):raise HTTPException(422,'Invalid evidence identity')
    report=path.parent/'lab-results'/(evidence_id+'.json')
    if not report.exists():raise HTTPException(404,'Preserved replay not found')
    raw=report.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=evidence_id:raise HTTPException(409,'Replay evidence integrity mismatch')
    value=json.loads(raw)
    if value['source_video_sha256']!=hashlib.sha256(path.read_bytes()).hexdigest():raise HTTPException(409,'Source video changed')
    return {**value,'evidence_id':evidence_id,'recovered':True}


class AskRequest(BaseModel):
    text: str = Field(min_length=1,max_length=1000)
    parameters: Parameters
    alternate: Parameters | None = None


@app.post('/api/lab/ask')
def lab_ask(body: AskRequest):
    from backend.reality_lab import mock_intent,execute_tool
    call=mock_intent(body.text,body.parameters)
    return {'provider':'deterministic_mock','model_live_verified':False,'call':call.model_dump(),'calculated':execute_tool(call,body.parameters,body.alternate),'inference_performed':False}


class MuseQuoteRequest(BaseModel):
    model_config=ConfigDict(extra='forbid')
    text: str = Field(default='Duplica la velocidad angular del mecanismo',min_length=1,max_length=1000)
    parameters: Parameters


@app.post('/api/lab/muse/quote')
def muse_quote(body:MuseQuoteRequest):
    from backend.muse_trial import quote
    return quote(body.text,body.parameters)


class MuseRunRequest(BaseModel):
    model_config=ConfigDict(extra='forbid')
    token: str = Field(min_length=32,max_length=32)
    approved: bool = False


@app.post('/api/lab/muse/run')
async def muse_run(body:MuseRunRequest):
    from backend.muse_trial import run
    return await run(body.token,body.approved,DATA/'muse-evidence')


DIST=ROOT/'frontend'/'dist'
if DIST.exists():
    from fastapi.staticfiles import StaticFiles
    app.mount('/',StaticFiles(directory=DIST,html=True),name='studio')
