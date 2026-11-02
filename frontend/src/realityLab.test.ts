import {describe,it,expect} from 'vitest';
import {strokeParameters} from './RealityLab';
import {defaults,solve} from './engine';
describe('counterfactual motion uses validated solver geometry',()=>{
 it('inverts a centered stroke while retaining the original',()=>{const next=strokeParameters(defaults,100)!;expect(next.r).toBe(50);expect(defaults.r).toBe(32);expect(solve(next,0).B[0]-solve(next,30/next.rpm).B[0]).toBeCloseTo(100);});
 it('rejects impossible, uncalibrated eccentric inversion and nonfinite requests',()=>{expect(strokeParameters(defaults,300)).toBeNull();expect(strokeParameters({...defaults,e:2},100)).toBeNull();expect(strokeParameters(defaults,NaN)).toBeNull();});
});
