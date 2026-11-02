import {solve,type Parameters} from './engine';
export function modelPose(p:Parameters,t:number){
 const state=solve(p,t);
 const scale=Math.max(32,(p.L+p.r)/6);
 const r=p.r/scale,L=p.L/scale,e=p.e/scale;
 const baseTop=Math.min(-r-.5,e-.55);
 return {state,scale,r,L,e,baseTop,A:[state.A[0]/scale,state.A[1]/scale,1.03] as [number,number,number],B:[state.B[0]/scale,state.B[1]/scale,1.03] as [number,number,number],floor:baseTop-.6};
}
