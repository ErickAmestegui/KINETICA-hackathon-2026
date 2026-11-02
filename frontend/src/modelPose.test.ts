import {it,expect} from 'vitest';
import {modelPose} from './modelPose';
import {defaults} from './engine';
it('keeps rendered rod endpoints connected with normalized dimensions and eccentric ground clearance',()=>{
 for(const p of [defaults,{...defaults,r:13.2,L:141,e:-60},{...defaults,r:10,e:-24},{...defaults,r:55,L:210,e:24}]){
  for(let i=0;i<200;i++){
   const pose=modelPose(p,i/100);
   expect(Math.hypot(...pose.B.map((v,j)=>v-pose.A[j]))*pose.scale).toBeCloseTo(p.L,9);
   expect(pose.B[1]-.3).toBeGreaterThan(pose.baseTop);
   expect(pose.A[1]-.25).toBeGreaterThan(pose.baseTop);
   expect(pose.A[2]-.08).toBeGreaterThan(.8); // moving rod clears fixed guide-support envelope
  }
 }
});
