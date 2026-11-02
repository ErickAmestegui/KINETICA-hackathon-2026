"""Protocol fixtures are official documentation examples, NOT our live API results."""
import asyncio
import httpx
import pytest
from fastapi import HTTPException
from backend import meta
from meta_sam_parser import ResponsesStreamError

# Published meta-sam-parser 0.1.0 README example; Meta copyright / SAM License.
# Fixture content is licensed separately; see docs/licenses/SAM-LICENSE.txt.
EXAMPLE=("<0f>0<|box;x1=211;y1=228;x2=270;y2=254;w=320;h=334|>"
"<|mask;x=0;y=0;data=27,60,~!!!!M!0c[0o91w?q1!pIH4pPRVp2B3'7`e.ioeAf6-k/#Xd8%dX9x(|>\n")


async def events(text,complete=True,failed=False):
    lane={'item_id':'test-only','output_index':0,'content_index':0}
    for index in range(0,len(text),7):
        yield {'type':'response.output_text.delta',**lane,'delta':text[index:index+7]}
    yield {'type':'response.content_part.done',**lane,'part':{'type':'output_text','text':text}}
    if failed: yield {'type':'response.failed','response':{'error':{'message':'synthetic failure'}}}
    elif complete: yield {'type':'response.completed'}


def test_official_parser_chunked_mask():
    result=asyncio.run(meta.parse_sam(events(EXAMPLE)))
    assert result['outcome']['status']=='completed'
    assert len(result['records'])==2
    box,mask=result['records']
    assert box['object_id']=='0' and box['frame']==0 and box['right']==271
    assert mask['width']==60 and mask['height']==27 and mask['path']
    assert mask['bounds']['left']==211


def test_empty_incomplete_and_failure():
    result=asyncio.run(meta.parse_sam(events('')))
    assert result['records']==[] and result['outcome']['status']=='completed'
    partial=asyncio.run(meta.parse_sam(events(EXAMPLE,complete=False)))
    assert partial['outcome']['status']=='incomplete'
    assert asyncio.run(meta.parse_sam(events('',failed=True)))['outcome']['status']=='failed'


def test_malformed_not_fabricated():
    result=asyncio.run(meta.parse_sam(events('<0f>0<|box;bad|>\n')))
    assert not result['records'] and result['diagnostics']


@pytest.mark.parametrize('status',[400,401,402,403,429,500])
def test_sanitized_errors(status):
    response=httpx.Response(status,json={'error':'private-upstream-sentinel'})
    with pytest.raises(HTTPException) as exc: meta.check_response(response)
    assert str(status) in exc.value.detail
    assert 'private-upstream-sentinel' not in exc.value.detail


def test_no_key_no_payment(monkeypatch):
    monkeypatch.delenv('MODEL_API_KEY',raising=False)
    with pytest.raises(HTTPException) as exc: meta.authorize(True)
    assert exc.value.status_code==503
    monkeypatch.setenv('MODEL_API_KEY','test-key-not-real')
    monkeypatch.setenv('META_ALLOW_PAID','false')
    with pytest.raises(HTTPException) as exc: meta.authorize(True)
    assert exc.value.status_code==403
    with pytest.raises(HTTPException): meta.authorize(False)


def test_proposal_validation():
    with pytest.raises(ValueError): meta.Proposal.model_validate({'mechanism':'arbitrary-code','components':[],'joints':[],'limitations':[]})
