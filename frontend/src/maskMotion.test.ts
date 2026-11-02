import {describe,it,expect} from 'vitest';
import {correctedTrack,emptyMotionState,type MaskObject} from './maskMotion';
describe('Manual mask decisions stay separate from immutable SAM geometry',()=>{
 const object:MaskObject={object_id:'a',boxes:2,masks:2,valid_masks:2,missing_mask_frames:[],motion:'moving_in_image',span_px:10,possible_id_jumps:[],samples:[{frame:0,t:0,x:10,y:20,area_px2:10,source:'sam-contour',object_id:'a'},{frame:2,t:.08,x:20,y:20,area_px2:10,source:'sam-contour',object_id:'a'}]};
 it('does not interpolate the absent frame',()=>{expect(correctedTrack(object,[object],emptyMotionState()).map(s=>s.frame)).toEqual([0,2]);});
 it('labels corrections and retains original samples',()=>{const state={...emptyMotionState(),corrections:[{frame:0,x:12,y:19}]};expect(correctedTrack(object,[object],state)[0].source).toBe('manual-centroid');expect(object.samples[0].x).toBe(10);});
 it('does not automatically confirm any object as the slider',()=>{expect(emptyMotionState().confirmedSlider).toBe(false);});
 it('excludes frames without filling the gap',()=>{expect(correctedTrack(object,[object],{...emptyMotionState(),corrections:[{frame:0,excluded:true}]}).map(s=>s.frame)).toEqual([2]);});
});
