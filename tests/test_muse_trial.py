import asyncio
import copy
import json
import pytest
import httpx
from fastapi import HTTPException
from backend import muse_trial as trial
from backend.kinematics import Parameters
from backend.reality_lab import mock_intent,execute_tool

def response():
    return {'choices':[{'finish_reason':'tool_calls','message':{'tool_calls':[{'id':'test-call','type':'function','function':{'name':'propose_parameter_change','arguments':json.dumps({'parameter':'rpm','value':80})}}]}}],'usage':{'prompt_tokens':200,'completion_tokens':40,'total_tokens':240}}

def test_angular_prompt_is_not_stroke_change_and_schema_matches_contract():
    p=Parameters();call=mock_intent(trial.TRIAL_TEXT,p)
    assert call.arguments.parameter=='rpm' and execute_tool(call,p)['proposed']['rpm']==80
    body=trial.request_payload(trial.TRIAL_TEXT,p)
    assert body['tool_choice']=='auto' and body['parallel_tool_calls'] is False
    schema=body['tools'][0]['function']['parameters']
    assert schema['additionalProperties'] is False and set(schema['required'])==set(schema['properties'])
    q=trial.quote(trial.TRIAL_TEXT,p)
    assert q['estimated_usd']==pytest.approx((q['input_token_allowance']*1.25+512*4.25)/1e6,abs=1e-8)
    assert q['request_count']==1 and q['retry_count']==0
    assert q['status']['paid_enabled'] is False
    with pytest.raises(ValueError):trial.parse_call([])

@pytest.mark.parametrize('mutation',['plain','many','wrong_tool','extra','string_number','boolean','nonfinite','truncated','refused'])
def test_untrusted_tool_responses_are_not_executed(mutation):
    value=response();message=value['choices'][0]['message'];fn=message['tool_calls'][0]['function']
    if mutation=='plain':value['choices'][0]['finish_reason']='stop'
    if mutation=='many':message['tool_calls']*=2
    if mutation=='wrong_tool':fn['name']='run_shell'
    if mutation=='extra':fn['arguments']='{"parameter":"rpm","value":80,"shell":"bad"}'
    if mutation=='string_number':fn['arguments']='{"parameter":"rpm","value":"80"}'
    if mutation=='boolean':fn['arguments']='{"parameter":"rpm","value":true}'
    if mutation=='nonfinite':fn['arguments']='{"parameter":"rpm","value":NaN}'
    if mutation=='truncated':value['choices'][0]['finish_reason']='length'
    if mutation=='refused':message['refusal']='refused'
    with pytest.raises(ValueError):trial.parse_call(value)

def test_disabled_gate_precedes_credentials_and_transport(monkeypatch,tmp_path):
    def denied(*a,**k):raise AssertionError('No credential/client access while disabled')
    monkeypatch.setattr(trial.meta,'headers',denied)
    q=trial.quote(trial.TRIAL_TEXT,Parameters())
    with pytest.raises(HTTPException) as e:asyncio.run(trial.run(q['token'],True,tmp_path))
    assert e.value.status_code==403
    monkeypatch.setenv('META_ALLOW_PAID','true') # synthetic gate test; never inherited, transport still forbidden
    with pytest.raises(HTTPException):asyncio.run(trial.run(q['token'],True,tmp_path))

@pytest.mark.parametrize('status',[200,402,429,500,'timeout','bad-parser'])
def test_one_mock_request_consumes_approval_even_on_failure(monkeypatch,tmp_path,status):
    calls=[];original=httpx.AsyncClient
    def handler(request):
        calls.append(request)
        if status=='timeout':raise httpx.ReadTimeout('SYNTHETIC',request=request)
        return httpx.Response(200 if isinstance(status,str) else status,json={} if status=='bad-parser' else response())
    def client(**kwargs):return original(timeout=kwargs['timeout'],transport=httpx.MockTransport(handler))
    monkeypatch.setenv('META_ALLOW_PAID','true')
    monkeypatch.setattr(trial.meta,'headers',lambda:{'Authorization':'Bearer SYNTHETIC-TEST'})
    monkeypatch.setattr(trial.httpx,'AsyncClient',client)
    q=trial.quote(trial.TRIAL_TEXT,Parameters())
    if status==200:
        value=asyncio.run(trial.run(q['token'],True,tmp_path))
        assert value['calculated']['proposed']['rpm']==80 and value['applied'] is False
        assert value['calculated']['kinematic_preview']['proposed']['rod_error']<1e-8
        assert value['requires_user_confirmation'] and len(list(tmp_path.glob('muse-*.json')))==1
        assert value['calculated_usage_usd']==pytest.approx(.00042)
    else:
        with pytest.raises(HTTPException) as error:asyncio.run(trial.run(q['token'],True,tmp_path))
        detail=error.value.detail
        assert detail['category']==('timeout' if status=='timeout' else 'parser' if status=='bad-parser' else 'http')
        assert detail['provider_receipt_confirmed']==(status!='timeout')
        records=list(tmp_path.glob('diagnostic-*.json'))
        assert len(records)==1 and json.loads(records[0].read_text())['status']=='failed'
    with pytest.raises(HTTPException):asyncio.run(trial.run(q['token'],True,tmp_path))
    assert len(calls)==1


def test_transient_windows_replace_denial_still_preserves_failed_status(monkeypatch,tmp_path):
    original=httpx.AsyncClient;real_replace=trial.Path.replace;denials=[]
    def client(**kwargs):return original(timeout=kwargs['timeout'],transport=httpx.MockTransport(lambda request:httpx.Response(200,json={})))
    def replace(self,target):
        if json.loads(self.read_text())['status']=='failed' and len(denials)<3:
            denials.append(target);raise PermissionError(13,'SYNTHETIC reader lock')
        return real_replace(self,target)
    monkeypatch.setenv('META_ALLOW_PAID','true')
    monkeypatch.setattr(trial.meta,'headers',lambda:{'Authorization':'Bearer SYNTHETIC-TEST'})
    monkeypatch.setattr(trial.httpx,'AsyncClient',client)
    monkeypatch.setattr(trial.Path,'replace',replace)
    q=trial.quote(trial.TRIAL_TEXT,Parameters())
    with pytest.raises(HTTPException) as error:asyncio.run(trial.run(q['token'],True,tmp_path))
    assert len(denials)==3 and error.value.detail['diagnostic_persistence_failed'] is False
    records=list(tmp_path.glob('diagnostic-*.json'))
    assert len(records)==1 and json.loads(records[0].read_text())['status']=='failed'


def test_usage_survives_a_truncated_provider_result(monkeypatch,tmp_path):
    original=httpx.AsyncClient;calls=[]
    def handler(request):
        calls.append(request);value=response();value['choices'][0]['finish_reason']='length'
        return httpx.Response(200,json=value,headers={'x-request-id':'SYNTHETIC-REQUEST'})
    monkeypatch.setenv('META_ALLOW_PAID','true')
    monkeypatch.setattr(trial.meta,'headers',lambda:{'Authorization':'Bearer SYNTHETIC-TEST'})
    monkeypatch.setattr(trial.httpx,'AsyncClient',lambda **kwargs:original(transport=httpx.MockTransport(handler)))
    quote=trial.quote(trial.TRIAL_TEXT,Parameters())
    with pytest.raises(HTTPException) as error:asyncio.run(trial.run(quote['token'],True,tmp_path))
    assert error.value.detail['usage']['completion_tokens']==40
    assert error.value.detail['category']=='incomplete_response'
    saved=json.loads(next(tmp_path.glob('diagnostic-*.json')).read_text())
    assert saved['finish_reasons']==['length'] and saved['http_status']==200
    assert 'Authorization' not in json.dumps(saved) and 'Bearer' not in json.dumps(saved)
    assert len(calls)==1


@pytest.mark.parametrize('fail_before_request',[True,False])
def test_persistence_failures_are_distinct_and_preflight_blocks_spend(monkeypatch,tmp_path,fail_before_request):
    from pathlib import Path
    original=httpx.AsyncClient;calls=[];open_original=Path.open
    def handler(request):calls.append(request);return httpx.Response(200,json=response())
    monkeypatch.setenv('META_ALLOW_PAID','true')
    monkeypatch.setattr(trial.meta,'headers',lambda:{'Authorization':'Bearer SYNTHETIC-TEST'})
    monkeypatch.setattr(trial.httpx,'AsyncClient',lambda **kwargs:original(transport=httpx.MockTransport(handler)))
    directory=tmp_path/'blocked'
    if fail_before_request:directory.write_text('SYNTHETIC file, not directory')
    else:
        def guarded_open(path,*args,**kwargs):
            if path.name.startswith('muse-'):raise OSError('PRIVATE-SYNTHETIC must not be exposed')
            return open_original(path,*args,**kwargs)
        monkeypatch.setattr(Path,'open',guarded_open)
    quote=trial.quote(trial.TRIAL_TEXT,Parameters())
    with pytest.raises(HTTPException) as error:asyncio.run(trial.run(quote['token'],True,directory))
    assert error.value.detail['category']=='persistence'
    assert len(calls)==(0 if fail_before_request else 1)
    assert error.value.detail['provider_receipt_confirmed']==(not fail_before_request)
    assert 'PRIVATE' not in str(error.value.detail)
    if not fail_before_request:assert error.value.detail['usage']['completion_tokens']==40
