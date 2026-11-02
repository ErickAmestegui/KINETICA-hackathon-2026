import {describe,it,expect} from 'vitest';
import {solve,defaults,compare,project} from './engine';
import golden from '../../sample-data/engine-golden.json';
describe('geometry and coordinate conventions',()=>{
 it('matches shared Python reference states used by the 3D assembly',()=>{for(const row of golden){const s=solve(row.p,row.t);s.A.forEach((v,i)=>expect(v).toBeCloseTo(row.A[i],10));s.B.forEach((v,i)=>expect(v).toBeCloseTo(row.B[i],10));}});
 it('preserves both links across a full eccentric revolution',()=>{for(const e of [-12,0,12]) for(let i=0;i<1000;i++){const p={...defaults,e};const s=solve(p,i*.007);expect(Math.hypot(...s.A)).toBeCloseTo(p.r,10);expect(s.rodError).toBeLessThan(1e-10);expect(s.B[1]).toBe(e);}});
 it('rejects impossible and singular assemblies',()=>{expect(()=>solve({...defaults,L:32},0)).toThrow();expect(()=>solve({...defaults,r:NaN},0)).toThrow();});
 it('does not call a fitted frame held-out after relabeling',()=>{const result=compare(defaults,[{frame:5,t:0,x:160,y:0,joint:'slider',source:'manual',split:'validation'}],{ox:0,oy:0,scale:1,angle:0,unit:'relative'},[5]);expect(result.validation.rmse_px).toBeNull();expect(result.validation.reason).toContain('used for fitting');});
 it('has the correct dead centers',()=>{expect(solve(defaults,0).B[0]).toBe(160);expect(solve(defaults,.75).B[0]).toBe(96);});
 it('matches analytic velocity to central differences',()=>{const p={...defaults,e:8};const t=.37,h=1e-6;expect(solve(p,t).velocity).toBeCloseTo((solve(p,t+h).B[0]-solve(p,t-h).B[0])/(2*h),5);});
 it('projects y up into video y down and computes a held-out metric',()=>{const c={ox:50,oy:80,angle:0,scale:2,unit:'relative' as const};expect(project([3,4],c)).toEqual([56,72]);const pt=project(solve(defaults,0).B,c);const a=compare(defaults,[{frame:0,t:0,x:pt[0]+3,y:pt[1]+4,joint:'slider',source:'manual',split:'validation'}],c);expect(a.validation.rmse_px).toBe(5);expect(a.fit.rmse_px).toBeNull();});
});
