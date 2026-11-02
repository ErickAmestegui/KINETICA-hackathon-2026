"""Single-request Muse tool-calling trial. Quoting is offline; sending is gated."""
import asyncio
import hashlib
import json
import os
import re
import time
import uuid
from pathlib import Path

import httpx
from fastapi import HTTPException
from backend import meta
from backend.reality_lab import ChangeArgs,ToolCall,execute_tool
from backend.kinematics import Parameters,solve

TRIAL_TEXT='Duplica la velocidad angular del mecanismo'
QUOTES={}
LOCK=asyncio.Lock()
INPUT_RATE=1.25/1_000_000
OUTPUT_RATE=4.25/1_000_000


def request_payload(text,p):
    # No images, recordings, joint observations or private paths leave the backend.
    return {'model':'muse-spark-1.3','messages':[
        {'role':'system','content':'Interpret the instruction by proposing the permitted parameter-change function. Never execute code. Parameters are relative model units; a proposal requires user review. Current parameters: '+json.dumps(p.model_dump(),sort_keys=True)},
        {'role':'user','content':text}],
        'tools':[{'type':'function','function':{'name':'propose_parameter_change','description':'Propose a bounded parameter change for local validation and user confirmation. rpm denotes angular speed in the declared model clock.','strict':True,
            'parameters':{'type':'object','properties':{'parameter':{'type':'string','enum':['r','L','rpm','phase','stroke']},'value':{'type':'number'}},'required':['parameter','value'],'additionalProperties':False}}}],
        'tool_choice':'auto','parallel_tool_calls':False,'max_completion_tokens':512,'stream':False}


def quote(text,p):
    now=time.time()
    for token,q in list(QUOTES.items()):
        if q['expires']<now:QUOTES.pop(token,None)
    if len(QUOTES)>=100:raise HTTPException(429,'Too many pending Muse estimates')
    payload=request_payload(text,p)
    encoded=json.dumps(payload,ensure_ascii=False,sort_keys=True).encode()
    # No authoritative provider tokenizer is called during offline preparation.
    allowance=max(2048,len(encoded)+256)
    token=uuid.uuid4().hex
    budget=allowance*INPUT_RATE+512*OUTPUT_RATE
    public={'token':token,'model':'muse-spark-1.3','request_count':1,'retry_count':0,'input_token_allowance':allowance,'output_token_limit':512,'estimated_usd':round(budget,8),'estimate_method':'Conservative UTF-8-byte allowance + framing; not an authoritative token count or guaranteed billing ceiling','rates_usd_per_million':{'input':1.25,'output':4.25},'price_checked':'2026-10-29','expires_in_seconds':300,'request_sha256':hashlib.sha256(encoded).hexdigest(),'text':text,'parameters':p.model_dump(),'status':meta.status()}
    QUOTES[token]={'public':public,'payload':payload,'parameters':p,'expires':now+300}
    return public


def parse_call(response):
    if not isinstance(response,dict):raise ValueError('Invalid Muse response envelope; no tool executed')
    try:
        if not isinstance(response.get('choices'),list) or len(response['choices'])!=1:raise ValueError()
        choice=response['choices'][0];message=choice['message']
        if choice.get('finish_reason')!='tool_calls' or message.get('refusal'):raise ValueError()
        calls=message.get('tool_calls')
        if not isinstance(calls,list) or len(calls)!=1:raise ValueError()
        call=calls[0]
        if call.get('type')!='function' or not isinstance(call.get('id'),str) or not 1<=len(call['id'])<=64:raise ValueError()
        function=call['function']
        if function['name']!='propose_parameter_change':raise ValueError()
        args=function['arguments']
        if not isinstance(args,str) or len(args)>2000:raise ValueError()
        return ToolCall(name=function['name'],arguments=ChangeArgs.model_validate_json(args))
    except (KeyError,TypeError,ValueError,IndexError):
        raise ValueError('No valid single permitted Muse tool call; no tool executed, no retry') from None


async def run(token,approved,directory):
    # Gate BEFORE credentials/client creation. False-created estimates are unusable.
    if os.getenv('META_ALLOW_PAID','false').lower()!='true' or approved is not True:
        raise HTTPException(403,'Paid Muse trial blocked; explicit authorization and a NEW enabled estimate are required')
    if LOCK.locked():raise HTTPException(409,'One Muse trial is already running')
    async with LOCK:
        entry=QUOTES.pop(token,None)
        if not entry or entry['expires']<time.time() or not entry['public']['status']['paid_enabled']:
            raise HTTPException(403,'Estimate expired, disabled or used; prepare a new estimate')
        headers=meta.headers()
        diagnostic=uuid.uuid4().hex[:12]
        folder=Path(directory)
        record={'diagnostic_id':diagnostic,'status':'prepared','phase':'preflight','request_sha256':entry['public']['request_sha256'],'planned_request_count':1,'request_count':0,'retry_count':0,'http_status':None,'usage':{},'provider_receipt_confirmed':False,'model_live_verified':False,'events':[]}
        def preserve():
            folder.mkdir(parents=True,exist_ok=True)
            destination=folder/f'diagnostic-{diagnostic}.json'
            pending=destination.with_suffix('.tmp')
            pending.write_text(json.dumps(record,allow_nan=False),'utf-8')
            # Windows denies replacing a file another process (scanner, indexer, reader) holds open.
            for attempt in range(40):
                try:
                    pending.replace(destination);return
                except PermissionError:
                    if attempt==39:raise
                    time.sleep(.05)
        def phase(value):
            record['phase']=value;record['events'].append({'phase':value,'at_unix':time.time()})
            preserve()
        try:
            # Fail locally before spending if diagnostic storage is unavailable.
            phase('preflight')
            record['status']='request_started';phase('transport')
            async with httpx.AsyncClient(timeout=httpx.Timeout(45),transport=httpx.AsyncHTTPTransport(retries=0),follow_redirects=False) as client:
                record['request_count']=1
                response=await client.post(meta.BASE+'/chat/completions',headers=headers,json=entry['payload'])
            record['http_status']=response.status_code;record['provider_receipt_confirmed']=True
            request_id=response.headers.get('x-request-id','')
            if re.fullmatch(r'[A-Za-z0-9_.:-]{1,128}',request_id):record['provider_request_id']=request_id
            phase('http_response')
            meta.check_response(response)
            if len(response.content)>128_000:raise ValueError('response_size')
            record['phase']='response_decode'
            data=response.json()
            usage=data.get('usage') if isinstance(data,dict) else None
            if not isinstance(usage,dict):usage={}
            usage={key:value for key,value in usage.items() if key in ('prompt_tokens','completion_tokens','total_tokens') and isinstance(value,int) and not isinstance(value,bool) and value>=0}
            record['usage']=usage
            if isinstance(data,dict) and isinstance(data.get('choices'),list):
                record['finish_reasons']=[c.get('finish_reason') if c.get('finish_reason') in ('stop','tool_calls','length','content_filter') else 'unknown' for c in data['choices'] if isinstance(c,dict)]
                record['tool_call_counts']=[len(c.get('message',{}).get('tool_calls') or []) for c in data['choices'] if isinstance(c,dict) and isinstance(c.get('message'),dict)]
            phase('response_decoded') # Token usage survives a later parser failure.
            record['phase']='tool_parser';call=parse_call(data)
            record['phase']='local_validation';calculated=execute_tool(call,entry['parameters'])
            if calculated.get('valid') and calculated.get('proposed'):
                proposed=Parameters(**calculated['proposed'])
                calculated['kinematic_preview']={'t_seconds':.25,'original':solve(entry['parameters'],.25),'proposed':solve(proposed,.25),'units':'relative model units; not measured forces or physical shaft speed'}
            result={'provider':'meta_live','model_live_verified':True,'model':'muse-spark-1.3','diagnostic_id':diagnostic,'call':call.model_dump(),'calculated':calculated,'usage':usage,'inference_performed':True,'request_count':1,'retry_count':0,'parameters':entry['parameters'].model_dump(),'request_sha256':entry['public']['request_sha256'],'requires_user_confirmation':True,'applied':False}
            if 'prompt_tokens' in usage and 'completion_tokens' in usage:result['calculated_usage_usd']=usage['prompt_tokens']*INPUT_RATE+usage['completion_tokens']*OUTPUT_RATE
            record['phase']='result_persistence'
            with (folder/f'muse-{diagnostic}.json').open('x',encoding='utf-8') as out:json.dump(result,out,allow_nan=False)
            record['status']='completed';record['model_live_verified']=True;phase('completed')
            return result
        except (HTTPException,httpx.HTTPError,ValueError,TypeError,KeyError,OSError) as exc:
            category='http' if isinstance(exc,HTTPException) else 'timeout' if isinstance(exc,httpx.TimeoutException) else 'connection' if isinstance(exc,httpx.ConnectError) else 'disconnection' if isinstance(exc,(httpx.ReadError,httpx.RemoteProtocolError)) else 'transport' if isinstance(exc,httpx.HTTPError) else 'persistence' if isinstance(exc,OSError) else 'parser' if record['phase'] in ('tool_parser','response_decode') else 'validation'
            if category=='parser' and record['phase']=='tool_parser':
                reasons=record.get('finish_reasons',[])
                if 'length' in reasons:category='incomplete_response'
                elif 'content_filter' in reasons:category='refusal'
                elif reasons==['stop']:category='no_tool_call'
            record.update(status='failed',category=category)
            try:preserve()
            except OSError:record['diagnostic_persistence_failed']=True
            # Never include exception strings, private response bodies or headers.
            raise HTTPException(502,{'message':'Muse trial failed; no retry. Review diagnostic and prior usage before authorizing another request.','diagnostic_id':diagnostic,'category':category,'phase':record['phase'],'http_status':record['http_status'],'usage':record['usage'],'provider_receipt_confirmed':record['provider_receipt_confirmed'],'diagnostic_persistence_failed':record.get('diagnostic_persistence_failed',False)}) from None
