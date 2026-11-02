// Release inventory only: builds in memory and does not overwrite frontend/dist.
import {fileURLToPath, pathToFileURL} from 'node:url';
import path from 'node:path';
import fs from 'node:fs';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const frontend=path.join(root,'frontend');
const output=path.join(root,'output','submission-package','bundled-modules.json');
const {build}=await import(pathToFileURL(path.join(frontend,'node_modules','vite','dist','node','index.js')).href);
process.chdir(frontend);
const result=await build({configFile:path.join(frontend,'vite.config.ts'),build:{write:false}});
const bundles=Array.isArray(result)?result.flatMap(item=>item.output):result.output;
const rows=bundles.filter(item=>item.type==='chunk').flatMap(chunk=>Object.entries(chunk.modules)
  .filter(([,metadata])=>metadata.renderedLength>0)
  .map(([identity,metadata])=>{
    const normalized=identity.replaceAll('\\','/');
    const marker='/node_modules/';
    const offset=normalized.lastIndexOf(marker);
    const dependency=offset>=0?normalized.slice(offset+marker.length):null;
    const packageName=dependency?(dependency.startsWith('@')?dependency.split('/').slice(0,2).join('/'):dependency.split('/')[0]):null;
    const safeModule=dependency??(identity.startsWith('\0')?identity:path.relative(root,identity).replaceAll('\\','/'));
    return {module:safeModule,dependency_package:packageName,bytes:metadata.renderedLength};
  }));
fs.mkdirSync(path.dirname(output),{recursive:true});
fs.writeFileSync(output,JSON.stringify(rows,null,2)+'\n');
console.log(JSON.stringify({rendered_modules:rows.length,dependency_packages:[...new Set(rows.map(row=>row.dependency_package).filter(Boolean))].sort(),production_dist_overwritten:false},null,2));
