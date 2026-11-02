import {test,expect} from './fixtures';
import fs from 'node:fs';
import path from 'node:path';

test('3D labels stay below Model connections and return after closing',async({page})=>{
 await page.goto('/');
 await expect(page.locator('.part-label').first()).toBeVisible();
 await page.getByRole('button',{name:'Model connections'}).click();
 await expect(page.getByRole('dialog')).toBeVisible();
 const covered=await page.locator('.part-label').evaluateAll(labels=>labels.map(label=>{
  const r=label.getBoundingClientRect();
  if(r.right<0||r.left>innerWidth||r.bottom<0||r.top>innerHeight)return true;
  const hit=document.elementFromPoint(Math.min(innerWidth-1,Math.max(0,r.x+r.width/2)),Math.min(innerHeight-1,Math.max(0,r.y+r.height/2)));
  return !!hit?.closest('.modal-backdrop');
 }));
 expect(covered.every(Boolean)).toBe(true);
 await page.screenshot({path:'../output/playwright/sam-modal-layering.png',fullPage:true});
 await page.keyboard.press('Escape');
 await page.locator('.part-label').filter({hasText:'Connecting rod'}).click();
 await expect(page.locator('.component-strip')).toContainText('Connecting rod');
});

test('50-frame Eitech clip plays and receives its own blocked one-request estimate',async({page})=>{
 const original='<USER_HOME>/Desktop/Schubkurbelgetriebe_(Eitech) (1).mp4',clip=path.resolve('../output/sam-local/eitech-50-cfr.mp4');
 test.skip(!fs.existsSync(original)||!fs.existsSync(clip),'Private original 442-frame video and local SAM clip are not distributed');
 const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
 let inferenceRequests=0;page.on('request',r=>{if(new URL(r.url()).pathname==='/api/meta/run')inferenceRequests++;});
 await page.goto('/');
 // An older 442-frame selection must not carry its budget into a new clip.
 const imported=page.waitForResponse(r=>new URL(r.url()).pathname==='/api/videos'&&r.request().method()==='POST',{timeout:30000});
 await page.locator('input[type=file]').first().setInputFiles(original);
 expect((await imported).ok()).toBe(true);
 await expect(page.locator('.notification')).toContainText('Video imported');
 await page.getByRole('button',{name:'Model connections'}).click();
 await page.getByLabel('Object phrase').fill('white foam block');
 await page.getByRole('button',{name:'Prepare cost estimate'}).click();
 await expect(page.locator('.quote')).toContainText('US$0.0884');
 // Simulate a file change while an estimate is displayed; no stale authorization.
 await page.locator('input[type=file]').first().setInputFiles(clip);
 await expect(page.locator('.notification')).toContainText('Video imported');
 await expect(page.locator('.quote')).toHaveCount(0);
 await page.getByRole('button',{name:'Prepare cost estimate'}).click();
 await expect(page.locator('.quote')).toContainText('eitech-50-cfr.mp4');
 await expect(page.locator('.quote')).toContainText('50 source frames');
 await expect(page.locator('.quote')).toContainText('1 request');
 await expect(page.locator('.quote')).toContainText('US$0.0100');
 await expect(page.locator('.quote')).not.toContainText('442');
 await expect(page.getByRole('button',{name:'Authorize this paid request'})).toBeDisabled();
 await page.screenshot({path:'../output/playwright/sam-final-budget.png',fullPage:true});
 await page.keyboard.press('Escape');
 await page.getByLabel('Footage provenance').selectOption('real');
 await page.waitForFunction(()=>{const v=document.querySelector('video');return v&&v.readyState>=2&&!v.seeking;});
 await page.getByRole('button',{name:'Run simulation'}).click();
 await expect.poll(()=>page.locator('video').evaluate((v:HTMLVideoElement)=>v.currentTime)).toBeGreaterThan(.15);
 await expect.poll(()=>page.locator('video').evaluate((v:HTMLVideoElement)=>v.ended),{timeout:10000}).toBe(true);
 expect(await page.locator('video').evaluate((v:HTMLVideoElement)=>v.error)).toBeNull();
 expect(inferenceRequests).toBe(0);expect(errors).toEqual([]);
});
