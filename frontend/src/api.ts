export class ApiError extends Error {
 constructor(message:string,public detail:unknown){super(message);this.name='ApiError';}
}
export function failureMessage(detail:unknown):string {
 if(typeof detail==='string')return detail;
 if(detail&&typeof detail==='object'&&'diagnostic_id' in detail&&'category' in detail){
  const d=detail as {diagnostic_id:string;category:string;phase?:string;http_status?:number|null;usage?:{prompt_tokens?:number;completion_tokens?:number}};
  const tokens=d.usage?.completion_tokens!==undefined?` Reported tokens: ${d.usage.prompt_tokens??'unknown'} input / ${d.usage.completion_tokens} output.`:' Token usage unavailable.';
  return `Muse trial failed (${d.category}, ${d.phase??'unknown phase'}${d.http_status?`, HTTP ${d.http_status}`:''}). Diagnostic: ${d.diagnostic_id}.${tokens} No retry; review this result before any new spending authorization.`;
 }
 return JSON.stringify(detail);
}
export async function api<T>(path:string, options:RequestInit={}):Promise<T>{
 const response=await fetch(`/api${path}`,options);
 if(!response.ok){let message=`Request failed (${response.status})`,detail:unknown;try{const j=await response.json();detail=j.detail;message=failureMessage(detail);}catch{/* non-json response */}throw new ApiError(message,detail);}
 return response.json();
}
export const post=<T,>(path:string,data:unknown)=>api<T>(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
export function download(name:string,content:string,type='application/json'){const url=URL.createObjectURL(new Blob([content],{type}));const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
export type VideoInfo={id:string;name:string;width:number;height:number;fps:number;frames:number;duration:number;timestamps:number[];timing:string;provenance?:'unclassified'|'real'|'synthetic'};
export type Region={frame:number;left:number;top:number;right:number;bottom:number;id:number};
export type SamRecord={kind:'box'|'mask';object_id:string;frame:number;left?:number;top?:number;right?:number;bottom?:number;path?:string;bounds?:{left:number;top:number;right:number;bottom:number};width?:number;height?:number};
export type Proposal={mechanism:'slider-crank'|'unknown';components:{name:string;role:string;evidence:string}[];joints:{name:string;kind:'revolute'|'prismatic'|'unknown';evidence:string}[];limitations:string[]};
export function frameAt(video:VideoInfo,t:number){let lo=0,hi=video.timestamps.length-1;while(lo<hi){const mid=Math.ceil((lo+hi)/2);if(video.timestamps[mid]<=t+1e-6)lo=mid;else hi=mid-1;}return lo;}
