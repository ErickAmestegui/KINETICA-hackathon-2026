// Read-only presentation/accessibility smoke audit of the existing local app.
// Uses installed Playwright; no new dependency, inference or product changes.
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const {chromium} = require(path.join(root, 'frontend/node_modules/@playwright/test'));
const out = path.join(root, 'output/submission-validation');
fs.mkdirSync(out, {recursive:true});

(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true,args:['--enable-unsafe-swiftshader']});
 const context=await browser.newContext({viewport:{width:1440,height:1000},serviceWorkers:'block'});
 const errors=[];const requests=[];const pages=[];
 try{
  await context.route('**/*',route=>{
   const url=new URL(route.request().url());
   if(!['127.0.0.1','localhost'].includes(url.hostname))return route.abort();
   if(url.pathname.startsWith('/api/meta/')||url.pathname==='/api/lab/muse/run'){
    requests.push({path:url.pathname,blocked:true});
    return route.fulfill({status:403,json:{detail:'Presentation audit: external inference disabled'}});
   }
   return route.continue();
  });
  const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
  await page.goto('http://127.0.0.1:8000');await page.waitForLoadState('networkidle');
  const cdp=await context.newCDPSession(page);
  async function inspect(name){
   const tree=await cdp.send('Accessibility.getFullAXTree');
   const interactive=tree.nodes.filter(n=>!n.ignored&&['button','link','textbox','combobox','slider','checkbox','radio','tab'].includes(n.role?.value));
   const unnamed=interactive.filter(n=>!n.name?.value?.trim()).map(n=>({role:n.role.value,node:n.backendDOMNodeId}));
   const size=await page.evaluate(()=>({width:innerWidth,documentWidth:document.documentElement.scrollWidth,lang:document.documentElement.lang}));
   await page.screenshot({path:path.join(out,`presentation-${name}.png`),fullPage:true});
   pages.push({name,...size,interactiveCount:interactive.length,unnamed,overflow:size.documentWidth>size.width});
  }
  await inspect('studio');
  const keyboard=[];
  for(let i=0;i<18;i++){
   await page.keyboard.press('Tab');
   keyboard.push(await page.evaluate(()=>{const e=document.activeElement;const s=getComputedStyle(e);return {tag:e.tagName,role:e.getAttribute('role'),name:e.getAttribute('aria-label')||e.getAttribute('title')||e.textContent?.trim().slice(0,90),outline:s.outlineStyle,outlineWidth:s.outlineWidth,boxShadow:s.boxShadow};}));
  }
  await page.getByRole('button',{name:'My machines',exact:true}).click();
  const chooser=page.waitForEvent('filechooser');await page.getByRole('button',{name:'Open project JSON'}).click();
  await(await chooser).setFiles(path.join(root,'output/kinetica-project.json'));
  await page.getByRole('tab',{name:'Reality Lab',exact:true}).click();
  await inspect('predict');
  await page.getByRole('button',{name:'02 / Break Reality'}).click();await inspect('break');
  await page.getByRole('button',{name:'03 / Ask the Machine'}).click();await inspect('ask');
  await page.setViewportSize({width:390,height:844});await inspect('ask-mobile');
  const report={schema:'kinetica-presentation-smoke/1',observedAt:new Date().toISOString(),newInference:false,pages,keyboard,errors,blockedRequests:requests,
   scope:['Chromium accessibility names for exposed controls','keyboard focus traversal','desktop/mobile DOM overflow','authentic UI screenshots'],
   notTested:['Complete WCAG conformance','screen-reader user study','all color contrast combinations','all 3D keyboard interactions'],
   pass:pages.every(p=>!p.overflow&&p.unnamed.length===0)&&errors.length===0};
  fs.writeFileSync(path.join(out,'presentation.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify({pass:report.pass,pages:pages.map(p=>({name:p.name,unnamed:p.unnamed.length,overflow:p.overflow})),runtimeErrors:errors.length}));
  if(!report.pass)process.exitCode=1;
 }finally{await context.close();await browser.close();}
})().catch(e=>{console.error(e.message);process.exitCode=1;});
