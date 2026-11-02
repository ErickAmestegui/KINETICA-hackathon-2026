from backend.kinematics import Parameters,Calibration,Observation,compare

def test_relabeling_fitted_frame_invalidates_heldout_claim():
    o=Observation(frame=5,t=0,x=160,y=0,joint='slider',source='manual',split='validation')
    result=compare(Parameters(),[o],Calibration(),trained_frames=[5])
    assert result['validation']['rmse_px'] is None
    assert 'previously used' in result['validation']['reason']

def test_scale_is_declared_not_verified():
    result=compare(Parameters(),[],Calibration(unit='mm'))
    assert result['physical_scale_user_declared'] is True
    assert 'physical_scale_verified' not in result
