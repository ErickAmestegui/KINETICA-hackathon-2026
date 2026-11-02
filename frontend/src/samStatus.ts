import type {SamRecord} from './api';

export type SamResult={
 records:SamRecord[];
 simulated?:boolean;
 outcome:{status:'completed'|'incomplete'|'failed';reason?:string};
 failure?:{category:string;phase:string;http_status?:number|null;parser_code?:string|null}|null;
 diagnostics?:unknown[];
 remote_file_cleanup?:string;
 diagnostic?:{id:string};
 reconstruction_verified?:boolean;
};

export function isSamResult(value:unknown):value is SamResult {
 if(!value||typeof value!=='object')return false;
 const result=value as SamResult;
 return Array.isArray(result.records)&&['completed','incomplete','failed'].includes(result.outcome?.status);
}

export function samSummary(result:SamResult):string {
 const {status,reason}=result.outcome;
 const state=status==='completed'?'SAM completed':status==='incomplete'?'SAM incomplete — partial results':'SAM failed — no automatic retry';
 const failure=result.failure;
 const details=failure?` ${failure.category} / ${failure.phase}${failure.http_status?` / HTTP ${failure.http_status}`:''}${failure.parser_code?` / ${failure.parser_code}`:''}.`:reason?` Reason: ${reason}.`:'';
 const cleanup=result.remote_file_cleanup;
 return `${result.simulated?'SIMULATED TEST — no real Meta inference. ':''}${state}. ${result.records.length} geometry records; ${result.diagnostics?.length??0} parser diagnostics.${details} Segmentation is not a verified reconstruction.${cleanup&&cleanup!=='not_needed'?` Remote file: ${cleanup}.`:''}${cleanup==='failed'||cleanup==='unknown_upload'?' Check remote files manually before any new request.':''}${result.diagnostic?.id?` Diagnostic: ${result.diagnostic.id}.`:''}`;
}
