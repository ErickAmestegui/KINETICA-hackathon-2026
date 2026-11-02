import json
import pytest
from fastapi.testclient import TestClient
from backend import main
from test_mask_motion import fixture, VIDEO


@pytest.fixture
def local_video(monkeypatch,tmp_path):
    media=tmp_path/'data'/'source.mp4';media.parent.mkdir();media.write_bytes(b'SYNTHETIC TEST ONLY')
    monkeypatch.setattr(main,'ROOT',tmp_path)
    monkeypatch.setattr(main,'video_files',lambda identity:(media,{**VIDEO,'id':identity}))
    return TestClient(main.app),media


def test_mask_analysis_never_calls_meta_and_requires_expected_diagnostic(local_video,monkeypatch):
    client,_=local_video
    def denied(*a,**kw):raise AssertionError('No inference allowed')
    monkeypatch.setattr(main.meta,'segment',denied)
    body={'result':fixture(),'object_id':'moving'}
    r=client.post('/api/videos/local/mask-motion',json=body)
    assert r.status_code==200
    data=r.json();assert data['motion'] is None
    assert data['audit']['evidence']['kind']=='synthetic_test'
    assert len(data['audit']['evidence']['video_sha256'])==64
    r=client.post('/api/videos/local/mask-motion',json={**body,'expected_diagnostic':'e14d21bb8f3c'})
    assert r.status_code==422


def test_preservation_is_content_addressed_and_original_unchanged(local_video):
    client,media=local_video
    body={'result':fixture()}
    r=client.post('/api/videos/local/preserve-segmentation',json=body)
    assert r.status_code==200
    saved=media.parent.parent/r.json()['local_file']
    assert json.loads(saved.read_text('utf-8'))['result']==body['result']
    before=saved.read_bytes()
    assert client.post('/api/videos/local/preserve-segmentation',json=body).status_code==200
    assert saved.read_bytes()==before
    changed={**body['result'],'outcome':{'status':'incomplete'}}
    other=client.post('/api/videos/local/preserve-segmentation',json={'result':changed})
    assert other.status_code==200
    assert other.json()['local_file']!=r.json()['local_file']
    assert saved.read_bytes()==before


def test_corrections_cannot_leave_the_source_image(local_video):
    client,_=local_video
    r=client.post('/api/videos/local/mask-motion',json={'result':fixture(),'object_id':'moving','corrections':[{'frame':1,'x':900,'y':20}]})
    assert r.status_code==422
    r=client.post('/api/videos/local/mask-motion',json={'result':fixture(),'object_id':'moving','confirmed_slider':True,'start_frame':30,'end_frame':20})
    assert r.status_code==422


def test_isolated_local_port_accepts_only_its_own_origin(local_video):
    client,_=local_video
    body={'result':fixture()}
    assert client.post('/api/videos/local/mask-motion',json=body,headers={'host':'127.0.0.1:8001','origin':'http://127.0.0.1:8001'}).status_code==200
    assert client.post('/api/videos/local/mask-motion',json=body,headers={'origin':'https://external.example'}).status_code==403


def test_revealed_results_survive_cleared_sessions_and_detect_tampering(local_video):
    from test_reality_lab import recording
    from backend.reality_lab import SESSIONS
    client,media=local_video;p,result=recording()
    frozen=client.post('/api/videos/local/lab/freeze',json={'result':result,'parameters':p.model_dump(),'object_id':'moving','confirmed_slider':True,'freeze_frame':29,'horizon':8})
    assert frozen.status_code==200
    revealed=client.post('/api/lab/reveal',json={'token':frozen.json()['token']})
    assert revealed.status_code==200
    identity=revealed.json()['evidence_id'];SESSIONS.clear()
    recovered=client.get('/api/videos/local/lab/results/'+identity)
    assert recovered.status_code==200 and recovered.json()['metrics']==revealed.json()['metrics']
    assert client.get('/api/videos/local/lab/results').json()[0]['evidence_id']==identity
    (media.parent/'lab-results'/(identity+'.json')).write_text('{}')
    assert client.get('/api/videos/local/lab/results/'+identity).status_code==409
