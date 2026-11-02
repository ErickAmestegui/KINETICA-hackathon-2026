import {describe,it,expect} from 'vitest';
import {samSummary,isSamResult,type SamResult} from './samStatus';

describe('SAM outcome presentation',()=>{
 it('visibly labels mock outcomes separately from real footage provenance',()=>{
  expect(samSummary({records:[],outcome:{status:'completed'},simulated:true})).toContain('SIMULATED TEST — no real Meta inference');
 });
 for(const status of ['completed','incomplete','failed'] as const){
  it(`identifies ${status} without claiming reconstruction`,()=>{
   const result:SamResult={records:[],outcome:{status},remote_file_cleanup:'deleted'};
   expect(isSamResult(result)).toBe(true);
   expect(samSummary(result)).toContain(`SAM ${status}`);
   expect(samSummary(result)).toContain('not a verified reconstruction');
  });
 }
 it('reports cleanup failure and transport category separately',()=>{
  const text=samSummary({records:[],outcome:{status:'failed'},failure:{category:'http',phase:'response_http',http_status:402},remote_file_cleanup:'failed'});
  expect(text).toContain('HTTP 402');expect(text).toContain('Check remote files manually');
 });
 it('rejects missing or unknown outcome',()=>{
  expect(isSamResult({records:[]})).toBe(false);
  expect(isSamResult({records:[],outcome:{status:'verified'}})).toBe(false);
 });
});
