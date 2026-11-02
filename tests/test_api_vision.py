import json
import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient
from backend import main
from backend.vision import inspect_video,track_points


@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setattr(main,'DATA',tmp_path/'data');main.DATA.mkdir()
    monkeypatch.delenv('MODEL_API_KEY',raising=False)
    return TestClient(main.app)


def make_video(path,occlusion=False):
    writer=cv2.VideoWriter(str(path),cv2.VideoWriter_fourcc(*'mp4v'),30,(320,240))
    assert writer.isOpened()
    for i in range(60):
        image=np.full((240,320,3),220,np.uint8)
        if not occlusion or i<20:
            cv2.rectangle(image,(40+i,100),(60+i,120),(20,20,20),-1)
            cv2.rectangle(image,(47+i,107),(53+i,113),(250,250,250),-1)
        writer.write(image)
    writer.release()


def test_video_import_track_export(client,tmp_path):
    path=tmp_path/'synthetic.mp4';make_video(path)
    info=inspect_video(path)
    assert info['frames']==60 and info['width']==320
    result=client.post('/api/videos',files={'file':('synthetic.mp4',path.read_bytes(),'video/mp4')})
    assert result.status_code==200,result.text
    identity=result.json()['id']
    assert client.get(f'/api/videos/{identity}/media',headers={'Range':'bytes=0-100'}).status_code==206
    assert client.get(f'/api/videos/{identity}/thumbnail/0').headers['content-type']=='image/jpeg'
    tracked=client.post(f'/api/videos/{identity}/track',json={'start_frame':0,'seeds':[{'x':50,'y':110,'joint':'slider'}]})
    assert tracked.status_code==200
    points=tracked.json()['observations'];assert len(points)>40
    assert abs(points[-1]['x']-(50+points[-1]['frame']))<1
    payload={'parameters':{'r':32,'L':128},'calibration':{},'observations':points}
    export=client.post('/api/export/csv',json=payload)
    assert export.status_code==200 and 'opencv-lk' in export.text and 'error_px' in export.text
    quote=client.post('/api/meta/quote',json={'video_id':identity,'action':'sam'}).json()
    assert quote['estimated_usd']==.012
    assert client.post('/api/meta/run',json={'token':quote['token'],'video_id':identity,'approved':True}).status_code==503


def test_occlusion_is_reported(tmp_path):
    path=tmp_path/'occlusion.mp4';make_video(path,True)
    result=track_points(path,[{'x':50,'y':110,'joint':'slider'}],0)
    assert result['lost']
    lost_frame=result['lost'][0]['frame']
    assert all(o['frame']<lost_frame for o in result['observations'])


def test_bad_files_and_origin(client):
    assert client.post('/api/videos',files={'file':('bad.exe',b'bad')}).status_code==415
    assert client.post('/api/videos',files={'file':('bad.mp4',b'bad')}).status_code==422
    assert client.get('/api/videos/not-an-id/media').status_code==404
    assert client.post('/api/fit',headers={'Origin':'https://evil.example'},json={}).status_code==403
    assert client.get('/api/meta/status').json()['key_configured'] is False
    assert client.get('/api/meta/catalogue').status_code==503


def test_frame_leakage_rejected(client):
    a={'frame':1,'t':1,'x':1,'y':1,'joint':'crank','source':'manual','split':'fit'}
    b={**a,'joint':'slider','split':'validation'}
    assert client.post('/api/compare',json={'parameters':{},'calibration':{},'observations':[a,b]}).status_code==422


def test_backend_frontend_fixture(client):
    fixture=json.loads((main.ROOT/'sample-data'/'engine-golden.json').read_text())
    from backend.kinematics import solve,Parameters
    for row in fixture:
        actual=solve(Parameters(**row['p']),row['t'])
        assert actual['A']==pytest.approx(row['A'],abs=1e-10)
        assert actual['B']==pytest.approx(row['B'],abs=1e-10)
