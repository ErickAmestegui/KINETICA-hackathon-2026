"""Synthetic protocol tests; no authentic Meta evidence is fabricated."""
import copy
import pytest
from pydantic import ValidationError
from backend.kinematics import Parameters,solve
from backend.reality_lab import freeze,reveal,ToolCall,mock_intent,execute_tool,muse_request,parse_muse_response,SESSIONS
from test_mask_motion import VIDEO,fixture


def recording():
    p=Parameters(r=12,L=60,rpm=95,phase=.7);result=fixture()
    for row in result['records']:
        if row['object_id']=='moving':
            x=100+solve(p,row['frame']/25)['B'][0]
            box=dict(left=x-5,right=x+5,top=20,bottom=30)
            if row['kind']=='box':row.update(box)
            else:row['bounds']=box
    return p,result


def test_prediction_is_blind_to_hidden_geometry_and_hidden_corrections():
    p,result=recording();a=freeze(result,VIDEO,p,'moving',True,29,8)
    assert 'metrics' not in a and 'rows' not in a
    assert a['protocol']['training_frames']==list(range(30))
    assert a['protocol']['prediction_frames']==list(range(30,38))
    changed=copy.deepcopy(result)
    for row in changed['records']:
        if row['frame']>=30:
            bounds=row if row['kind']=='box' else row['bounds'];bounds['left']+=20;bounds['right']+=20
    # Even a previously fitted timing seed cannot leak into the optimizer.
    b=freeze(changed,VIDEO,p.model_copy(update={'rpm':10,'phase':3}),'moving',True,29,8,[{'frame':31,'x':180,'y':30}])
    assert a['predictions']==b['predictions']
    assert a['training_sha256']==b['training_sha256']
    r=reveal(a['token']);s=reveal(b['token'])
    assert r['evaluation_valid'] and r['metrics']['model_rmse_px']<1e-5
    assert s['metrics']['model_rmse_px']>10
    assert r['n']==8
    assert r['metrics']['constant_rmse_px']>r['metrics']['model_rmse_px']
    assert r['metrics']['linear_rmse_px']>r['metrics']['model_rmse_px']


def test_cut_and_missing_masks_invalidate_score_not_original_measurements():
    p,result=recording();result['diagnostic']['id']='e14d21bb8f3c'
    a=freeze(result,VIDEO,p,'moving',True,29,20)
    r=reveal(a['token']);assert not r['evaluation_valid']
    assert all(v is None for v in r['metrics'].values())
    assert '37–38' in r['reason']
    result['diagnostic']['id']='synthetic-only'
    result['records']=[row for row in result['records'] if not(row['object_id']=='moving' and row['frame']==32 and row['kind']=='mask')]
    b=freeze(result,VIDEO,p,'moving',True,29,8)
    assert reveal(b['token'])['n']==7 and not reveal(b['token'])['evaluation_valid']


def test_evidence_and_token_guards():
    p,result=recording()
    with pytest.raises(ValueError,match='Confirm'):freeze(result,VIDEO,p,'moving',False,29,8)
    with pytest.raises(ValueError,match='split'):freeze(result,VIDEO,p,'moving',True,29,30)
    with pytest.raises(ValueError):freeze(result,VIDEO,p,'moving',True,8,8)
    with pytest.raises(ValueError,match='expired'):reveal('x'*32)


def test_mock_proposals_require_review_and_never_mutate_input():
    p=Parameters();call=mock_intent('Quiero duplicar el recorrido',p)
    output=execute_tool(call,p)
    assert output['requires_confirmation'] and output['proposed']['r']==64 and p.r==32
    invalid=execute_tool(ToolCall(name='propose_parameter_change',arguments={'parameter':'r','value':200}),p)
    assert not invalid['valid']
    with pytest.raises(ValidationError):ToolCall(name='run_shell',arguments=None)
    with pytest.raises(ValidationError):ToolCall(name='get_mechanism_state',arguments=None,path='private')
    with pytest.raises(ValueError):execute_tool(ToolCall(name='validate_geometry',arguments={'parameter':'r','value':20}),p)
    payload=muse_request([{'role':'user','content':'test'}])
    assert payload['model']=='muse-spark-1.3' and payload['response_format']['json_schema']['strict']
    assert payload['response_format']['json_schema']['schema']['additionalProperties'] is False
    parsed=parse_muse_response({'choices':[{'finish_reason':'stop','message':{'content':call.model_dump_json()}}]})
    assert parsed==call
    with pytest.raises(ValueError,match='incomplete'):
        parse_muse_response({'choices':[{'finish_reason':'length','message':{'content':call.model_dump_json()}}]})
