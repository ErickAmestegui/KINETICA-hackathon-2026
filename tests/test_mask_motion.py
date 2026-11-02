"""Synthetic geometry only. Real SAM evidence must come from a preserved export."""
import pytest
from backend.mask_motion import audit_masks, fit_projection, extract_track
from backend.kinematics import Parameters


def fixture(n=50):
    records=[]
    for frame in range(n):
        for identity,x in [('fixed',20),('moving',60+frame*2)]:
            bounds=dict(left=x,top=20,right=x+10,bottom=30)
            records.extend([dict(kind='box',object_id=identity,frame=frame,**bounds),
                dict(kind='mask',object_id=identity,frame=frame,bounds=bounds,width=10,height=10,path='M0 0L10 0L10 10L0 10Z')])
    return dict(records=records,outcome={'status':'completed'},simulated=True,diagnostic={'id':'synthetic-only'})


VIDEO=dict(width=320,height=180,frames=50,timestamps=[i/25 for i in range(50)],provenance='synthetic')


def test_centroids_motion_and_real_label():
    result=audit_masks(fixture(),VIDEO)
    assert result['counts']['records']==200
    assert result['counts']['objects']==2
    objects={o['object_id']:o for o in result['objects']}
    assert objects['fixed']['motion']=='stationary_in_image'
    assert objects['moving']['motion']=='moving_in_image'
    assert objects['moving']['samples'][0]['x']==65
    assert result['evidence']['kind']=='synthetic_test'


def test_holes_are_subtracted_in_svg_centroid():
    r=fixture(1); m=r['records'][1]
    m['path']='M0 0L10 0L10 10L0 10Z M0 0L0 5L5 5L5 0Z'
    a=audit_masks(r,VIDEO)['objects'][0]['samples'][0]
    assert a['area_px2']==75
    assert a['x']==pytest.approx(20+350/60)  # (100*5-25*2.5)/75


def test_invalid_missing_duplicate_masks_never_fall_back_to_boxes():
    r=fixture();r['records'][1]['path']='M0 0Q5 5 10 10Z'
    r['records'].append(r['records'][5].copy())
    a=audit_masks(r,VIDEO)
    fixed=next(o for o in a['objects'] if o['object_id']=='fixed')
    assert 0 not in [s['frame'] for s in fixed['samples']]
    assert 1 not in [s['frame'] for s in fixed['samples']]
    assert fixed['missing_mask_frames']==[0,1]
    assert a['issues']


def test_corrections_are_explicit_do_not_mutate_original_and_can_reassign_ids():
    r=fixture();a=audit_masks(r,VIDEO)
    track=extract_track(a,'moving',[{'frame':4,'x':90,'y':25},{'frame':5,'excluded':True}],[])
    assert track[4]['source']=='manual-centroid'
    assert track[4]['x']==90
    assert 5 not in [s['frame'] for s in track]
    assert a['objects'][1]['samples'][4]['x']==73
    reassigned=extract_track(a,'moving',[],[{'frame':4,'object_id':'fixed'}])
    assert reassigned[4]['x']==25
    with pytest.raises(ValueError,match='duplicate'):
        extract_track(a,'moving',[],[{'frame':4,'object_id':'fixed'},{'frame':4,'object_id':'moving'}])


def test_projection_reserves_frames_and_holds_geometry_fixed():
    from backend.kinematics import solve
    r=fixture();p=Parameters(r=12,L=60,rpm=40,phase=.4)
    for row in r['records']:
        if row['object_id']!='moving':continue
        x=100+2*solve(p,row['frame']/25)['B'][0]
        box=dict(left=x-5,top=20,right=x+5,bottom=30)
        if row['kind']=='box':row.update(box)
        else:row['bounds']=box
    video={**VIDEO,'width':640}
    a=audit_masks(r,video)
    report=fit_projection(a,'moving',p,video,confirmed_slider=True)
    assert report['validation']['n']==12
    assert report['validation']['rmse_px']<1e-8
    assert set(report['fit_frames']).isdisjoint(report['validation_frames'])
    assert report['parameters_held_fixed']==p.model_dump()
    assert report['projection']['gain_px_per_model_unit']==pytest.approx(2)
    # Alter ONLY held-out samples; the fitted projection and axis must not change.
    for row in r['records']:
        if row['object_id']=='moving' and row['frame']>=38:
            if row['kind']=='box':row['left']+=20;row['right']+=20
            else:row['bounds']['left']+=20;row['bounds']['right']+=20
    b=fit_projection(audit_masks(r,video),'moving',p,video,confirmed_slider=True)
    assert b['projection']==report['projection']
    assert b['validation']['rmse_px']==pytest.approx(20)


def test_no_role_or_constant_prediction_cannot_be_fitted():
    a=audit_masks(fixture(),VIDEO)
    with pytest.raises(ValueError,match='confirm'):
        fit_projection(a,'moving',Parameters(),VIDEO,confirmed_slider=False)
    with pytest.raises(ValueError,match='identifiable'):
        fit_projection(a,'moving',Parameters(rpm=0),VIDEO,confirmed_slider=True)


def test_missing_evidence_and_frame_timestamp_integrity():
    with pytest.raises(ValueError,match='records'):
        audit_masks({'records':[]},VIDEO)
    r=fixture();r.pop('simulated');r['diagnostic']['id']='different'
    with pytest.raises(ValueError,match='diagnostic'):
        audit_masks(r,VIDEO,expected_diagnostic='e14d21bb8f3c')
    with pytest.raises(ValueError,match='timestamps'):
        audit_masks(fixture(),{**VIDEO,'timestamps':[0]*50})


@pytest.mark.parametrize('path', ['L0 0L10 0L10 10L0 10Z', 'M0 0L10 0M10 10L0 10Z'])
def test_malformed_subpaths_cannot_be_measured(path):
    r=fixture(1);r['records'][1]['path']=path
    a=audit_masks(r,VIDEO)
    assert a['objects'][0]['valid_masks']==0
    assert a['issues']


def test_duplicate_box_identity_excludes_ambiguous_frame():
    r=fixture();r['records'].append(r['records'][0].copy())
    a=audit_masks(r,VIDEO)
    assert 0 in a['objects'][0]['missing_mask_frames']


def test_temporal_alerts_flag_discontinuity_without_excluding_data_or_fitting_heldout():
    r=fixture();original=audit_masks(r,VIDEO)['objects'][1]
    assert original['temporal_alerts']==[]
    for row in r['records']:
        if row['object_id']=='moving' and row['frame']>=40:
            box=row if row['kind']=='box' else row['bounds']
            box['left']+=40;box['right']+=40
    changed=audit_masks(r,VIDEO)['objects'][1]
    assert changed['temporal_threshold_px']==original['temporal_threshold_px']
    assert [a['frame'] for a in changed['temporal_alerts']]==[39,40]
    assert changed['valid_masks']==50


def test_timing_estimate_is_training_only_and_interval_is_explicit():
    from backend.kinematics import solve
    true=Parameters(r=12,L=60,rpm=95,phase=.7)
    r=fixture()
    for row in r['records']:
        if row['object_id']=='moving':
            x=100+solve(true,row['frame']/25)['B'][0]
            box=dict(left=x-5,right=x+5,top=20,bottom=30)
            if row['kind']=='box':row.update(box)
            else:row['bounds']=box
    declared=true.model_copy(update={'rpm':40,'phase':0})
    a=fit_projection(audit_masks(r,VIDEO),'moving',declared,VIDEO,True,end_frame=37,estimate_timing=True)
    assert a['parameters_used']['rpm']==pytest.approx(95,abs=.01)
    assert a['parameters_used']['phase']==pytest.approx(.7,abs=.01)
    assert a['parameters_held_fixed']=={'r':12,'L':60,'e':0}
    assert a['validation']['n']==9 and a['validation']['rmse_px']<1e-6
    assert a['interval']['selection']=='manual; retrospective'
    assert a['fit_frames']==list(range(29))
    for row in r['records']:
        if row['object_id']=='moving' and row['frame']>=29:
            box=row if row['kind']=='box' else row['bounds'];box['left']+=25;box['right']+=25
    b=fit_projection(audit_masks(r,VIDEO),'moving',declared,VIDEO,True,end_frame=37,estimate_timing=True)
    assert b['parameters_used']==a['parameters_used']
    assert b['projection']==a['projection']
    assert b['validation']['rmse_px']==pytest.approx(25)
    assert len(b['rows'])==38
    with pytest.raises(ValueError,match='interval'):
        fit_projection(audit_masks(r,VIDEO),'moving',declared,VIDEO,True,start_frame=40,end_frame=37)
