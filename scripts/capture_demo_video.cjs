// Authentic browser recording. No DOM replacement, fabricated values or Meta I/O.
const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
const {execFileSync}=require('node:child_process');
const root=path.resolve(__dirname,'..');
const out=path.join(root,'output/submission-video');
if(process.argv.includes('--help')){console.log('node scripts/capture_demo_video.cjs [http://127.0.0.1:8000] [--smoke]\nRequires narration.json from prepare_demo_video.py --prepare. Writes genuine raw recording and chapter markers. --smoke validates the encoder with a two-second real-app capture first.');process.exit(0);}
// The locked Playwright expects FFmpeg1011. Reuse an already installed official
// Playwright FFmpeg in a workspace-only cache if that exact cache is absent.
// This copies no binary into the source tree and downloads/installs nothing.
const cache=path.join(process.env.LOCALAPPDATA||'', 'ms-playwright');
let recorderBinary=path.join(cache,'ffmpeg-1011','ffmpeg-win64.exe');
if(!fs.existsSync(recorderBinary)){
 const candidate=execFileSync(path.join(root,'.venv/Scripts/python.exe'),['-c','import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())'],{encoding:'utf8'}).trim();
 const encoders=execFileSync(candidate,['-hide_banner','-encoders'],{encoding:'utf8'});
 if(!/\blibvpx\s/.test(encoders))throw Error('Existing FFmpeg lacks required VP8 encoder');
 const local=path.join(out,'runtime','ffmpeg-1011');fs.mkdirSync(local,{recursive:true});
 recorderBinary=path.join(local,'ffmpeg-win64.exe');fs.copyFileSync(candidate,recorderBinary);
 process.env.PLAYWRIGHT_BROWSERS_PATH=path.join(out,'runtime');
}
const {chromium,expect}=require('../frontend/node_modules/@playwright/test');
const base=process.argv.slice(2).find(arg=>!arg.startsWith('--'))||'http://127.0.0.1:8000';
if(!['127.0.0.1','localhost'].includes(new URL(base).hostname))throw Error('Local loopback only');
const entries=JSON.parse(fs.readFileSync(path.join(out,'narration.json'),'utf8'));
const projectPath=path.join(root,'output/kinetica-project.json');
const project=JSON.parse(fs.readFileSync(projectPath,'utf8'));
const hash=file=>crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const sourcePath=path.join(root,'data',project.video.id,'source.mp4');
const sourceHash=hash(sourcePath),projectHash=hash(projectPath);
const errors=[],blocked=[],scenes=[];
let browser,context,page,origin;
const now=()=>Number(process.hrtime.bigint()-origin)/1e9;
const hold=seconds=>page.waitForTimeout(seconds*1000);
async function scene(id,action){
 const entry=entries.find(e=>e.id===id),start=now();
 console.log('Recording chapter:',id);
 await action();
 const remaining=entry.minimum_scene_seconds-(now()-start);
 if(remaining>0)await hold(remaining);
 const end=now();scenes.push({id,start,end});
 await page.screenshot({path:path.join(out,`capture-${id}.png`)});
}
async function scroll(selector){await page.locator(selector).scrollIntoViewIfNeeded();await page.locator(selector).evaluate(el=>window.scrollTo({top:el.getBoundingClientRect().top+window.scrollY-24,behavior:'smooth'}));await hold(.65);}
async function main(){
 fs.mkdirSync(path.join(out,'raw'),{recursive:true});
 browser=await chromium.launch({channel:'chrome',headless:true,args:['--enable-unsafe-swiftshader']});
 context=await browser.newContext({viewport:{width:1600,height:800},deviceScaleFactor:1,serviceWorkers:'block',
   recordVideo:{dir:path.join(out,'raw'),size:{width:1600,height:800}}});
 await context.route('**/*',async route=>{
  const url=new URL(route.request().url());
  if(!['127.0.0.1','localhost'].includes(url.hostname)||url.pathname==='/api/meta/run'||url.pathname==='/api/meta/catalogue'||url.pathname==='/api/lab/muse/run'){
   blocked.push({host:url.hostname,path:url.pathname});return route.abort('blockedbyclient');
  }return route.continue();
 });
 page=await context.newPage();origin=process.hrtime.bigint();
 page.on('pageerror',e=>errors.push(e.message));
 await page.goto(base,{waitUntil:'networkidle'});
 const health=await (await page.request.get(`${base}/api/health`)).json();if(health.meta.paid_enabled)throw Error('Paid flag must remain false');
 if(process.argv.includes('--smoke')){
  await hold(2);const video=page.video();await context.close();
  const destination=path.join(out,'encoder-smoke.webm');await video.saveAs(destination);await browser.close();
  if(fs.statSync(destination).size<1024)throw Error('Empty encoder smoke result');
  console.log('Authentic app recording encoder smoke passed:',fs.statSync(destination).size,'bytes');return;
 }
 await page.getByRole('button',{name:'My machines'}).click();
 const chooser=page.waitForEvent('filechooser');await page.getByRole('button',{name:'Open project JSON'}).click();await(await chooser).setFiles(projectPath);
 await expect(page.locator('.notification')).toContainText('Study restored');
 // Rights audit identifies the public source and authentic recording. Declare
 // that source through the existing UI only; never rewrite the original export.
 await page.getByRole('tab',{name:'Compare',exact:true}).click();
 await page.getByLabel('Footage provenance').selectOption('real');
 await page.getByRole('tab',{name:'Reality Lab',exact:true}).click();
 await expect(page.locator('.lab-footage video')).toHaveJSProperty('readyState',4);
 // The recording contains setup, but the master trims it at the first chapter.
 const opening=now();
 await scene('intro',async()=>{
  await page.evaluate(()=>window.scrollTo({top:0,behavior:'smooth'}));await hold(7);
  await scroll('.lab-acts');
 });
 await scene('observe',async()=>{
  // Reality Lab draws masks faintly over turquoise parts; Compare shows the saved SAM boxes/IDs legibly.
  await page.getByRole('tab',{name:'Compare',exact:true}).click();
  await page.locator('.video-wrap').evaluate(el=>window.scrollTo({top:el.getBoundingClientRect().top+window.scrollY-90,behavior:'smooth'}));await hold(.8);
  await expect(page.locator('.sam-status')).toContainText('300 geometry records');
  await page.getByLabel('Video playback speed').selectOption('0.5');
  await page.evaluate(()=>document.activeElement&&document.activeElement.blur());
  await page.keyboard.press('Space');await hold(4.7);
  await page.getByRole('tab',{name:'Reality Lab',exact:true}).click();
  await expect(page.locator('.lab-footage video')).toHaveJSProperty('readyState',4);
  await scroll('.lab-message');
  await page.getByLabel('Lab tracked object').selectOption('2');
  await page.getByRole('checkbox',{name:/I inspected this object/}).check();
  await page.getByLabel('Freeze after frame').fill('29');await page.getByLabel('Hidden horizon').fill('8');
  // The true source is two seconds long. Replay it at its real rate three times.
  for(let i=0;i<3;i++){
   await page.getByLabel('Reality replay time').fill('0');
   await page.getByRole('button',{name:'Play reality',exact:true}).click();await hold(2.25);
  }
 });
 await scene('predict',async()=>{
  await scroll('.lab-message');
  await page.getByRole('button',{name:'FREEZE REALITY',exact:true}).click();
  await expect(page.getByRole('button',{name:'REVEAL REALITY',exact:true})).toBeEnabled({timeout:45000});
  await expect(page.locator('.lab-results')).toContainText('SEALED FORECAST');
  await hold(7);await scroll('.lab-results');
 });
 await scene('reveal',async()=>{
  await page.getByRole('button',{name:'REVEAL REALITY',exact:true}).click();
  await expect(page.locator('.lab-scorecards')).toContainText('9.10 px');
  await expect(page.locator('.lab-scorecards')).toContainText('23.93 px');
  await expect(page.locator('.lab-scorecards')).toContainText('75.59 px');
  await scroll('.lab-results');
  const response=page.waitForEvent('download');await page.getByRole('button',{name:'Export replay evidence'}).click();
  await(await response).saveAs(path.join(out,'real-replay-29-8.json'));
 });
 await scene('cut',async()=>{
  await page.getByRole('button',{name:'Reset replay',exact:true}).click();
  await page.getByLabel('Hidden horizon').fill('20');
  await scroll('.lab-message');await page.getByRole('button',{name:'FREEZE REALITY',exact:true}).click();
  await expect(page.getByRole('button',{name:'REVEAL REALITY',exact:true})).toBeEnabled({timeout:45000});
  await page.getByRole('button',{name:'REVEAL REALITY',exact:true}).click();
  await expect(page.locator('.lab-results')).toContainText('Known source framing');
  await scroll('.lab-results');await expect(page.locator('.lab-scorecards')).toContainText('No evaluado');
 });
 await scene('break',async()=>{
  await page.getByRole('button',{name:'02 / Break Reality'}).click();await scroll('.lab-message');
  await page.getByRole('button',{name:'Animate both machines'}).click();await hold(4);
  await page.getByRole('button',{name:'Pause both machines'}).click();
  await scroll('.lab-controls');
  await page.getByLabel('Requested slider stroke').fill('500');await page.getByRole('button',{name:'Calculate requested stroke'}).click();
  await expect(page.locator('.lab-message')).toContainText('Impossible requested stroke');
  await scroll('.lab-message');await hold(1);await scroll('.lab-controls');
  await page.getByLabel('Requested slider stroke').fill('100');await page.getByRole('button',{name:'Calculate requested stroke'}).click();
  await expect(page.getByLabel('Alternate r',{exact:true})).toHaveValue('50');
  await page.getByLabel('Alternate r',{exact:true}).fill('50');
  await scroll('.lab-message');await page.getByRole('button',{name:'Animate both machines'}).click();await hold(4);
  await page.getByRole('button',{name:'Pause both machines'}).click();
 });
 await scene('ask',async()=>{
  await page.getByRole('button',{name:'Restore original',exact:true}).click();
  await page.getByRole('button',{name:'03 / Ask the Machine'}).click();await scroll('.lab-ask');
  await page.getByRole('button',{name:'Interpret locally (mock)'}).click();
  await expect(page.locator('.lab-tool-preview')).toContainText('deterministic_mock');await hold(5);
  await page.getByRole('button',{name:'Confirm alternate change'}).click();await hold(1);
  await page.getByRole('button',{name:'02 / Break Reality'}).click();await scroll('.lab-message');
  await expect(page.getByLabel('Alternate r',{exact:true})).toHaveValue('64');
  await page.getByRole('button',{name:'Animate both machines'}).click();await hold(4);
  await page.getByRole('button',{name:'Pause both machines'}).click();
 });
 await scene('outro',async()=>{
  await scroll('.lab-message');await page.getByRole('button',{name:'Animate both machines'}).click();
 });
 const captureStop=now(),video=page.video();await context.close();await video.saveAs(path.join(out,'authentic-screen-recording.webm'));await browser.close();
 if(errors.length)throw Error(`Browser errors: ${errors.join('; ')}`);
 if(hash(sourcePath)!==sourceHash||hash(projectPath)!==projectHash)throw Error('Original source changed');
 const report={schema:'kinetica-authentic-screen-capture/1',recording:path.join(out,'authentic-screen-recording.webm'),
  opening_trim_seconds:opening,capture_stop_wall_seconds:captureStop,scenes,source_sha256:sourceHash,source_export_sha256:projectHash,
  original_inputs_unchanged:true,new_inference:false,paid_requests:0,blocked_requests:blocked,console_page_errors:errors,
  note:'Capture contains genuine UI interactions. Master trims setup only; narration is synthesized offline.'};
 fs.writeFileSync(path.join(out,'capture.json'),JSON.stringify(report,null,2));
 console.log(JSON.stringify({recording:report.recording,raw_duration:scenes.at(-1).end,master_duration:scenes.at(-1).end-opening,scenes:scenes.length,errors,blocked}));
}
main().catch(async e=>{console.error(e);if(context)await context.close().catch(()=>{});if(browser)await browser.close().catch(()=>{});process.exit(1);});
