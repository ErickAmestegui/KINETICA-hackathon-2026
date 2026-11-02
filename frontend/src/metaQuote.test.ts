import {expect,it} from 'vitest';
import {canRunQuote,quoteMatches,type Quote} from './metaQuote';
const quote:Quote={token:'local-test',video_id:'50-frame-clip',action:'sam',request_count:1,
 source:{name:'fixture',frames:50,width:960,height:540,duration:2},estimated_usd:.01,kind:'test',detail:'test',
 status:{key_configured:true,paid_enabled:false,message:'mock',verified_live:false}};
it('matches the exact video and model, rejecting stale estimates',()=>{
 expect(quoteMatches(quote,'50-frame-clip','sam')).toBe(true);
 expect(quoteMatches(quote,'442-frame-clip','sam')).toBe(false);
 expect(quoteMatches(quote,'50-frame-clip','muse')).toBe(false);
 expect(quoteMatches(null,'50-frame-clip','sam')).toBe(false);
});
it('blocks an otherwise valid quote while paid_enabled is false',()=>{
 expect(canRunQuote(quote,'50-frame-clip','sam')).toBe(false);
 expect(canRunQuote({...quote,status:{...quote.status,paid_enabled:true}},'wrong-clip','sam')).toBe(false);
});
