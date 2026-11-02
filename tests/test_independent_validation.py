import copy
import pytest
from backend.independent_validation import seal,evaluate

def test_future_manual_labels_are_separate_and_sealed_inputs_immutable():
    protocol={'status':'preregistered_local','video_sha256':'a'*64,'freeze_frame':10,'horizon':3}
    forecast={'protocol':{'freeze_frame':10,'horizon':3,'training_frames':list(range(11))},'axis':{'origin':[0,0],'direction':[1,0]},'predictions':[{'frame':i,'t':i/25,'predicted_px':i,'constant_px':10,'linear_px':i+1} for i in range(11,14)]}
    frozen=seal(protocol,forecast)
    labels={'video_sha256':'a'*64,'source':'manual_future_blinded','points':[{'frame':i,'t':i/25,'x':i,'y':0} for i in range(11,14)]}
    r=evaluate(frozen,labels)
    assert r['metrics']['model_rmse_px']==0 and r['metrics']['linear_rmse_px']==1
    assert r['independence_verified'] is False
    bad=copy.deepcopy(frozen);bad['forecast']['predictions'][0]['predicted_px']=100
    with pytest.raises(ValueError,match='changed'):evaluate(bad,labels)
    with pytest.raises(ValueError,match='Revealed'):seal(protocol,{**forecast,'metrics':{}})
    with pytest.raises(ValueError,match='frame set'):evaluate(frozen,{**labels,'points':labels['points'][:-1]})
