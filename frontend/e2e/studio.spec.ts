import {test,expect} from './fixtures';
import fs from 'node:fs';
import path from 'node:path';

test('studio renders a live 3D model, responds to parameters and exports honest report',async({page})=>{
 const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('/');await expect(page.getByRole('heading',{name:'From footage to function.'})).toBeVisible();
 await expect(page.locator('.model-stage canvas')).toBeVisible();
 await page.waitForFunction(()=>{const c=document.querySelector('.model-stage canvas') as HTMLCanvasElement;return c?.width>0;});
 await page.evaluate(()=>window.scrollTo(0,0));await page.screenshot({path:'../output/playwright/studio-desktop.png',fullPage:true});
 const first=await page.locator('.filmstrip').screenshot();
 await page.getByRole('slider',{name:'Crank radius',exact:true}).fill('45');
 const second=await page.locator('.filmstrip').screenshot();expect(Buffer.compare(first,second)).not.toBe(0);
 await page.getByRole('button',{name:'Run simulation'}).click();await expect(page.getByRole('button',{name:'Pause motion'})).toBeVisible();
 const old=await page.locator('.time-readout').textContent();await expect.poll(()=>page.locator('.time-readout').textContent()).not.toBe(old);
 await page.getByRole('button',{name:'Pause motion'}).click();
 await page.getByRole('tab',{name:'Analysis',exact:true}).click();await expect(page.getByText('Every motion. Accounted for.')).toBeVisible();
 await expect(page.getByRole('button',{name:'Fit to training observations'})).toBeDisabled();
 await page.getByRole('tab',{name:'Report',exact:true}).click();
 await expect(page.getByText('No Meta inference has been performed in this study.')).toBeVisible();
 const dl=page.waitForEvent('download');await page.getByRole('button',{name:'Export validation report'}).click();const download=await dl;const file=await download.path();const report=JSON.parse(fs.readFileSync(file!,'utf8'));expect(report.mode).toBe('Simulation Demo');expect(report.comparison.validation.rmse_px).toBeNull();
 await page.getByRole('button',{name:'Model connections'}).click();await expect(page.getByText('Paid inference: blocked by default')).toBeVisible();await page.getByRole('button',{name:'Check model catalogue (no inference)'}).click();await expect(page.locator('.notification')).toContainText('MODEL_API_KEY');
 await page.keyboard.press('Escape');expect(errors).toEqual([]);
});

test('local video annotations, tracking, calibration, fitting and CSV round trip',async({page})=>{
 await page.goto('/');
 await page.locator('input[type=file]').first().setInputFiles(path.resolve('../output/synthetic-slider-crank.mp4'));
 await expect(page.getByRole('tab',{name:'Compare',exact:true})).toHaveAttribute('aria-selected','true');
 await page.waitForFunction(()=>{const v=document.querySelector('video');return v&&v.readyState>=2&&!v.seeking;});
 const overlay=page.getByLabel('Video annotation canvas');const box=await overlay.boundingBox();expect(box).not.toBeNull();
 async function mark(tool:string,x:number,y:number){await page.getByLabel('Annotation tool').selectOption(tool);await overlay.click({position:{x:x/640*box!.width,y:y/360*box!.height}});}
 await mark('origin',100,180);await mark('axis',550,180);await mark('crank',148,180);await mark('slider',340,180);
 await page.getByRole('button',{name:'Track locally',exact:true}).click();await expect(page.locator('.notification')).toContainText('OpenCV baseline',{timeout:30000});
 await page.evaluate(()=>window.scrollTo(0,0));await page.screenshot({path:'../output/playwright/compare-video.png',fullPage:true});
 await page.getByRole('tab',{name:'Analysis',exact:true}).click();
 await page.getByLabel('Pixels / model unit').fill('1.5');
 await page.getByRole('slider',{name:'Angular speed',exact:true}).fill('30');
 // Synthetic footage is test-only; the UI treats uploaded videos as unclassified real inputs.
 await page.getByText('Advanced geometry').click();
 await page.getByRole('slider',{name:'Phase',exact:true}).fill('0');
 await page.getByRole('button',{name:'Fit to training observations'}).click();
 await expect(page.locator('.notification')).toContainText('Fit completed',{timeout:20000});
 const rmse=await page.locator('.metric-grid>div').first().textContent();expect(rmse).not.toContain('—');
 await page.evaluate(()=>window.scrollTo(0,0));await page.screenshot({path:'../output/playwright/analysis.png',fullPage:true});
 const dl=page.waitForEvent('download');await page.getByRole('button',{name:'Export CSV',exact:true}).click();const saved=await dl;const csvPath=await saved.path();expect(fs.readFileSync(csvPath!,'utf8')).toContain('opencv-lk');
 await page.locator('input[type=file]').nth(1).setInputFiles({name:'observations.csv',mimeType:'text/csv',buffer:fs.readFileSync(csvPath!)});
 await expect(page.locator('.notification')).toContainText('Imported');
 await page.getByRole('button',{name:'My machines'}).click();await page.getByRole('button',{name:'Save current study'}).click();await page.keyboard.press('Escape');await page.reload();await page.getByRole('button',{name:'My machines'}).click();await page.getByRole('button',{name:'Restore saved study'}).click();await expect(page.locator('.notification')).toContainText('Study restored');
});

test('laptop and narrow view have no horizontal overflow and keyboard guide works',async({page})=>{
 for(const size of [{width:1280,height:800},{width:390,height:844}]){
  await page.setViewportSize(size);await page.goto('/');await expect(page.locator('.model-stage canvas')).toBeVisible();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  await page.evaluate(()=>window.scrollTo(0,0));await page.screenshot({path:`../output/playwright/studio-${size.width}.png`,fullPage:true});
 }
 await page.getByRole('button',{name:'Studio guide'}).click();await expect(page.getByRole('dialog')).toBeVisible();await page.keyboard.press('Escape');await expect(page.getByRole('dialog')).toHaveCount(0);
});

test('optional real-video diagnostic project opens with manual provenance and genuine residuals',async({page})=>{
 const project=path.resolve('../output/real-video/eitech-project.json');
 test.skip(!fs.existsSync(project),'Run scripts.evaluate_eitech with a lawfully obtained local video first.');
 const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('/');await page.locator('input[type=file]').nth(2).setInputFiles(project);
 await expect(page.locator('.notification')).toContainText('Study restored');
 await page.getByRole('tab',{name:'Compare',exact:true}).click();
 await page.getByRole('slider',{name:'Timeline',exact:true}).fill('6');
 await page.waitForFunction(()=>{const v=document.querySelector('video');return v&&v.readyState>=2&&!v.seeking;});
 await expect(page.getByLabel('Footage provenance')).toHaveValue('real');
 await page.evaluate(()=>window.scrollTo(0,0));await page.screenshot({path:'../output/playwright/real-eitech-compare.png',fullPage:true});
 await page.getByRole('button',{name:'Run simulation'}).click();
 const before=await page.locator('.time-readout').textContent();
 await expect.poll(()=>page.locator('.time-readout').textContent()).not.toBe(before);
 await page.getByRole('button',{name:'Pause motion'}).click();
 await page.getByRole('tab',{name:'Analysis',exact:true}).click();
 await expect(page.locator('.metric-grid').first()).toContainText('58.42');
 await page.evaluate(()=>window.scrollTo(0,0));await page.screenshot({path:'../output/playwright/real-eitech-analysis.png',fullPage:true});
 await page.getByRole('tab',{name:'Report',exact:true}).click();
 await expect(page.getByText('No Meta inference has been performed in this study.')).toBeVisible();
 expect(errors).toEqual([]);
});
