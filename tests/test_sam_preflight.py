"""Budget/gate tests: temporary local metadata and mocked inference, never network."""
import asyncio
import json
import time

import pytest
from fastapi import HTTPException
from backend import main, meta


@pytest.fixture
def clips(tmp_path, monkeypatch):
    monkeypatch.setattr(main, 'DATA', tmp_path)
    monkeypatch.setattr(main, 'quotes', {})
    for identity, frames in [('a'*32,442),('b'*32,50)]:
        folder=tmp_path/identity;folder.mkdir()
        (folder/'metadata.json').write_text(json.dumps({'name':f'eitech-{frames}.mp4', 'frames':frames,
            'width':960,'height':540,'duration':frames/25,'extension':'.mp4'}))
    return 'a'*32,'b'*32


def test_budget_binds_exact_clip_and_one_request(clips):
    old,new=clips
    q_old=main.quote(main.QuoteRequest(video_id=old,action='sam'))
    q=main.quote(main.QuoteRequest(video_id=new,action='sam'))
    assert q_old['estimated_usd']==.0884
    assert q['estimated_usd']==.01 and q['source']['frames']==50
    assert q['video_id']==new and q['request_count']==1 and q['action']=='sam'
    assert q['status']['paid_enabled'] is False
    assert q_old['token']!=q['token']


def test_gate_blocks_valid_approved_quote_before_transport(clips,monkeypatch):
    monkeypatch.setenv('MODEL_API_KEY','MOCK-NOT-A-CREDENTIAL')
    def forbidden(*args,**kwargs): raise AssertionError('Transport must not execute')
    monkeypatch.setattr(meta,'segment',forbidden)
    q=main.quote(main.QuoteRequest(video_id=clips[1],action='sam'))
    with pytest.raises(HTTPException) as caught:
        asyncio.run(main.infer(main.InferRequest(token=q['token'],video_id=clips[1],approved=True,prompt='white foam block')))
    assert caught.value.status_code==403


def test_mismatch_expiry_and_token_reuse_without_enabling_paid(clips,monkeypatch):
    # Both authorization and transport are local stubs. Environment stays false.
    monkeypatch.setattr(meta,'authorize',lambda approved:None)
    calls=[]
    async def mock_segment(path, info, prompt, regions, approved):
        calls.append((info['frames'],prompt))
        return {'outcome':{'status':'completed'},'provenance':'SYNTHETIC TEST ONLY'}
    monkeypatch.setattr(meta,'segment',mock_segment)
    old,new=clips
    q=main.quote(main.QuoteRequest(video_id=old,action='sam'))
    with pytest.raises(HTTPException) as caught:
        asyncio.run(main.infer(main.InferRequest(token=q['token'],video_id=new,approved=True)))
    assert caught.value.status_code==409 and not calls
    q=main.quote(main.QuoteRequest(video_id=new,action='sam'))
    main.quotes[q['token']]['expires']=time.time()-1
    with pytest.raises(HTTPException) as caught:
        asyncio.run(main.infer(main.InferRequest(token=q['token'],video_id=new,approved=True)))
    assert caught.value.status_code==403 and not calls
    q=main.quote(main.QuoteRequest(video_id=new,action='sam'))
    request=main.InferRequest(token=q['token'],video_id=new,approved=True,prompt='white foam block')
    asyncio.run(main.infer(request))
    with pytest.raises(HTTPException) as caught: asyncio.run(main.infer(request))
    assert caught.value.status_code==403 and calls==[(50,'white foam block')]
    assert meta.status()['paid_enabled'] is False
