import {defineConfig} from '@playwright/test';
// A service worker must not bypass the offline interception in e2e/fixtures.ts.
export default defineConfig({testDir:'./e2e',timeout:90000,workers:1,outputDir:'../output/playwright/results',reporter:[['list'],['json',{outputFile:'../output/playwright/results.json'}]],use:{serviceWorkers:'block',baseURL:process.env.KINETICA_URL||'http://127.0.0.1:8000',channel:'chrome',headless:true,viewport:{width:1440,height:1000},screenshot:'only-on-failure',trace:'retain-on-failure',launchOptions:{args:['--enable-unsafe-swiftshader']}}});
