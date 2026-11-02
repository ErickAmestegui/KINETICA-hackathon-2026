export type Parameters = {r:number; L:number; rpm:number; e:number; phase:number};
export type Point = [number,number];
export const defaults:Parameters = {r:32,L:128,rpm:40,e:0,phase:0};
export function valid(p:Parameters) {return Object.values(p).every(Number.isFinite)&&p.r>0&&p.L>p.r+Math.abs(p.e)&&Math.abs(p.rpm)<=600;}
export function solve(p:Parameters,t:number) {
  if(!valid(p)||!Number.isFinite(t)) throw new Error('Invalid geometry: L must exceed r + |e|');
  const theta=p.phase+t*p.rpm*Math.PI/30;
  const A:Point=[p.r*Math.cos(theta),p.r*Math.sin(theta)];
  const q=p.e-A[1], h=Math.sqrt(p.L*p.L-q*q);
  const B:Point=[A[0]+h,p.e];
  return {theta,A,B,O:[0,0] as Point,velocity:(-p.r*Math.sin(theta)+q*p.r*Math.cos(theta)/h)*p.rpm*Math.PI/30,rodError:Math.abs(Math.hypot(B[0]-A[0],B[1]-A[1])-p.L)};
}
export type Observation={frame:number;t:number;x:number;y:number;joint:'crank'|'slider';source:'manual'|'opencv-lk'|'synthetic';split:'fit'|'validation'};
export type Calibration={ox:number;oy:number;angle:number;scale:number;unit:'relative'|'mm'};
export function project(pt:Point,c:Calibration):Point {const [x,y]=pt,co=Math.cos(c.angle),si=Math.sin(c.angle);return [c.ox+c.scale*(co*x+si*y),c.oy+c.scale*(si*x-co*y)];}
export function compare(p:Parameters,obs:Observation[],c:Calibration,trainedFrames:number[]=[]) {
  const rows=obs.map(o=>{const s=solve(p,o.t),a=project(o.joint==='crank'?s.A:s.B,c);return {...o,predicted_x:a[0],predicted_y:a[1],error_px:Math.hypot(a[0]-o.x,a[1]-o.y)};});
  const metrics=(split:string)=>{const r=rows.filter(o=>o.split===split);const contaminated=split==='validation'&&r.some(o=>trainedFrames.includes(o.frame));return {n:r.length,rmse_px:r.length&&!contaminated?Math.sqrt(r.reduce((a,o)=>a+o.error_px**2,0)/r.length):null,max_px:r.length&&!contaminated?Math.max(...r.map(o=>o.error_px)):null,reason:contaminated?'No evaluado: validation includes frames used for fitting. Refit with disjoint frames.':r.length?null:'No evaluado: no observations in this split.'};};
  return {rows,fit:metrics('fit'),validation:metrics('validation'),units:'pixels',physical_scale_user_declared:c.unit==='mm'};
}
