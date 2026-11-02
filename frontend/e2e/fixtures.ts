import {test as base,expect} from '@playwright/test';

// All specs import this fixture. Meta routes never reach the backend from a test.
// Per-test synthetic responses can override these routes; no paid server flag changes.
export const test=base.extend({
 context:async({context},use)=>{
  await context.route('**/*',async route=>{
   const url=new URL(route.request().url());
   if(!['127.0.0.1','localhost'].includes(url.hostname))return route.abort('blockedbyclient');
   if(url.pathname==='/api/meta/catalogue')return route.fulfill({status:503,json:{detail:'MODEL_API_KEY catalogue check disabled by offline browser fixture'}});
   if(url.pathname==='/api/meta/run'||url.pathname==='/api/lab/muse/run')return route.fulfill({status:403,json:{detail:'Paid inference blocked by offline browser fixture'}});
   return route.continue();
  });
  await use(context);
 },
});
export {expect};
