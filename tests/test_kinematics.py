import math
import numpy as np
import pytest
from backend.kinematics import Parameters, Calibration, Observation, solve, compare, project, fit_parameters


@pytest.mark.parametrize('e',[-24,0,24])
def test_constraints(e):
    p=Parameters(e=e)
    for t in np.linspace(0,3,721):
        s=solve(p,float(t))
        assert np.linalg.norm(s['A']) == pytest.approx(p.r,abs=1e-10)
        assert s['rod_error'] < 1e-10
        assert s['B'][1] == e


@pytest.mark.parametrize('values',[{'r':0},{'L':32},{'L':40,'e':8},{'r':float('nan')},{'rpm':float('inf')}])
def test_invalid(values):
    with pytest.raises(ValueError): Parameters(**values)


def test_dead_centers_velocity_and_projection():
    p=Parameters(rpm=60)
    assert solve(p,0)['B'][0] == 160
    assert solve(p,.5)['B'][0] == 96
    t=.17; h=1e-6
    assert solve(p,t)['velocity'] == pytest.approx((solve(p,t+h)['B'][0]-solve(p,t-h)['B'][0])/(2*h),rel=1e-7)
    assert project([3,4],Calibration(ox=10,oy=10,scale=2)).tolist()==[16,2]


def synthetic_observations():
    p=Parameters(r=30,L=116,rpm=45,phase=.3); c=Calibration(ox=100,oy=150,scale=2)
    obs=[]
    for i,t in enumerate(np.linspace(0,3,80)):
        for joint in ['crank','slider']:
            x,y=project(solve(p,float(t))['A' if joint=='crank' else 'B'],c)
            obs.append(Observation(frame=i,t=float(t),x=x,y=y,joint=joint,source='synthetic',split='fit' if i<60 else 'validation'))
    return p,c,obs


def test_fit_and_holdout():
    expected,c,obs=synthetic_observations()
    result=fit_parameters(Parameters(r=32,L=120,rpm=43),obs,c)
    for k in ['r','L','rpm','phase']:
        assert result['parameters'][k] == pytest.approx(getattr(expected,k),abs=1e-5)
    assert result['comparison']['validation']['n']==40
    assert result['comparison']['validation']['rmse_px'] < 1e-6
    # Perturb held-out samples: fitted values must not change.
    changed=[o.model_copy(update={'x':o.x+100}) if o.split=='validation' else o for o in obs]
    second=fit_parameters(Parameters(r=32,L=120,rpm=43),changed,c)
    assert second['parameters']==result['parameters']
    assert second['comparison']['validation']['rmse_px']==pytest.approx(100,abs=1e-5)


def test_empty_and_known_error():
    p=Parameters(); c=Calibration()
    assert compare(p,[],c)['validation']['rmse_px'] is None
    obs=[Observation(frame=0,t=0,x=163,y=4,joint='slider',source='manual')]
    assert compare(p,obs,c)['validation']['rmse_px']==5
    with pytest.raises(ValueError): fit_parameters(p,obs,c)
