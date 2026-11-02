import {test,expect} from './fixtures';
import path from 'node:path';
import fs from 'node:fs';

for(const status of ['completed','incomplete','failed'] as const){
 test(`mock SAM ${status} stays explicit in overlays, saved study and report`,async({page})=>{
  let calls=0;
  const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
  // Synthetic UI-only permissions. The actual server remains META_ALLOW_PAID=false.
  const mockStatus={key_configured:true,paid_enabled:true,verified_live:false,message:'OFFLINE MOCK — no Meta request'};
  const result={records:[{kind:'box',object_id:'0',frame:0,left:140,top:170,right:160,bottom:190}],
   outcome:{status,...(status==='incomplete'?{reason:'eof'}:{})},
   failure:status==='failed'?{phase:'response_stream',category:'timeout',parser_code:'source_error'}:null,
   diagnostics:[],remote_file_cleanup:status==='failed'?'failed':'deleted',reconstruction_verified:false,
   diagnostic:{id:'offline-fixture'},simulated:true,provenance:'SYNTHETIC UI TEST ONLY'};
  await page.route('**/api/meta/status',r=>r.fulfill({json:mockStatus}));
  await page.route('**/api/meta/quote',r=>r.fulfill({json:{token:'offline-only',video_id:r.request().postDataJSON().video_id,action:'sam',request_count:1,source:{name:'synthetic-slider-crank.mp4',frames:120,width:640,height:360,duration:4},estimated_usd:0,detail:'SYNTHETIC TEST; no charge',status:mockStatus}}));
  await page.route('**/api/meta/run',r=>{calls++;return r.fulfill({status:status==='failed'?502:200,json:status==='failed'?{detail:result}:result});});
  await page.goto('/');
  await page.locator('input[type=file]').first().setInputFiles(path.resolve('../output/synthetic-slider-crank.mp4'));
  await expect(page.getByRole('tab',{name:'Compare',exact:true})).toHaveAttribute('aria-selected','true');
  await page.getByRole('button',{name:'Model connections'}).click();
  await page.getByRole('button',{name:'Prepare cost estimate'}).click();
  await page.getByRole('button',{name:'Authorize this paid request'}).click();
  await expect(page.getByRole('dialog').locator('.sam-status')).toContainText(`SAM ${status}`);
  await expect(page.getByRole('dialog').locator('.sam-status')).toContainText('not a verified reconstruction');
  await expect(page.getByRole('dialog').locator('.sam-status')).toContainText('SIMULATED TEST');
  if(status==='failed')await expect(page.getByRole('dialog').locator('.sam-status')).toContainText('Check remote files manually');
  await page.keyboard.press('Escape');
  await expect(page.locator('.video-wrap:not(.hidden) .sam-status')).toContainText(`SAM ${status}`);
  await page.screenshot({path:`../output/playwright/sam-mock-${status}.png`,fullPage:true});
  await page.getByRole('button',{name:'My machines'}).click();
  await page.getByRole('button',{name:'Save current study'}).click();await page.keyboard.press('Escape');
  await page.reload();await page.getByRole('button',{name:'My machines'}).click();
  await page.getByRole('button',{name:'Restore saved study'}).click();
  await expect(page.locator('.notification')).toContainText('Study restored');
  await page.getByRole('tab',{name:'Report',exact:true}).click();
  await expect(page.locator('.report-panel .sam-status')).toContainText(`SAM ${status}`);
  const download=page.waitForEvent('download');await page.getByRole('button',{name:'Export validation report'}).click();
  const file=await (await download).path();const report=JSON.parse(fs.readFileSync(file!,'utf8'));
  expect(report.samResult.outcome.status).toBe(status);expect(report.samResult.reconstruction_verified).toBe(false);
  expect(report.aiEvidence.at(-1).result.provenance).toBe('SYNTHETIC UI TEST ONLY');
  expect(calls).toBe(1);expect(errors).toEqual([]);
 });
}

test('unmocked inference routes are blocked by the offline browser harness',async({page})=>{
 await page.goto('/');
 const code=await page.evaluate(async()=>{const r=await fetch('/api/meta/run',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({approved:true,token:'never-real'})});return r.status;});
 expect(code).toBe(403);
});
