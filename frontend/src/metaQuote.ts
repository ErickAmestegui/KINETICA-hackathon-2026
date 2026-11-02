export type MetaStatus={key_configured:boolean;paid_enabled:boolean;message:string;verified_live:boolean};
export type Quote={token:string;video_id:string;action:'sam'|'muse';request_count:1;
 source:{name:string;frames:number;width:number;height:number;duration:number};
 estimated_usd:number;kind:string;detail:string;status:MetaStatus};
export function quoteMatches(quote:Quote|null,videoId:string|undefined,action:'sam'|'muse'){
 return !!quote&&quote.video_id===videoId&&quote.action===action&&quote.request_count===1;
}
export function canRunQuote(quote:Quote|null,videoId:string|undefined,action:'sam'|'muse'){
 return quoteMatches(quote,videoId,action)&&!!quote?.status.key_configured&&quote.status.paid_enabled;
}
